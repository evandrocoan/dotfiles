"""Repository-owned skill structure; repeated prose is advisory, never a verdict."""

from collections import defaultdict
from pathlib import Path
import re
import subprocess
import unicodedata
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt

from .common import Invalid, load_yaml, read_json


MARKDOWN = MarkdownIt("commonmark")


def owned_files(repo):
    output = subprocess.check_output([
        "git", "ls-files", "--cached", "--others", "--exclude-standard", "-z",
    ], cwd=repo)
    return sorted(set(p.decode() for p in output.split(b"\0") if p))


def local_packages(repo, files):
    packages = []
    for name in files:
        path = Path(name)
        if (len(path.parts) == 4 and path.parts[:2] == (".claude", "skills")
                and path.name == "SKILL.md" and path.parts[2] != "synced"):
            package = Path(repo) / path.parent
            if package.is_symlink() or not package.resolve().is_relative_to(Path(repo).resolve()):
                continue
            packages.append(path.parent.as_posix())
    if not packages:
        raise Invalid("No repository-owned skill entrypoints; inventory scope is invalid")
    return packages


def frontmatter(text):
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
    if not match:
        raise Invalid("Missing YAML frontmatter")
    metadata = load_yaml(match[1])
    if not isinstance(metadata, dict):
        raise Invalid("Frontmatter must be a mapping")
    name, description = metadata.get("name"), metadata.get("description")
    if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64:
        raise Invalid("Invalid or empty skill name")
    if not isinstance(description, str) or not description.strip() or len(description) > 1024:
        raise Invalid("Invalid or empty skill description")
    return metadata, text[match.end():]


def prose(token):
    return "".join(t.content for t in (token.children or [])
                   if t.type in {"text", "code_inline", "image"})


def anchors(tokens):
    """Supported GFM-style slug dialect: Unicode letters/numbers/marks, _ and -."""
    used = set()
    for index, token in enumerate(tokens):
        if token.type == "heading_open":
            text = prose(tokens[index + 1]).lower()
            base = "".join(c for c in text if c in "_-" or c.isspace()
                           or unicodedata.category(c)[0] in "LNM").replace(" ", "-")
            slug, suffix = base, 0
            while slug in used:
                suffix += 1
                slug = f"{base}-{suffix}"
            used.add(slug)
        if token.type in {"html_block", "inline"}:
            used.update(re.findall(r'<a\s+(?:id|name)=["\']([^"\']+)["\']', token.content))
    return used


def markdown_body(path):
    text = path.read_text()
    return frontmatter(text)[1] if path.name == "SKILL.md" else text


def check_repository(repo):
    repo = Path(repo).resolve()
    files = owned_files(repo)
    file_set = set(files)
    packages = local_packages(repo, files)
    result = {"packages": packages, "errors": [], "advisories": [], "boundaries": []}
    blocks = defaultdict(list)

    def error(path, message):
        result["errors"].append({"path": path, "message": message})

    for package in packages:
        name = Path(package).name
        alias = repo / ".agents/skills" / name
        expected = f"../../.claude/skills/{name}"
        if not alias.is_symlink() or alias.readlink().as_posix() != expected:
            error(f".agents/skills/{name}", "Missing or incorrect relative shared alias")
        excluded = set()
        manifest = repo / package / "upstream-manifest.json"
        if manifest.exists():
            data = read_json(manifest)
            excluded.update(item["destination"] for item in data["files"].values())
        for relative in files:
            if not relative.startswith(package + "/"):
                continue
            within = relative[len(package) + 1:]
            if within in excluded or not relative.endswith(".md") or within.startswith("assets/"):
                continue
            path = repo / relative
            if path.is_symlink() or not path.resolve().is_relative_to(repo / package):
                error(relative, "Owned Markdown must stay inside its package")
                continue
            try:
                body = markdown_body(path)
                if path.name == "SKILL.md" and frontmatter(path.read_text())[0]["name"] != name:
                    raise Invalid("Entrypoint name differs from package name")
                tokens = MARKDOWN.parse(body)
                for index, token in enumerate(tokens):
                    if token.type != "inline":
                        continue
                    if index and tokens[index - 1].type == "paragraph_open":
                        normalized = " ".join(prose(token).split())
                        if len(normalized) >= 120:
                            blocks[normalized].append(relative)
                    for child in token.children or []:
                        if child.type not in {"link_open", "image"}:
                            continue
                        href = child.attrGet("href" if child.type == "link_open" else "src") or ""
                        parsed = urlsplit(href)
                        if parsed.scheme or parsed.netloc:
                            continue  # External links are not fetched or certified.
                        target = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
                        if not target.is_relative_to(repo):
                            result["boundaries"].append({"path": relative, "link": href, "kind": "outside repository"})
                            continue
                        target_relative = target.relative_to(repo).as_posix()
                        if target_relative not in file_set and not any(x.startswith(target_relative + "/") for x in files):
                            error(relative, f"Target is absent from owned inventory: {href}")
                            continue
                        if not target.exists():
                            error(relative, f"Missing link target: {href}")
                        elif parsed.fragment and target.suffix == ".md":
                            if unquote(parsed.fragment) not in anchors(MARKDOWN.parse(markdown_body(target))):
                                error(relative, f"Missing heading/anchor: {href}")
            except (Invalid, OSError, UnicodeError) as exc:
                error(relative, str(exc))
    for text, locations in sorted(blocks.items()):
        if len(set(locations)) > 1:
            result["advisories"].append({"kind": "repeated prose", "paths": sorted(set(locations)), "text": text})
    return result
