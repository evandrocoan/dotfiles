// Local installed-bundle checks, separate from the portable repository CI gate.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');
const { ASSET, BACKUP_SUFFIX, edits, integrity, patchSource, loadTarget, update } = require('./patch.cjs');

const installed = loadTarget(process.env.CODEX_DESKTOP_TEST_ASAR);
const original = installed.original;
const patched = patchSource(original);
const neighbor = Buffer.from('An unrelated asset must remain byte-for-byte unchanged.');

function fixture(t, source = original, alterHeader = () => {}) {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'codex-sidebar-test-'));
  t.after(() => fs.rmSync(directory, { recursive: true, force: true }));
  const archive = path.join(directory, 'app.asar');
  const manifest = Buffer.from(JSON.stringify({ name: 'openai-codex-electron', version: 'fixture' }));
  const bytes = Buffer.from(source);
  const assetName = ASSET.split('/').at(-1);
  const header = { files: {
    'package.json': { size: manifest.length, offset: '0' },
    webview: { files: { assets: { files: {
      [assetName]: { size: bytes.length, offset: String(manifest.length),
        integrity: integrity(bytes, 4 * 1024 * 1024) },
    } } } },
    'neighbor.txt': { size: neighbor.length, offset: String(manifest.length + bytes.length) },
  } };
  alterHeader(header);
  const json = Buffer.from(JSON.stringify(header));
  const headerSize = 4 + Math.ceil((json.length + 4) / 4) * 4;
  const prefix = Buffer.alloc(headerSize + 8);
  prefix.writeUInt32LE(4, 0);
  prefix.writeUInt32LE(headerSize, 4);
  prefix.writeUInt32LE(headerSize - 4, 8);
  prefix.writeUInt32LE(json.length, 12);
  json.copy(prefix, 16);
  fs.writeFileSync(archive, Buffer.concat([prefix, manifest, bytes, neighbor]), { mode: 0o640 });
  return archive;
}

function components(source) {
  const jsx = (type, props) => ({ type, props });
  const context = {
    eQo: { c: count => Array(count).fill(Symbol.for('react.memo_cache_sentinel')) },
    aBo: { c: count => Array(count).fill(Symbol.for('react.memo_cache_sentinel')) },
    P0: { jsx, jsxs: jsx }, oBo: { jsx, jsxs: jsx }, XHo: { jsx },
    Cp: () => ({ formatMessage: message => message.id === 'Remove from section' ? 'Remover da seção' : message.id }),
    Lq: { archiveThread: { id: 'Archive chat' }, moreActions: { id: 'More actions' } },
    ZHo: { id: 'Remove from section' },
    $se: 'unpin-icon', Uhe: 'pin-icon', BTe: 'archive-icon', L1: 'pin-indicator',
    f1: 'row-action-rail', CZo: 'menu-trigger', Dc: 'button', Hn: 'tooltip',
    hf: (...values) => values.filter(Boolean).join(' '),
    iBo: () => {}, rBo: () => {},
  };
  const names = ['XZo', 'YHo', 'nBo'];
  const functions = names.map(name => {
    const start = source.indexOf(`function ${name}(`);
    assert.notEqual(start, -1, `Installed bundle must contain ${name}`);
    const next = source.indexOf('function ', start + 9);
    return source.slice(start, next);
  });
  const result = vm.runInNewContext(functions.join('\n') + ';({ XZo, YHo })', context);
  // Execute the actual compiled indicator expressions from each sidebar row owner.
  // React itself is outside this rendering boundary; the action-selection expressions stay real.
  result.indicator = (index, values) => {
    const { stock, patched: replacement } = edits[index];
    const matches = [stock, replacement].filter(fragment => source.includes(fragment));
    assert.equal(matches.length, 1);
    const fragment = source.slice(source.indexOf(matches[0]), source.indexOf(matches[0]) + matches[0].length);
    const variable = ['E', 'm', 'l', 'T'][index - 1];
    return vm.runInNewContext(`let ${variable};${fragment};${variable}`, { ...context, ...values, YHo: result.YHo });
  };
  return result;
}

function indicatorValues(index, isPinned, removeFromSection) {
  switch (index) {
    case 1: return { _: true, o: removeFromSection, p: false, m: false, x: isPinned, T: 'row action', C() {} };
    case 2: return { Fe: true, E: removeFromSection, ae: false, o: isPinned, p: 'row action', l() {} };
    case 3: return { Fe: true, E: removeFromSection, ae: false, o: isPinned, n: true,
      e: { task: { id: 'remote-chat', has_unread_turn: false } }, c: 'row action', ut() {} };
    case 4: return { b: true, x: false, o: isPinned, S: true, l: false, f: 'local-chat',
      U: { formatMessage: message => message.id }, B1: { id: 'Unpin' }, z1: { id: 'Pin' }, ut() {} };
    default: throw new Error('Unknown row expression.');
  }
}

