// Hide the chat row's inline archive and pin controls in the Linux desktop app.
const fs = require('node:fs');
const path = require('node:path');
const { createHash, randomUUID } = require('node:crypto');
const { spawnSync } = require('node:child_process');

const DEFAULT_ARCHIVE = '/usr/lib/chatgpt/resources/app.asar';
const ASSET = 'webview/assets/app-initial-ed5807835d97.js';
const ORIGINAL_HASH = 'a9f4a1a86c7486b97b750b97296d83c8c8c67074144480b697244f0c8b6ef720';
const BACKUP_SUFFIX = '.codex-sidebar-original';
const edits = [
  {
    stock: 'let g;t[7]!==m||t[8]!==h?(g=[...m,...h],t[7]=m,t[8]=h,t[9]=g):g=t[9];',
    replacement: 'let g=l&&l.ariaLabel===p.formatMessage(ZHo)?m:[];',
  },
  // The same pin-shaped control also represents "Remove from section". Keep that action.
  {
    stock: 'E=_&&!p&&!m?YHo({isPinned:x,hasUnreadTurn:!1,ariaLabel:T,onPin:()=>C(!0),onUnpin:()=>C(!1)}):{rest:null,hover:null}',
    replacement: 'E=_&&o&&!p&&!m?YHo({isPinned:x,ariaLabel:T,onPin:()=>C(!0),onUnpin:()=>C(!1)}):{rest:null,hover:null}',
  },
  {
    stock: 'm=Fe&&!ae?YHo({isPinned:o,hasUnreadTurn:!1,ariaLabel:p,onPin:()=>{l(!0)},onUnpin:()=>{l(!1)}}):{rest:null,hover:null}',
    replacement: 'm=Fe&&E&&!ae?YHo({isPinned:o,hasUnreadTurn:!1,ariaLabel:p,onPin:()=>l(!0),onUnpin:()=>l(!1)}):{rest:null,hover:null}',
  },
  {
    stock: 'l=Fe&&!ae?YHo({isPinned:o,hasUnreadTurn:!n&&e.task.has_unread_turn,ariaLabel:c,onPin:()=>{ut(e.task.id,!0)},onUnpin:()=>{ut(e.task.id,!1)}}):{rest:null,hover:null}',
    replacement: 'l=Fe&&E&&!ae?YHo({isPinned:o,hasUnreadTurn:!n&&e.task.has_unread_turn,ariaLabel:c,onPin:()=>ut(e.task.id,!0),onUnpin:()=>ut(e.task.id,!1)}):{rest:null,hover:null}',
  },
  {
    stock: 'T=b&&!x?YHo({isPinned:o,hasUnreadTurn:!S&&l,ariaLabel:U.formatMessage(o?B1:z1),onPin:()=>{ut(f,!0)},onUnpin:()=>{ut(f,!1)}}):{rest:null,hover:null}',
    replacement: 'T={rest:null,hover:null}',
  },
].map(({ stock, replacement }) => {
  if (replacement.length > stock.length) throw new Error('Replacement exceeds the available byte range.');
  return { stock, patched: replacement.padEnd(stock.length, ' ') };
});

function sha256(bytes) {
  return createHash('sha256').update(bytes).digest('hex');
}

function normalize(source) {
  const states = edits.map(({ stock, patched }) => {
    const stockCount = source.split(stock).length - 1;
    const patchedCount = source.split(patched).length - 1;
    if (stockCount + patchedCount !== 1) throw new Error('Unsupported or ambiguous sidebar bundle.');
    return patchedCount === 1;
  });
  if (states.some(state => state !== states[0])) throw new Error('Partially patched sidebar bundle.');
  const original = edits.reduce((result, edit) => result.replace(edit.patched, edit.stock), source);
  if (sha256(Buffer.from(original)) !== ORIGINAL_HASH) {
    throw new Error('Unknown sidebar bundle. Inspect the new app before adapting this patch.');
  }
  return original;
}

function patchSource(source) {
  return edits.reduce((result, edit) => result.replace(edit.stock, edit.patched), normalize(source));
}

function readExact(fd, length, position) {
  const bytes = Buffer.alloc(length);
  let count = 0;
  while (count < length) {
    const n = fs.readSync(fd, bytes, count, length - count, position + count);
    if (n === 0) throw new Error('Truncated ASAR archive.');
    count += n;
  }
  return bytes;
}

function regularFile(file) {
  const stat = fs.lstatSync(file);
  if (!stat.isFile()) throw new Error(`Expected a regular file, not a symlink: ${file}`);
  return stat;
}

function entryAt(header, name) {
  let entry = header;
  for (const part of name.split('/')) entry = entry?.files?.[part];
  if (!entry || entry.unpacked || entry.link || !Number.isSafeInteger(entry.size)
    || entry.size < 0 || !/^(0|[1-9][0-9]*)$/.test(entry.offset)) {
    throw new Error(`Missing or unsupported packed asset: ${name}`);
  }
  return entry;
}

