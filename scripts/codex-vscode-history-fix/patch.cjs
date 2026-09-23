// Local workaround for https://github.com/openai/codex/issues/15368.
// Deliberately reject unfamiliar bundles instead of guessing at a new implementation.
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { randomUUID } = require('node:crypto');
const { spawnSync } = require('node:child_process');

const LIMIT = 199;
const edits = [
  {
    stock: 'function R$t(e,t,n){return an(e)||!t&&e===`local`?50:n?0:500}',
    patched: `function R$t(e,t,n){return !t&&e===\`local\`?${LIMIT}:an(e)?50:n?0:500}`,
    legacy: ['function R$t(e,t,n){return an(e)||!t&&e===`local`?Number.POSITIVE_INFINITY:n?0:500}'],
  },
  {
    stock: 'let i=(t===`expanded`||n)&&r>50,a=i?r:50',
    patched: `let i=(r===${LIMIT}||t===\`expanded\`||n)&&r>50,a=i?r:50`,
    legacy: [
      'let i=r>50,a=i?r:50',
      'let i=(r===Number.POSITIVE_INFINITY||t===`expanded`||n)&&r>50,a=i?r:50',
    ],
  },
  {
    stock: 'this.replaceRecentThreadSummaries(t),c=e.slice(0,50)',
    patched: `this.replaceRecentThreadSummaries(t),c=r===${LIMIT}?e:e.slice(0,50)`,
    legacy: ['this.replaceRecentThreadSummaries(t),c=r===Number.POSITIVE_INFINITY?e:e.slice(0,50)'],
  },
];

function normalize(source) {
  let result = source;
  for (const edit of edits) {
    const matches = [edit.stock, edit.patched, ...edit.legacy]
      .flatMap(candidate => Array(result.split(candidate).length - 1).fill(candidate));
    if (matches.length !== 1) {
      throw new Error('Unsupported or ambiguous bundle structure. Inspect the new extension before adapting the patch.');
    }
    result = result.replace(matches[0], edit.stock);
  }
  return result;
}

function patchSource(source) {
  return edits.reduce((result, edit) => result.replace(edit.stock, edit.patched), normalize(source));
}

function installedExtension(home = os.homedir()) {
  const root = path.join(home, '.vscode', 'extensions');
  const entries = JSON.parse(fs.readFileSync(path.join(root, 'extensions.json'), 'utf8'))
    .filter(entry => entry.identifier?.id === 'openai.chatgpt');
  if (entries.length !== 1 || !entries[0].relativeLocation) {
    throw new Error('Cannot identify one installed Codex extension. Use --extension-dir with its exact directory.');
  }
  const selected = path.resolve(root, entries[0].relativeLocation);
  if (!selected.startsWith(root + path.sep)) throw new Error('Extension location is outside the registry directory.');
  return selected;
}

function loadTarget(directory = installedExtension()) {
  const root = fs.realpathSync(directory);
  const manifest = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8'));
  if (manifest.publisher !== 'openai' || manifest.name !== 'chatgpt') {
    throw new Error('The selected directory is not the Codex extension.');
  }
  const assets = path.join(root, 'webview', 'assets');
  const candidates = fs.readdirSync(assets).filter(name => /^app-initial-.*\.js$/.test(name));
  const matches = [];
  for (const name of candidates) {
    const file = fs.realpathSync(path.join(assets, name));
    if (!file.startsWith(root + path.sep)) throw new Error('Asset symlink escapes the selected extension.');
    const source = fs.readFileSync(file, 'utf8');
    if (source.includes('async runRecentConversationRefresh(')) matches.push({ file, source });
  }
  if (matches.length !== 1) throw new Error('Cannot identify exactly one supported history bundle.');
  const target = matches[0];
  const html = fs.readFileSync(path.join(root, 'webview', 'index.html'), 'utf8');
  if (!html.includes(`./assets/${path.basename(target.file)}`)) {
    throw new Error('History bundle is not referenced by the webview entry point.');
  }
  return { ...target, root, version: manifest.version };
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
  const patched = patchSource(original);
  const backup = target.file + '.codex-original';
  const exists = fs.existsSync(backup);
  if (exists && fs.readFileSync(backup, 'utf8') !== original) {
    throw new Error('Original backup differs from this bundle. Refusing to overwrite local changes.');
  }
  if (action === 'restore' && !exists) throw new Error('No original backup exists for this installation.');
  if (!exists && target.source !== original) throw new Error('A modified bundle has no original backup.');
  const desired = action === 'restore' ? original : patched;
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
    console.log('Usage: node patch.cjs [--check | --apply | --restore] [--extension-dir DIRECTORY]\n'
      + 'Default: --check (read only). Detects the installed desktop VS Code Codex extension.\n'
      + `Loads up to ${LIMIT} recent local conversations, retaining the existing handling of open chats.\n`
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
      throw new Error(`Codex ${target.version}: the ${LIMIT}-conversation patch is not applied. Run --apply.`);
    }
    validateSyntax(target.source);
    console.log(`OK: Codex ${target.version}, local history limit ${LIMIT}.\n${target.file}`);
  } else {
    const result = update(target, action);
    console.log(`${result.changed ? 'Updated' : 'Already correct'}: Codex ${target.version} (${action}).\n`
      + `Backup: ${result.backup}\nUse Developer: Reload Window in VS Code.`);
  }
}

module.exports = { LIMIT, edits, normalize, patchSource, installedExtension, loadTarget, update };
if (require.main === module) {
  try { main(process.argv.slice(2)); }
  catch (error) { console.error(`Error: ${error.message}`); process.exitCode = 1; }
}
