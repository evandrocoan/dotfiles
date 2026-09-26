// Runs the installed new-tab component with controlled UI dependencies.
// Filesystem checks use a disposable extension copy; no VS Code state is changed.
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const test = require('node:test');
const { variants, editsFor, normalize, patchSource, loadTarget, update } = require('./patch-empty-header.cjs');

const target = loadTarget(process.env.CODEX_EXTENSION_DIR);
const original = normalize(target.source);
const changed = patchSource(original);
const edits = editsFor(original);

function newTabTree(source) {
  const start = source.indexOf('function j(){');
  const end = source.indexOf('function M(e)', start);
  assert.notEqual(start, -1, 'Missing production NewThreadPanelPage');
  assert.notEqual(end, -1, 'Missing production function boundary');
  const sentinel = Symbol.for('react.memo_cache_sentinel');
  const jsx = (component, props) => ({ component, props });
  const context = {
    P: { c: size => Array(size).fill(sentinel) },
    a: () => ({ formatMessage: () => 'Main content' }),
    t: () => 'selected-project', w: 'project-selector',
    E: () => false, f: 'announcement-selector',
    b: { isRecording: () => false },
    F: { jsx, jsxs: jsx },
    n: () => 'footer-class', v: 'footer-base',
    A: 'Announcements', m: 'ComposerProvider', g: 'Composer',
    T: 'NewTabShell', H: 'NavigationHeader',
    M: () => null,
  };
  const component = vm.runInNewContext(`${source.slice(start, end)};j`, context);
  return component();
}

function nodes(root, component) {
  const found = [];
  function visit(node) {
    if (Array.isArray(node)) {
      node.forEach(visit);
    } else if (node && typeof node === 'object') {
      if (node.component === component) found.push(node);
      visit(node.props?.children);
    }
  }
  visit(root);
  return found;
}

test('the original empty tab omits navigation; the patch renders it above chat', () => {
  const before = newTabTree(original);
  assert.equal(nodes(before, 'NavigationHeader').length, 0);
  assert.equal(nodes(before, 'Composer').length, 1);
  const after = newTabTree(changed);
  assert.equal(nodes(after, 'NavigationHeader').length, 1);
  assert.equal(nodes(after, 'Composer').length, 1);
  const shellChildren = nodes(after, 'NewTabShell')[0].props.children;
  assert.equal(shellChildren[1].component, 'NavigationHeader');
  assert.equal(shellChildren[2].component, 'div');
});

test('the new tab imports the existing initialized header export', () => {
  assert.ok(changed.includes(edits[0].patched));
  assert.ok(!original.includes(edits[0].patched));
  const header = fs.readFileSync(path.join(path.dirname(target.file), target.variant.headerAsset), 'utf8');
  assert.ok(header.includes('export{t as Header}'));
});

test('both inspected bundle variants use their matching initialized header', () => {
  for (const variant of variants) {
    const source = original.replace(target.variant.stockImport, variant.stockImport);
    assert.ok(source.includes(variant.stockImport));
    assert.ok(patchSource(source).includes(variant.patchedImport));
    assert.equal(normalize(patchSource(source)), source);
  }
});

test('patching is idempotent and rejects missing, duplicated, or partial anchors', () => {
  assert.equal(patchSource(changed), changed);
  assert.throws(() => patchSource(original.replace(edits[1].stock, 'children:[s,null,')), /Unsupported/);
  assert.throws(() => patchSource(original + edits[1].stock), /ambiguous/);
  assert.throws(() => patchSource(original.replace(edits[0].stock, edits[0].patched)), /Partially patched/);
});

test('apply and restore preserve the original and refuse unrelated edits', context => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'codex-empty-header-test-'));
  context.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const assets = path.join(root, 'webview', 'assets');
  fs.mkdirSync(assets, { recursive: true });
  fs.writeFileSync(path.join(root, 'package.json'), JSON.stringify({
    publisher: 'openai', name: 'chatgpt', version: 'test',
  }));
  const file = path.join(assets, 'new-thread-panel-page-test.js');
  fs.writeFileSync(file, original);
  fs.writeFileSync(path.join(assets, 'app-initial-test.js'),
    'route("/extension/panel/new");import("./new-thread-panel-page-test.js")');
  fs.writeFileSync(path.join(assets, target.variant.headerAsset), 'export{t as Header}');
  assert.equal(update(loadTarget(root), 'apply').changed, true);
  assert.equal(fs.readFileSync(file, 'utf8'), changed);
  assert.equal(fs.readFileSync(file + '.codex-empty-header-original', 'utf8'), original);
  assert.equal(update(loadTarget(root), 'apply').changed, false);
  assert.equal(update(loadTarget(root), 'restore').changed, true);
  assert.equal(fs.readFileSync(file, 'utf8'), original);
  fs.appendFileSync(file, '\n// unrelated local edit\n');
  const drift = fs.readFileSync(file, 'utf8');
  assert.throws(() => update(loadTarget(root), 'apply'), /differs/);
  assert.equal(fs.readFileSync(file, 'utf8'), drift);
  assert.equal(fs.readFileSync(file + '.codex-empty-header-original', 'utf8'), original);
});
