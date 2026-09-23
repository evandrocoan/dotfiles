// Local integration checks: require an installed extension with a supported bundle.
// No Codex session database is read or written; writes use disposable extension copies.
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const test = require('node:test');
const { LIMIT, edits, normalize, patchSource, installedExtension, loadTarget, update } = require('./patch.cjs');

const target = loadTarget();
const stock = normalize(target.source);
const patched = patchSource(stock);
const assets = path.dirname(target.file);
const selectorSources = fs.readdirSync(assets).filter(name => /^app-initial-.*\.js$/.test(name))
  .map(name => fs.readFileSync(path.join(assets, name), 'utf8'))
  .filter(source => source.includes('function lFn({appServerRegistry:'));
assert.equal(selectorSources.length, 1, 'Expected exactly one supported UI list selector');

function between(text, start, end) {
  const a = text.indexOf(start);
  assert.notEqual(a, -1, `Missing production entry point: ${start}`);
  const b = text.indexOf(end, a + start.length);
  assert.notEqual(b, -1, `Missing production boundary: ${end}`);
  return text.slice(a, b);
}

const ui = selectorSources[0];
const select = vm.runInNewContext(
  between(ui, 'function iFn(', 'function aFn(')
  + between(ui, 'function lFn(', 'async function uFn(') + ';lFn',
);

function discoveryLimit(source, host = 'local', desktop = false, catalog = false) {
  const declaration = source.match(/function R\$t\(e,t,n\)\{[^}]+\}/);
  assert.ok(declaration, 'Expected the installed host history limit function');
  const fn = vm.runInNewContext(`(${declaration[0]})`, { an: value => value === 'remote' });
  return fn(host, desktop, catalog);
}

async function visibleChats(source, count, expectedCount) {
  // The production refresh orchestration, recent-list reader and UI selector run unchanged.
  // Server responses and adjacent metadata persistence/event services are controlled doubles.
  const methods = vm.runInNewContext('({'
    + between(source, 'async runRecentConversationRefresh(', 'async listRecentThreads(') + ','
    + between(source, 'getRecentConversations(){let e=[];', 'get hasFetchedRecentConversations')
    + '})', { B: value => value, b$: thread => ({ updatedAt: thread.updatedAt }) });
  const records = Array.from({ length: count }, (_, i) => ({
    id: `session-${i + 1}`, createdAt: count - i, updatedAt: count - i,
    name: `Chat ${i + 1}`,
  }));
  const calls = [];
  const store = {
    ...methods,
    params: { getHistoryLimit: () => discoveryLimit(source), host: {}, events: { emitThreadListInvalidated() {} } },
    recentHistorySource: 'live', recentConversationSortKey: 'updated_at',
    conversations: new Map(), threadsById: new Map(), threadSummaries: [],
    recentConversationIds: [], pinnedConversationIds: new Set(),
    async loadThreadHydrationState() {},
    async listRecentThreads(request) {
      calls.push({ limit: request.limit, cursor: request.cursor });
      assert.ok(Number.isInteger(request.limit) && request.limit > 0 && request.limit <= 100);
      const offset = Number(request.cursor ?? 0);
      const next = Math.min(offset + request.limit, records.length);
      return { data: records.slice(offset, next), nextCursor: next < records.length ? String(next) : null };
    },
    recordThreadAvailability() {},
    getThreadSummaryFromThread(thread) { return { conversationId: thread.id }; },
    shouldSurfaceThreadSummary() { return true; },
    replaceRecentThreadSummaries(summaries) { this.threadSummaries = summaries; },
    upsertRecentConversationState(id, thread) { this.conversations.set(id, thread); },
    notifyConversationCallbacks() {}, notifyAnyConversationCallbacks() {},
    shouldSurfaceRecentConversation() { return true; }, isConversationActive() { return false; },
    getHostId() { return 'local'; },
  };
  const registry = { getDefault: () => store, getAll: () => [store] };
  for (let iteration = 0; iteration < 2; iteration++) {
    await store.runRecentConversationRefresh('updated_at', 'routine');
    const visible = select({ appServerRegistry: registry, enabledRemoteHostIds: new Set(), sortKey: 'updated_at' });
    assert.equal(visible.length, expectedCount, `Visible chat count on refresh ${iteration + 1}`);
    assert.deepEqual(Array.from(visible, record => record.id), records.slice(0, expectedCount).map(record => record.id));
  }
  return { calls, store };
}

