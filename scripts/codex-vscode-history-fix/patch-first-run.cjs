// Local workaround for https://github.com/openai/codex/issues/25146.
// Reject unfamiliar bundles rather than bypassing a changed first-run flow.
const fs = require('node:fs');
const path = require('node:path');
const { randomUUID } = require('node:crypto');
const { spawnSync } = require('node:child_process');
const { installedExtension } = require('./patch.cjs');

const stock = 'function pcr(){let{data:e,isLoading:t}=iS(Cs.NUX_2025_09_15),{authMethod:n}=Zl();if(!t)return e||n==null?`none`:n===`chatgptAuthTokens`||n===`chatgpt`?`2025-09-15-full-chatgpt-auth`:`2025-09-15-apikey-auth`}';
const patched = 'function pcr(){return `none`}';
const routeGuard = 'function hcr(e){let t=(0,gcr.c)(4),{children:n}=e,r=pcr();';
const redirect = '$r,{to:`/first-run`,replace:!0}';

function normalize(source) {
  const count = [stock, patched].reduce((total, candidate) => total + source.split(candidate).length - 1, 0);
  if (count !== 1 || !source.includes(routeGuard) || !source.includes(redirect)) {
    throw new Error('Unsupported or ambiguous first-run bundle. Inspect the new extension before adapting the patch.');
  }
  return source.replace(patched, stock);
}

function patchSource(source) {
  return normalize(source).replace(stock, patched);
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
    if (source.includes('function hcr(e)') && source.includes('function pcr()')) matches.push({ file, source });
  }
  if (matches.length !== 1) throw new Error('Cannot identify exactly one supported first-run bundle.');
  const target = matches[0];
  const html = fs.readFileSync(path.join(root, 'webview', 'index.html'), 'utf8');
  if (!html.includes(`./assets/${path.basename(target.file)}`)) {
    throw new Error('First-run bundle is not referenced by the webview entry point.');
  }
  normalize(target.source);
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
  const backup = target.file + '.codex-first-run-original';
  const exists = fs.existsSync(backup);
  if (exists && fs.readFileSync(backup, 'utf8') !== original) {
    throw new Error('Original backup differs from this bundle. Refusing to overwrite local changes.');
  }
  if (action === 'restore' && !exists) throw new Error('No original first-run backup exists for this installation.');
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
    console.log('Usage: node patch-first-run.cjs [--check | --apply | --restore] [--extension-dir DIRECTORY]\n'
      + 'Default: --check (read only). Targets the installed desktop VS Code Codex extension.\n'
      + 'Disables the repeated first-run walkthrough for this local extension installation.\n'
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
      throw new Error(`Codex ${target.version}: first-run patch is not applied. Run --apply.`);
    }
    validateSyntax(target.source);
    console.log(`OK: Codex ${target.version}, repeated first-run walkthrough disabled.\n${target.file}`);
  } else {
    const result = update(target, action);
    console.log(`${result.changed ? 'Updated' : 'Already correct'}: Codex ${target.version} (${action}).\n`
      + `Backup: ${result.backup}\nUse Developer: Reload Window in VS Code.`);
  }
}

module.exports = { stock, patched, normalize, patchSource, loadTarget, update };
if (require.main === module) {
  try { main(process.argv.slice(2)); }
  catch (error) { console.error(`Error: ${error.message}`); process.exitCode = 1; }
}