function integrity(bytes, blockSize) {
  if (!Number.isSafeInteger(blockSize) || blockSize <= 0) throw new Error('Invalid integrity block size.');
  const blocks = [];
  for (let offset = 0; offset < bytes.length; offset += blockSize) {
    blocks.push(sha256(bytes.subarray(offset, offset + blockSize)));
  }
  return { algorithm: 'SHA256', hash: sha256(bytes), blockSize, blocks };
}

function verifyIntegrity(bytes, expected) {
  if (expected?.algorithm !== 'SHA256') throw new Error('Missing SHA256 integrity metadata.');
  const actual = integrity(bytes, expected.blockSize);
  if (actual.hash !== expected.hash || JSON.stringify(actual.blocks) !== JSON.stringify(expected.blocks)) {
    throw new Error('Sidebar asset integrity mismatch. No changes made.');
  }
}

function loadTarget(archive = DEFAULT_ARCHIVE) {
  const file = path.resolve(archive);
  const stat = regularFile(file);
  const fd = fs.openSync(file, 'r');
  try {
    const prefix = readExact(fd, 16, 0);
    const headerSize = prefix.readUInt32LE(4);
    const jsonSize = prefix.readUInt32LE(12);
    if (prefix.readUInt32LE(0) !== 4 || headerSize < 8 || headerSize > 16 * 1024 * 1024
      || prefix.readUInt32LE(8) !== headerSize - 4
      || headerSize !== 4 + Math.ceil((jsonSize + 4) / 4) * 4 || headerSize + 8 > stat.size) {
      throw new Error('Unsupported ASAR header.');
    }
    const headerBytes = readExact(fd, headerSize + 8, 0);
    const json = headerBytes.subarray(16, 16 + jsonSize);
    const header = JSON.parse(json.toString('utf8'));
    if (!Buffer.from(JSON.stringify(header)).equals(json)) throw new Error('Unsupported ASAR JSON encoding.');
    const dataOffset = headerSize + 8;
    function readEntry(name) {
      const entry = entryAt(header, name);
      const offset = Number(entry.offset);
      if (!Number.isSafeInteger(offset) || offset + entry.size > stat.size - dataOffset) {
        throw new Error(`ASAR asset is outside the archive: ${name}`);
      }
      return readExact(fd, entry.size, dataOffset + offset);
    }
    const manifest = JSON.parse(readEntry('package.json').toString('utf8'));
    if (manifest.name !== 'openai-codex-electron') throw new Error('This is not the Codex desktop app.');
    const asset = entryAt(header, ASSET);
    const bytes = readEntry(ASSET);
    verifyIntegrity(bytes, asset.integrity);
    const source = bytes.toString('utf8');
    if (!Buffer.from(source).equals(bytes)) throw new Error('Invalid UTF-8 sidebar asset.');
    const original = normalize(source);
    const patched = patchSource(original);
    if (Buffer.byteLength(patched) !== bytes.length) throw new Error('Patch changes the asset length.');
    function checkOverlap(node, prefix = '') {
      for (const [name, entry] of Object.entries(node.files ?? {})) {
        const full = prefix + name;
        if (entry.files) checkOverlap(entry, full + '/');
        else if (full !== ASSET && !entry.unpacked && !entry.link && entry.offset != null
          && Number(entry.offset) < Number(asset.offset) + asset.size
          && Number(entry.offset) + entry.size > Number(asset.offset)) {
          throw new Error(`Another asset shares sidebar bytes: ${full}`);
        }
      }
    }
    checkOverlap(header);
    return { file, stat, headerBytes, header, dataOffset, asset, bytes, original, patched,
      version: manifest.version, applied: source === patched };
  } finally {
    fs.closeSync(fd);
  }
}

function validateSyntax(source) {
  const result = spawnSync(process.execPath, ['--check', '--input-type=module'], {
    input: source, encoding: 'utf8', timeout: 30000,
  });
  if (result.error) throw result.error;
  if (result.status !== 0) throw new Error(`JavaScript syntax check failed: ${result.stderr}`);
}

function unchanged(target) {
  const stat = regularFile(target.file);
  if (['dev', 'ino', 'size', 'mtimeMs', 'ctimeMs', 'mode', 'uid', 'gid'].some(key => stat[key] !== target.stat[key])) {
    throw new Error('The app changed during inspection. Run the command again.');
  }
  const fd = fs.openSync(target.file, 'r');
  try {
    if (!readExact(fd, target.headerBytes.length, 0).equals(target.headerBytes)
      || !readExact(fd, target.bytes.length, target.dataOffset + Number(target.asset.offset)).equals(target.bytes)) {
      throw new Error('The app changed during inspection. Run the command again.');
    }
  } finally {
    fs.closeSync(fd);
  }
}

