"""Apply or restore the workspace Markdown preview patch for Codex 26.1103.31037."""

import argparse
from contextlib import contextmanager
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import stat
import struct
import subprocess
import tempfile


ARCHIVE = Path("/usr/lib/chatgpt/resources/app.asar")
VERSION = "26.1103.31037"
ASSET = "webview/assets/async/80348.56fe08dd0e.js"
STOCK_OFFSET = 457119386
STOCK_SIZE = 131258
STOCK_HASH = "c2b77850a477980358d234397031fb544fef5f7a021982129f523e503e8dd12f"
BLOCK_SIZE = 4194304
MARKER = "/* local-workspace-markdown-preview */"


def replace_once(source, original, replacement):
    if source.count(original) != 1:
        raise ValueError(f"Expected exactly one patch location: {original[:95]}")
    return source.replace(original, replacement, 1)


def patch_source(original):
    component = Path(__file__).with_name("preview.js").read_text()
    source = original.decode("utf-8")
    edits = [
        (
            'function eb(e){let t,n,s=(0,l.c)(8);',
            f"{MARKER}\n{component}\nfunction eb(e){{let t,n,s=(0,l.c)(8);",
        ),
        (
            'i=null==t?null:(0,er._d)(t,n),l={canRedo:',
            'i=null==t?null:(0,er._d)(t,n);this.onPreviewMarkdown?.(n);let l={canRedo:',
        ),
        (
            'hideFileHeader:G,hostId:H,environmentId:z,initialDraft:Q',
            'hideFileHeader:G,workspaceMarkdownPreview:!G,hostId:H,environmentId:z,initialDraft:Q',
        ),
        (
            'let td=n,tc=(0,h.useRef)(null),th=(0,h.useRef)(null),tu=(0,h.useRef)(null),',
            '''const enableMarkdownPreview = e.workspaceMarkdownPreview === true;
const [previewMarkdown, setPreviewMarkdown] = h.useState(null);
const [editingMarkdown, setEditingMarkdown] = h.useState(eJ != null);
const focusMarkdownEditor = h.useRef(false);
const markdownPreviewActive = h.useRef(false);
h.useLayoutEffect(() => {
  if (enableMarkdownPreview && eJ != null) setEditingMarkdown(true);
}, [enableMarkdownPreview, eJ]);
let td=n,tc=(0,h.useRef)(null),th=(0,h.useRef)(null),tu=(0,h.useRef)(null),''',
        ),
        (
            'tu.current=i,tO(()=>i.dispose({discardUnsavedChanges:!0}))',
            'i.onPreviewMarkdown=enableMarkdownPreview?setPreviewMarkdown:void 0,'
            'tu.current=i,tO(()=>i.dispose({discardUnsavedChanges:!0}))',
        ),
        (
            'onDraftChange:tT,onEdit:tA,onLoad:()=>',
            'onDraftChange:tT,onEdit:()=>{if(enableMarkdownPreview)setEditingMarkdown(true);tA()},onLoad:()=>',
        ),
        (
            'onScrollChange:tB,onScrollSnapshotChange:tP?tI:void 0',
            'onScrollChange:e=>{if(!markdownPreviewActive.current)tB(e)},'
            'onScrollSnapshotChange:tP?e=>{if(!markdownPreviewActive.current)tI(e)}:void 0',
        ),
        (
            'onOpen:()=>{tu.current?.closeFind(),tu.current?.beginGoToLinePreview()}',
            'onOpen:()=>{if(enableMarkdownPreview)setEditingMarkdown(true);'
            'tu.current?.closeFind();tu.current?.beginGoToLinePreview()}',
        ),
        (
            'focus:()=>i.focus({preventScroll:!0}),getController:()=>Promise.resolve(n)',
            '''focus:()=>{
              if (enableMarkdownPreview) {
                setEditingMarkdown(true);
                requestAnimationFrame(() => i.focus({preventScroll: true}));
              } else i.focus({preventScroll: true});
            },getController:()=>Promise.resolve(n)''',
        ),
        (
            ':eD=eP[189],eP[190]!==eb',
            ''':eD=eP[189];
h.useLayoutEffect(() => {
  if (editingMarkdown && focusMarkdownEditor.current) {
    focusMarkdownEditor.current = false;
    tu.current?.focus({preventScroll: true});
  }
}, [editingMarkdown]);
const availableMarkdown = enableMarkdownPreview && previewMarkdown != null
  && tw.loadState === "loaded" && tW == null && !tw.isSelectionEditPending && eJ == null;
const readingMarkdown = availableMarkdown && !editingMarkdown;
h.useLayoutEffect(() => {
  markdownPreviewActive.current = readingMarkdown;
}, [readingMarkdown]);
if (enableMarkdownPreview) {
  ek = i.jsxs(i.Fragment, {children: [
    i.jsx("div", {
      className: "absolute inset-0",
      inert: readingMarkdown,
      style: readingMarkdown ? {visibility: "hidden"} : undefined,
      children: ek,
    }, "editor"),
    readingMarkdown ? i.jsx(WorkspaceMarkdownPreview, {
      markdown: previewMarkdown,
      cwd: markdownFileDirectory(tM),
      hostId: eG,
      initialScrollTop: eQ,
      onScroll: tB,
      editLabel: tr.formatMessage({id: "workspaceMarkdown.preview.edit", defaultMessage: "Edit Markdown"}),
      onEdit: tw.isReadOnly ? undefined : () => {
        focusMarkdownEditor.current = true;
        setEditingMarkdown(true);
      },
    }, "reader") : null,
    availableMarkdown && editingMarkdown ? i.jsx("div", {
      className: "absolute right-12 top-2",
      children: i.jsx(WorkspaceMarkdownButton, {
        onClick: () => setEditingMarkdown(false),
        children: tr.formatMessage({id: "markdownFileEditor.mode.viewPreview", defaultMessage: "View preview"}),
      }),
    }, "view-preview") : null,
  ]});
  if (readingMarkdown) eR = null;
}
eP[190]!==eb''',
        ),
    ]
    for anchor, replacement in edits:
        source = replace_once(source, anchor, replacement)
    return source.encode("utf-8")


