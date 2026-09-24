// Executes the installed first-run decision and route guard with controlled preference data.
// Filesystem checks use a disposable copy; no VS Code user state is changed by this test.
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const test = require('node:test');
const { stock, patched, normalize, patchSource, loadTarget, update } = require('./patch-first-run.cjs');

const target = loadTarget();
const original = normalize(target.source);
const changed = patchSource(original);

function between(source, start, end) {
  const a = source.indexOf(start);
  assert.notEqual(a, -1, `Missing production entry point: ${start}`);
  const b = source.indexOf(end, a + start.length);
  assert.notEqual(b, -1, `Missing production boundary: ${end}`);
  return source.slice(a, b);
}

function route(source, viewed, loading = false) {
  const firstRun = between(source, 'function pcr()', 'function mcr()');
  const guard = between(source, 'function hcr(e)', 'var gcr,x7;');
  const sentinel = Symbol.for('react.memo_cache_sentinel');
  const context = {
    Cs: { NUX_2025_09_15: 'viewed2025-09-15-nux' },
    iS: key => {
      assert.equal(key, 'viewed2025-09-15-nux');
      return { data: viewed, isLoading: loading };
    },
    Zl: () => ({ authMethod: 'chatgpt' }),
    gcr: { c: size => Array(size).fill(sentinel) },
    x7: { Fragment: 'Fragment', jsx: (component, props) => ({ component, props }) },
    $r: 'Navigate', y7: 'Loading',
  };
  const guardFunction = vm.runInNewContext(`${firstRun}${guard};hcr`, context);
  return guardFunction({ children: 'normal chat' });
}

test('an unseen first run redirects in stock code but renders chat with the patch', () => {
  const before = route(original, false);
  assert.equal(before.component, 'Navigate');
  assert.equal(before.props.to, '/first-run');
  assert.equal(before.props.replace, true);
  const after = route(changed, false);
  assert.equal(after.component, 'Fragment');
  assert.equal(after.props.children, 'normal chat');
});

test('the patch bypasses a preference still loading; stock preserves its loading state', () => {
  assert.equal(route(original, false, true).component, 'Loading');
  const after = route(changed, false, true);
  assert.equal(after.component, 'Fragment');
  assert.equal(after.props.children, 'normal chat');
});

test('a completed first run continues directly to chat in both versions', () => {
  assert.equal(route(original, true).props.children, 'normal chat');
  assert.equal(route(changed, true).props.children, 'normal chat');
});

test('patching is idempotent and rejects an unfamiliar or ambiguous decision', () => {
  assert.equal(patchSource(changed), changed);
  assert.throws(() => patchSource(original.replace(stock, 'function pcr(){return `new-flow`}')), /Unsupported/);
  assert.throws(() => patchSource(original + patched), /ambiguous/);
});

test('apply and restore preserve a verified original and refuse unrelated changes', context => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'codex-first-run-test-'));
  context.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const assets = path.join(root, 'webview', 'assets');
  fs.mkdirSync(assets, { recursive: true });
  fs.writeFileSync(path.join(root, 'package.json'), JSON.stringify({
    publisher: 'openai', name: 'chatgpt', version: 'test',
  }));
  fs.writeFileSync(path.join(root, 'webview', 'index.html'),
    '<link rel="modulepreload" href="./assets/app-initial-test.js">');
  const file = path.join(assets, 'app-initial-test.js');
  fs.writeFileSync(file, original);
  assert.equal(update(loadTarget(root), 'apply').changed, true);
  assert.equal(fs.readFileSync(file, 'utf8'), changed);
  assert.equal(fs.readFileSync(file + '.codex-first-run-original', 'utf8'), original);
  assert.equal(update(loadTarget(root), 'apply').changed, false);
  assert.equal(update(loadTarget(root), 'restore').changed, true);
  assert.equal(fs.readFileSync(file, 'utf8'), original);
  fs.appendFileSync(file, '\n// unrelated local edit\n');
  const drift = fs.readFileSync(file, 'utf8');
  assert.throws(() => update(loadTarget(root), 'apply'), /differs/);
  assert.equal(fs.readFileSync(file, 'utf8'), drift);
  assert.equal(fs.readFileSync(file + '.codex-first-run-original', 'utf8'), original);
});