function update(target, action) {
  if (!['apply', 'restore'].includes(action)) throw new Error('Invalid update action.');
  const backup = target.file + BACKUP_SUFFIX;
  let hasBackup = false;
  try {
    regularFile(backup);
    hasBackup = true;
    if (!fs.readFileSync(backup).equals(Buffer.from(target.original))) {
      throw new Error('Original sidebar backup differs. Refusing to overwrite it.');
    }
  } catch (error) {
    if (error.code !== 'ENOENT') throw error;
  }
  if (!hasBackup && (action === 'restore' || target.applied)) {
    throw new Error('No original sidebar backup exists for this installation.');
  }
  const desired = Buffer.from(action === 'restore' ? target.original : target.patched);
  validateSyntax(desired);
  unchanged(target);
  if (desired.equals(target.bytes)) return { changed: false, backup };
  const header = JSON.parse(JSON.stringify(target.header));
  entryAt(header, ASSET).integrity = integrity(desired, target.asset.integrity.blockSize);
  const json = Buffer.from(JSON.stringify(header));
  if (json.length !== target.headerBytes.readUInt32LE(12)) throw new Error('Patch changes the ASAR header length.');
  const headerBytes = Buffer.from(target.headerBytes);
  json.copy(headerBytes, 16);
  if (!hasBackup) {
    const fd = fs.openSync(backup, 'wx', target.stat.mode & 0o777);
    try {
      fs.writeFileSync(fd, Buffer.from(target.original));
      fs.fsyncSync(fd);
    } finally {
      fs.closeSync(fd);
    }
  }
  const temporary = target.file + '.' + randomUUID() + '.tmp';
  try {
    fs.copyFileSync(target.file, temporary, fs.constants.COPYFILE_EXCL | fs.constants.COPYFILE_FICLONE);
    unchanged(target);
    const fd = fs.openSync(temporary, 'r+');
    try {
      fs.writeFileSync(fd, headerBytes);
      // writeFileSync on a descriptor advances its cursor; the asset has a separate absolute offset.
      let count = 0;
      while (count < desired.length) {
        count += fs.writeSync(fd, desired, count, desired.length - count,
          target.dataOffset + Number(target.asset.offset) + count);
      }
      fs.fchmodSync(fd, target.stat.mode & 0o777);
      const stat = fs.fstatSync(fd);
      if (stat.uid !== target.stat.uid || stat.gid !== target.stat.gid) {
        fs.fchownSync(fd, target.stat.uid, target.stat.gid);
      }
      fs.fsyncSync(fd);
    } finally {
      fs.closeSync(fd);
    }
    const candidate = loadTarget(temporary);
    if (!candidate.bytes.equals(desired) || candidate.stat.size !== target.stat.size) {
      throw new Error('Candidate archive verification failed.');
    }
    unchanged(target);
    fs.renameSync(temporary, target.file);
    const directory = fs.openSync(path.dirname(target.file), 'r');
    try { fs.fsyncSync(directory); } finally { fs.closeSync(directory); }
  } finally {
    if (fs.existsSync(temporary)) fs.unlinkSync(temporary);
  }
  if (!loadTarget(target.file).bytes.equals(desired)) throw new Error('Post-write verification failed.');
  return { changed: true, backup };
}

function main(args) {
  if (args.length === 1 && args[0] === '--help') {
    console.log('Usage: node patch.cjs [--check | --apply | --restore] [--app-asar FILE]\n'
      + `Default: --check (read only), ${DEFAULT_ARCHIVE}\n`
      + 'Hides inline archive and pin/unpin controls on sidebar chat rows.\n'
      + 'Keeps context menus and other row actions. Restart the app normally afterward.');
    return;
  }
  let action = 'check';
  let archive;
  let actionGiven = false;
  for (let i = 0; i < args.length; i++) {
    if (['--check', '--apply', '--restore'].includes(args[i]) && !actionGiven) {
      action = args[i].slice(2);
      actionGiven = true;
    } else if (args[i] === '--app-asar' && !archive && args[i + 1] && !args[i + 1].startsWith('--')) {
      archive = args[++i];
    } else throw new Error(`Invalid argument: ${args[i]}. Use --help.`);
  }
  const target = loadTarget(archive);
  if (action === 'check') {
    if (!target.applied) throw new Error(`Codex ${target.version}: sidebar patch is not applied. Run --apply.`);
    validateSyntax(target.bytes);
    console.log(`OK: Codex ${target.version}, inline archive and pin controls hidden.\n${target.file}`);
  } else {
    const result = update(target, action);
    console.log(`${result.changed ? 'Updated' : 'Already correct'}: Codex ${target.version} (${action}).\n`
      + `Original asset backup: ${result.backup}\nRestart the app normally to load the change.`);
  }
}

module.exports = { ASSET, ORIGINAL_HASH, BACKUP_SUFFIX, edits, sha256, integrity, normalize, patchSource,
  loadTarget, update };
if (require.main === module) {
  try { main(process.argv.slice(2)); }
  catch (error) { console.error(`Error: ${error.message}`); process.exitCode = 1; }
}