function nodes(node) {
  if (node == null || typeof node !== 'object') return [];
  if (Array.isArray(node)) return node.flatMap(nodes);
  if (typeof node.type === 'function') return nodes(node.type(node.props));
  return [node, ...nodes(node.props?.children)];
}

test('stock components expose the accidental archive and pin targets (negative control)', () => {
  const { XZo, YHo } = components(original);
  let archived = 0;
  let pinned = 0;
  const rendered = nodes(XZo({ archive: () => archived++,
    pinAction: { ariaLabel: 'Pin chat', isPinned: false, onClick: () => pinned++ } }));
  const buttons = rendered.filter(node => node.type === 'button');
  assert.deepEqual(buttons.map(node => node.props['aria-label']), ['Pin chat', 'Archive chat']);
  const event = { stopPropagation() {} };
  buttons[0].props.onClick(event);
  buttons[1].props.onClick(event);
  assert.equal(pinned, 1);
  assert.equal(archived, 1);
  assert.equal(nodes(YHo({ isPinned: true, hasUnreadTurn: false }).hover)
    .filter(node => node.type === 'pin-indicator').length, 1);
});

test('patched installed components remove inline targets and retain menu and other actions', () => {
  const { XZo, indicator } = components(patched);
  let archived = 0;
  let pinned = 0;
  const getItems = () => [{ id: 'archive-thread', onSelect: () => archived++ },
    { id: 'pin-thread', onSelect: () => pinned++ }];
  const primaryAction = { type: 'other-action', props: {} };
  for (const isPinned of [false, true]) {
    const rendered = nodes(XZo({ archive: () => archived++, retainArchiveAction: true,
      pinAction: { ariaLabel: isPinned ? 'Unpin chat' : 'Pin chat', isPinned, onClick: () => pinned++ },
      getMenuItems: getItems, primaryAction }));
    assert.deepEqual(rendered.filter(node => node.type === 'button'), []);
    assert.equal(rendered.filter(node => node.type === 'other-action').length, 1);
    const menu = rendered.find(node => node.type === 'menu-trigger');
    assert.equal(menu.props.getItems, getItems);
    assert.deepEqual(menu.props.getItems().map(item => item.id), ['archive-thread', 'pin-thread']);
    for (const index of [1, 2, 3, 4]) {
      const value = indicator(index, indicatorValues(index, isPinned, undefined));
      assert.deepEqual(nodes([value.rest, value.hover]), []);
    }
  }
  assert.equal(archived, 0);
  assert.equal(pinned, 0);
  const items = getItems();
  items[0].onSelect();
  items[1].onSelect();
  assert.equal(archived, 1);
  assert.equal(pinned, 1);
  // With no menu or other action, the entire action rail disappears, leaving the row as hit target.
  assert.deepEqual(nodes(XZo({ archive() {}, pinAction: { ariaLabel: 'Pin', onClick() {} } })), []);
});

test('custom-section removal remains available in both inline and indicator paths', () => {
  const stockComponents = components(original);
  const patchedComponents = components(patched);
  let removed = 0;
  const remove = () => removed++;
  const rendered = nodes(patchedComponents.XZo({ archive() { throw new Error('Unexpected archive'); },
    pinAction: { ariaLabel: 'Remover da seção', isPinned: true, onClick: remove } }));
  const buttons = rendered.filter(node => node.type === 'button');
  assert.deepEqual(buttons.map(node => node.props['aria-label']), ['Remover da seção']);
  buttons[0].props.onClick({ stopPropagation() {} });
  assert.equal(removed, 1);
  for (const index of [1, 2, 3]) {
    for (const isPinned of [false, true]) {
      const values = indicatorValues(index, isPinned, remove);
      const stock = stockComponents.indicator(index, values);
      const changed = patchedComponents.indicator(index, values);
      assert.equal(nodes(stock.hover).filter(node => node.type === 'pin-indicator').length, 1);
      assert.equal(nodes(changed.hover).filter(node => node.type === 'pin-indicator').length, 1);
      assert.equal(changed.hover.props.isPinned, stock.hover.props.isPinned);
      assert.equal(changed.hover.props.ariaLabel, stock.hover.props.ariaLabel);
      // The same real expressions expose a pin action without a section-removal callback.
      const pin = stockComponents.indicator(index, indicatorValues(index, isPinned, undefined));
      assert.equal(nodes(pin.hover).filter(node => node.type === 'pin-indicator').length, 1);
    }
  }
});