test('the installed extension has the requested limit applied', () => {
  assert.ok(target.source === patched, 'Run patch.cjs --apply before checking the installed extension');
  assert.equal(discoveryLimit(target.source), 199);
  assert.equal(discoveryLimit(target.source, 'remote'), 50);
  assert.equal(discoveryLimit(target.source, 'local', true, false), 500);
  assert.equal(discoveryLimit(target.source, 'local', true, true), 0);
});

for (const [count, expected] of [[0, 0], [50, 50], [151, 151], [199, 199], [250, 199]]) {
  test(`${count} server chats produce ${expected} UI entries across two refreshes`, async () => {
    await visibleChats(patched, count, expected);
  });
}

test('pagination stops after 100 + 99; chat 60 remains available and chat 200 is not loaded', async () => {
  const { calls, store } = await visibleChats(patched, 250, 199);
  assert.deepEqual(calls, [
    { limit: 100, cursor: null }, { limit: 99, cursor: '100' },
    { limit: 100, cursor: null }, { limit: 99, cursor: '100' },
  ]);
  assert.equal(store.conversations.get('session-60').name, 'Chat 60');
  assert.equal(store.conversations.has('session-200'), false);
});

test('the same behavior assertion rejects the stock 50 limit and the missed UI truncation', async () => {
  await assert.rejects(visibleChats(stock, 250, 199), { code: 'ERR_ASSERTION', actual: 50, expected: 199 });
  const broken = patched.replace(edits[2].patched, edits[2].stock);
  await assert.rejects(visibleChats(broken, 250, 199), { code: 'ERR_ASSERTION', actual: 50, expected: 199 });
});

test('reapplication accepts the previous unlimited patch and rejects unknown or duplicate anchors', () => {
  const unlimited = edits.reduce((source, edit) => source.replace(edit.stock, edit.legacy.at(-1)), stock);
  assert.equal(patchSource(unlimited), patched);
  assert.equal(patchSource(patched), patched);
  assert.throws(() => patchSource(stock.replace(edits[2].stock, 'this.newHistoryImplementation()')), /Unsupported/);
  assert.throws(() => patchSource(stock + edits[0].stock), /ambiguous/);
});

test('filesystem apply is idempotent, preserves the original, restores it and refuses drift', context => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'codex-history-test-'));
  context.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const directory = path.join(root, '.vscode', 'extensions', 'openai.chatgpt-test');
  const assetDir = path.join(directory, 'webview', 'assets');
  fs.mkdirSync(assetDir, { recursive: true });
  fs.writeFileSync(path.join(root, '.vscode', 'extensions', 'extensions.json'), JSON.stringify([
    { identifier: { id: 'openai.chatgpt' }, relativeLocation: 'openai.chatgpt-test' },
  ]));
  fs.writeFileSync(path.join(directory, 'package.json'), JSON.stringify({ publisher: 'openai', name: 'chatgpt', version: 'test' }));
  fs.writeFileSync(path.join(directory, 'webview', 'index.html'), '<link href="./assets/app-initial-test.js">');
  const file = path.join(assetDir, 'app-initial-test.js');
  fs.writeFileSync(file, stock);
  assert.equal(installedExtension(root), directory);
  assert.equal(update(loadTarget(directory), 'apply').changed, true);
  assert.equal(fs.readFileSync(file, 'utf8'), patched);
  assert.equal(fs.readFileSync(file + '.codex-original', 'utf8'), stock);
  assert.equal(update(loadTarget(directory), 'apply').changed, false);
  assert.equal(update(loadTarget(directory), 'restore').changed, true);
  assert.equal(fs.readFileSync(file, 'utf8'), stock);
  fs.appendFileSync(file, '\n// unrelated local edit\n');
  const changed = fs.readFileSync(file, 'utf8');
  assert.throws(() => update(loadTarget(directory), 'apply'), /differs/);
  assert.equal(fs.readFileSync(file, 'utf8'), changed);
  assert.equal(fs.readFileSync(file + '.codex-original', 'utf8'), stock);
});