def integrity(content):
    return {
        "algorithm": "SHA256",
        "hash": sha256(content).hexdigest(),
        "blockSize": BLOCK_SIZE,
        "blocks": [
            sha256(content[start:start + BLOCK_SIZE]).hexdigest()
            for start in range(0, len(content), BLOCK_SIZE)
        ],
    }


def packed_entry(data, offset):
    return {"size": len(data), "offset": str(offset), "integrity": integrity(data)}


def json_bytes(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def pack_header(header):
    data = json_bytes(header)
    padding = bytes((-len(data)) % 4)
    header_length = len(data) + len(padding)
    return struct.pack("<4I", 4, header_length + 8, header_length + 4, len(data)) + data + padding


def lookup(header, path):
    for part in path.split("/"):
        header = header["files"][part]
    return header


def packed_files(header):
    for entry in header.get("files", {}).values():
        if "files" in entry:
            yield from packed_files(entry)
        elif "offset" in entry:
            yield entry


def read_bytes(file, offset, length):
    file.seek(offset)
    content = file.read(length)
    if len(content) != length:
        raise ValueError("Unexpected end of ASAR archive.")
    return content


@contextmanager
def inspect(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as file:
        original_stat = os.fstat(file.fileno())
        if not stat.S_ISREG(original_stat.st_mode):
            raise ValueError("Expected a regular ASAR archive.")
        word, header_size, payload_size, json_size = struct.unpack("<4I", file.read(16))
        payload_offset = header_size + 8
        payload_length = original_stat.st_size - payload_offset
        if word != 4 or not 8 <= header_size <= 16_777_216 or payload_size != header_size - 4:
            raise ValueError("Unsupported ASAR header.")
        raw_header = read_bytes(file, 0, payload_offset)
        header = json.loads(raw_header[16:16 + json_size])
        if pack_header(header) != raw_header:
            raise ValueError("Unsupported ASAR header representation.")
        manifest = lookup(header, "package.json")
        meta = json.loads(read_bytes(file, payload_offset + int(manifest["offset"]), manifest["size"]))
        if meta["name"] != "openai-codex-electron" or meta["version"] != VERSION:
            raise ValueError(f"Unsupported build. Expected Codex {VERSION}.")
        entry = lookup(header, ASSET)
        offset = int(entry["offset"])
        original = read_bytes(file, payload_offset + STOCK_OFFSET, STOCK_SIZE)
        if sha256(original).hexdigest() != STOCK_HASH:
            raise ValueError("The original Markdown editor asset failed verification.")
        stock = packed_entry(original, STOCK_OFFSET)
        patched = patch_source(original)
        applied = entry != stock
        expected = packed_entry(patched, offset) if applied else stock
        if entry != expected or offset < 0 or offset + entry["size"] > payload_length:
            raise ValueError("Unknown Markdown editor asset or integrity metadata.")
        content = read_bytes(file, payload_offset + offset, entry["size"])
        if content != (patched if applied else original):
            raise ValueError("Markdown editor asset does not match its expected content.")
        last_other_byte = 0
        for other in packed_files(header):
            if other is entry:
                continue
            start = int(other["offset"])
            end = start + other["size"]
            if start < 0 or end > payload_length or (
                start < STOCK_OFFSET + STOCK_SIZE and end > STOCK_OFFSET
            ):
                raise ValueError("Archive asset overlaps the original Markdown editor.")
            last_other_byte = max(last_other_byte, end)
        if applied and offset < max(last_other_byte, STOCK_OFFSET + STOCK_SIZE):
            raise ValueError("Patched asset is not beyond the original archive assets.")
        yield file, original_stat, header, payload_offset, payload_length, offset, stock, patched, applied


def fingerprint(info):
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def update(path, apply):
    with inspect(path) as target:
        source, info, header, start, length, offset, stock, patched, applied = target
        if apply == applied:
            return False
        if apply:
            subprocess.run(["node", "--check", "--input-type=module"], input=patched, check=True)

        new_header = deepcopy(header)
        entry = lookup(new_header, ASSET)
        entry.clear()
        entry.update(packed_entry(patched, length) if apply else stock)
        keep = length
        if not apply and offset + len(patched) == length:
            keep = offset
        temporary = None
        try:
            fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
            with os.fdopen(fd, "wb") as candidate:
                candidate.write(pack_header(new_header))
                source.seek(start)
                remaining = keep
                while remaining:
                    chunk = source.read(min(4_194_304, remaining))
                    if not chunk:
                        raise ValueError("Archive changed during the copy.")
                    candidate.write(chunk)
                    remaining -= len(chunk)
                if apply:
                    candidate.write(patched)
                candidate_info = os.fstat(candidate.fileno())
                if (candidate_info.st_uid, candidate_info.st_gid) != (info.st_uid, info.st_gid):
                    os.fchown(candidate.fileno(), info.st_uid, info.st_gid)
                os.fchmod(candidate.fileno(), stat.S_IMODE(info.st_mode))
                candidate.flush()
                os.fsync(candidate.fileno())
            with inspect(temporary) as candidate:
                if candidate[-1] != apply:
                    raise ValueError("Candidate verification failed.")
            if fingerprint(path.lstat()) != fingerprint(info):
                raise ValueError("The installed app changed before replacement.")
            os.replace(temporary, path)
            temporary = None
            directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            if temporary is not None:
                os.unlink(temporary)
    with inspect(path) as installed:
        if installed[-1] != apply:
            raise ValueError("Installed archive verification failed.")
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--apply", action="store_true")
    actions.add_argument("--restore", action="store_true")
    actions.add_argument("--check", action="store_true")
    parser.add_argument("--app-asar", type=Path, default=ARCHIVE)
    args = parser.parse_args()
    try:
        if args.apply or args.restore:
            changed = update(args.app_asar, args.apply)
            print("Archive updated." if changed else "Archive already in the requested state.")
        with inspect(args.app_asar) as target:
            print(f"Codex {VERSION}: Markdown preview patch {'applied' if target[-1] else 'absent'}.")
    except (OSError, KeyError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