test('ASAR apply is idempotent and restore reproduces every original byte and permissions', t => {
  const archive = fixture(t);
  const before = fs.readFileSync(archive);
  const originalStat = fs.statSync(archive);
  const beforeTarget = loadTarget(archive);
  assert.equal(beforeTarget.applied, false);
  const applied = update(beforeTarget, 'apply');
  assert.equal(applied.changed, true);
  const after = loadTarget(archive);
  assert.equal(after.applied, true);
  assert.equal(after.headerBytes.length, beforeTarget.headerBytes.length);
  assert.equal(after.asset.offset, beforeTarget.asset.offset);
  assert.equal(after.asset.size, beforeTarget.asset.size);
  assert.equal(after.stat.size, originalStat.size);
  assert.equal(after.stat.mode, originalStat.mode);
  assert.equal(after.stat.uid, originalStat.uid);
  assert.equal(after.stat.gid, originalStat.gid);
  assert.deepEqual(fs.readFileSync(archive).subarray(-neighbor.length), neighbor);
  const backup = fs.readFileSync(archive + BACKUP_SUFFIX);
  assert.deepEqual(backup, Buffer.from(original));
  assert.equal(update(after, 'apply').changed, false);
  assert.equal(fs.statSync(archive).ino, after.stat.ino);
  assert.deepEqual(fs.readFileSync(archive + BACKUP_SUFFIX), backup);
  assert.equal(update(loadTarget(archive), 'restore').changed, true);
  assert.deepEqual(fs.readFileSync(archive), before);
  assert.equal(update(loadTarget(archive), 'restore').changed, false);
});

test('unknown and partial bundles are rejected before mutation', t => {
  for (const [source, message] of [
    [original + '\n', /Unknown sidebar bundle/],
    [original.replace(edits[0].stock, edits[0].patched), /Partially patched/],
  ]) {
    const archive = fixture(t, source);
    const before = fs.readFileSync(archive);
    assert.throws(() => loadTarget(archive), message);
    assert.deepEqual(fs.readFileSync(archive), before);
    assert.equal(fs.existsSync(archive + BACKUP_SUFFIX), false);
  }
});

test('corrupt integrity, out-of-range offsets and overlapping assets are rejected', t => {
  const assetAt = header => header.files.webview.files.assets.files[ASSET.split('/').at(-1)];
  for (const [change, message] of [
    [header => { assetAt(header).integrity.hash = '0'.repeat(64); }, /integrity mismatch/],
    [header => { assetAt(header).offset = '999999999'; }, /outside the archive/],
    [header => { header.files.alias = { size: 5, offset: assetAt(header).offset }; }, /shares sidebar bytes/],
  ]) {
    const archive = fixture(t, original, change);
    assert.throws(() => loadTarget(archive), message);
    assert.equal(fs.existsSync(archive + BACKUP_SUFFIX), false);
  }
});

test('stale inspection and incompatible backups cannot replace the archive', t => {
  const archive = fixture(t);
  const target = loadTarget(archive);
  fs.appendFileSync(archive, 'concurrent change');
  const current = fs.readFileSync(archive);
  assert.throws(() => update(target, 'apply'), /app changed during inspection/);
  assert.deepEqual(fs.readFileSync(archive), current);
  assert.equal(fs.existsSync(archive + BACKUP_SUFFIX), false);
  fs.writeFileSync(archive + BACKUP_SUFFIX, 'unrelated backup');
  assert.throws(() => update(loadTarget(archive), 'apply'), /backup differs/);
  assert.deepEqual(fs.readFileSync(archive), current);
  assert.equal(fs.readFileSync(archive + BACKUP_SUFFIX, 'utf8'), 'unrelated backup');
});

test('symlink targets and symlink backups are rejected', t => {
  const archive = fixture(t);
  const alias = archive + '.alias';
  fs.symlinkSync(path.basename(archive), alias);
  assert.throws(() => loadTarget(alias), /Expected a regular file/);
  const unrelated = archive + '.unrelated';
  fs.writeFileSync(unrelated, 'preserve me');
  fs.symlinkSync(path.basename(unrelated), archive + BACKUP_SUFFIX);
  assert.throws(() => update(loadTarget(archive), 'apply'), /Expected a regular file/);
  assert.equal(fs.readFileSync(unrelated, 'utf8'), 'preserve me');
  assert.equal(loadTarget(archive).applied, false);
});

test('a patched archive cannot be rewritten without its original backup', t => {
  const archive = fixture(t, patched);
  const before = fs.readFileSync(archive);
  for (const action of ['apply', 'restore']) {
    assert.throws(() => update(loadTarget(archive), action), /No original sidebar backup/);
  }
  assert.deepEqual(fs.readFileSync(archive), before);
});
