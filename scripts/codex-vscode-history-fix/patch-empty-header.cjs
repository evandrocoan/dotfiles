// Local workaround for https://github.com/openai/codex/issues/44100.
// Add the existing navigation header to an empty Codex editor tab.
const fs = require('node:fs');
const path = require('node:path');
const { randomUUID } = require('node:crypto');
const { spawnSync } = require('node:child_process');
const { installedExtension } = require('./patch.cjs');

const headerAsset = 'header-4be255c13706.js';
const stockImport = 'import{r as k,t as A}from"./codex-home-announcements-bd7d6b208bdb.js";function j(){';
const patchedImport = `import{r as k,t as A}from"./codex-home-announcements-bd7d6b208bdb.js";import{Header as H}from"./${headerAsset}";function j(){`;
const stockBody = 'children:[s,(0,F.jsx)(`div`,{className:`flex h-full flex-col`';
const patchedBody = 'children:[s,(0,F.jsx)(H,{}),(0,F.jsx)(`div`,{className:`flex h-full flex-col`';
const edits = [
  { stock: stockImport, patched: patchedImport },
  { stock: stockBody, patched: patchedBody },
];

function normalize(source) {
  const states = edits.map(edit => {
    const stockCount = source.split(edit.stock).length - 1;
    const patchedCount = source.split(edit.patched).length - 1;
    if (stockCount + patchedCount !== 1) {
      throw new Error('Unsupported or ambiguous new-tab bundle. Inspect the new extension before adapting the patch.');
    }
    return patchedCount === 1;
  });
  if (states[0] !== states[1] || !source.includes('export{j as NewThreadPanelPage}')) {
    throw new Error('Partially patched or unsupported new-tab bundle. No changes made.');
  }
  return edits.reduce((result, edit) => result.replace(edit.patched, edit.stock), source);
}

function patchSource(source) {
  return edits.reduce((result, edit) => result.replace(edit.stock, edit.patched), normalize(source));
}

function loadTarget(directory = installedExtension()) {
  const root = fs.realpathSync(directory);
  const manifest = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8'));
  if (manifest.publisher !== 'openai' || manifest.name !== 'chatgpt') {
    throw new Error('The selected directory is not the Codex extension.');
  }
  const assets = path.join(root, 'webview', 'assets');
  const candidates = fs.readdirSync(assets).filter(name => /^new-thread-panel-page-.*\.js$/.test(name));
  const matches = [];
  for (const name of candidates) {
    const file = fs.realpathSync(path.join(assets, name));
    if (!file.startsWith(root + path.sep)) throw new Error('Asset symlink escapes the selected extension.');
    const source = fs.readFileSync(file, 'utf8');
    if (source.includes('export{j as NewThreadPanelPage}')) matches.push({ file, source });
  }
  if (matches.length !== 1) throw new Error('Cannot identify exactly one supported new-tab bundle.');
  const target = matches[0];
  normalize(target.source);
  const routeOwners = fs.readdirSync(assets).filter(name => /^app-initial-.*\.js$/.test(name))
    .filter(name => {
      const source = fs.readFileSync(path.join(assets, name), 'utf8');
      return source.includes(`/extension/panel/new`) && source.includes(`./${path.basename(target.file)}`);
    });
  if (routeOwners.length !== 1) throw new Error('Cannot verify the new-tab route owns this bundle.');
  const headerFile = fs.realpathSync(path.join(assets, headerAsset));
  if (!headerFile.startsWith(root + path.sep)
    || !fs.readFileSync(headerFile, 'utf8').includes('export{t as Header}')) {
    throw new Error('Cannot verify the existing navigation header export.');
  }
  return { ...target, version: manifest.version };
}

function validateSyntax(source) {
  const result = spawnSync(process.execPath, ['--check', '--input-type=module'], {
    input: source, encoding: 'utf8', timeout: 30000,
  });
  if (result.error) throw result.error;
  if (result.status !== 0) throw new Error(`JavaScript syntax check failed: ${result.stderr}`);
}

function update(target, action) {
  const original = normalize(target.source);
  const desired = action === 'restore' ? original : patchSource(original);
  const backup = target.file + '.codex-empty-header-original';
  const exists = fs.existsSync(backup);
  if (exists && fs.readFileSync(backup, 'utf8') !== original) {
    throw new Error('Original backup differs from this bundle. Refusing to overwrite local changes.');
  }
  if (action === 'restore' && !exists) throw new Error('No original header backup exists for this installation.');
  if (!exists && target.source !== original) throw new Error('A modified bundle has no original backup.');
  validateSyntax(desired);
  if (target.source === desired) return { changed: false, backup };
  if (fs.readFileSync(target.file, 'utf8') !== target.source) {
    throw new Error('The extension changed during inspection. Run the command again.');
  }
  const mode = fs.statSync(target.file).mode & 0o777;
  if (!exists) fs.writeFileSync(backup, original, { flag: 'wx', mode });
  const temporary = target.file + '.' + randomUUID() + '.tmp';
  try {
    fs.writeFileSync(temporary, desired, { flag: 'wx', mode });
    if (fs.readFileSync(target.file, 'utf8') !== target.source) {
      throw new Error('The extension changed before replacement. No replacement was made.');
    }
    fs.renameSync(temporary, target.file);
  } finally {
    if (fs.existsSync(temporary)) fs.unlinkSync(temporary);
  }
  if (fs.readFileSync(target.file, 'utf8') !== desired) throw new Error('Post-write verification failed.');
  return { changed: true, backup };
}

function main(args) {
  if (args.includes('--help')) {
    console.log('Usage: node patch-empty-header.cjs [--check | --apply | --restore] [--extension-dir DIRECTORY]\n'
      + 'Default: --check (read only). Targets the installed desktop VS Code Codex extension.\n'
      + 'Shows the existing navigation header before the first message in a new editor tab.\n'
      + 'After --apply or --restore, use Developer: Reload Window in VS Code.');
    return;
  }
  let action = 'check';
  let directory;
  let actionGiven = false;
  for (let i = 0; i < args.length; i++) {
    if (['--check', '--apply', '--restore'].includes(args[i]) && !actionGiven) {
      action = args[i].slice(2);
      actionGiven = true;
    } else if (args[i] === '--extension-dir' && !directory && args[i + 1] && !args[i + 1].startsWith('--')) {
      directory = args[++i];
    } else throw new Error(`Invalid argument: ${args[i]}. Use --help.`);
  }
  const target = loadTarget(directory);
  if (action === 'check') {
    if (target.source !== patchSource(target.source)) {
      throw new Error(`Codex ${target.version}: new-tab header patch is not applied. Run --apply.`);
    }
    validateSyntax(target.source);
    console.log(`OK: Codex ${target.version}, new-tab navigation header enabled.\n${target.file}`);
  } else {
    const result = update(target, action);
    console.log(`${result.changed ? 'Updated' : 'Already correct'}: Codex ${target.version} (${action}).\n`
      + `Backup: ${result.backup}\nUse Developer: Reload Window in VS Code.`);
  }
}

module.exports = { headerAsset, edits, normalize, patchSource, loadTarget, update };
if (require.main === module) {
  try { main(process.argv.slice(2)); }
  catch (error) { console.error(`Error: ${error.message}`); process.exitCode = 1; }
}
