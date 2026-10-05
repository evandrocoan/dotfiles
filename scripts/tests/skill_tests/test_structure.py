from pathlib import Path
import subprocess

import pytest

from skill_tests.common import Invalid, inventory, load_yaml, verify_inventory, write_new
from skill_tests.structure import MARKDOWN, anchors, check_repository, frontmatter


@pytest.fixture
def repository(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    package = tmp_path / ".claude/skills/example"
    package.mkdir(parents=True)
    (package / "SKILL.md").write_text("---\nname: example\ndescription: Useful example.\n---\n# Example\n")
    aliases = tmp_path / ".agents/skills"
    aliases.mkdir(parents=True)
    (aliases / "example").symlink_to("../../.claude/skills/example")
    return tmp_path, package


def test_valid_inventory_and_negative_scope_control(repository, tmp_path_factory):
    repo, _ = repository
    assert check_repository(repo)["errors"] == []
    empty = tmp_path_factory.mktemp("empty")
    subprocess.run(["git", "init", "-q", str(empty)], check=True)
    with pytest.raises(Invalid, match="No repository-owned"):
        check_repository(empty)


@pytest.mark.parametrize("text", ["name: a\nname: b", "value: [", "!!python/object:os.system {}"])
def test_yaml_rejects_invalid_or_unsafe_input(text):
    assert load_yaml("name: valid") == {"name": "valid"}
    with pytest.raises(Invalid):
        load_yaml(text)


@pytest.mark.parametrize("body", ["name: ''\ndescription: ok", "name: a\ndescription: []", "- value"])
def test_frontmatter_contract(body):
    with pytest.raises(Invalid):
        frontmatter(f"---\n{body}\n---\n# Body")


def test_links_parse_references_encoding_anchors_and_exclude_code(repository):
    repo, package = repository
    (package / "detail.md").write_text("# Café & `code`!\n# Same\n# Same\n")
    entry = package / "SKILL.md"
    entry.write_text(entry.read_text() + "\n[ref][x]\n\n[x]: detail.md#caf%C3%A9--code\n\n"
                     "[repeat](detail.md#same-1)\n\n```md\n[ignored](missing.md)\n```\n")
    assert check_repository(repo)["errors"] == []
    entry.write_text(entry.read_text() + "\n[bad](detail.md#absent)\n[missing](absent.md)\n")
    errors = check_repository(repo)["errors"]
    assert len(errors) == 2
    assert "Missing heading" in errors[0]["message"]
    assert "absent from owned inventory" in errors[1]["message"]


def test_heading_collision_and_html_anchor():
    assert anchors(MARKDOWN.parse('# A\n# A\n# A-1\n<a id="literal"></a>\n')) == {
        "a", "a-1", "a-1-1", "literal"}


def test_bad_alias_and_external_symlink_are_classified(repository, tmp_path_factory):
    repo, package = repository
    alias = repo / ".agents/skills/example"
    alias.unlink()
    alias.symlink_to("../../outside")
    external = tmp_path_factory.mktemp("external") / "secret.md"
    external.write_text("Private content must not be inspected")
    (package / "external.md").symlink_to(external)
    errors = check_repository(repo)["errors"]
    assert len(errors) == 2
    assert "relative shared alias" in errors[0]["message"]
    assert "inside its package" in errors[1]["message"]


def test_duplicate_prose_is_advisory_not_semantic_failure(repository):
    repo, package = repository
    repeated = "A repeated instruction requiring explicit evidence and preserving the real authorization boundary before any operation or model execution."
    (package / "a.md").write_text(repeated)
    (package / "b.md").write_text(repeated)
    (package / "c.md").write_text(f"```text\n{repeated}\n```\n")
    result = check_repository(repo)
    assert result["errors"] == []
    assert len(result["advisories"]) == 1
    assert result["advisories"][0]["paths"] == [
        ".claude/skills/example/a.md", ".claude/skills/example/b.md"]


def test_inventory_preserves_hidden_state_and_rejects_escape(tmp_path):
    (tmp_path / "visible").write_text("before")
    expected = inventory(tmp_path)
    verify_inventory(tmp_path, expected)
    (tmp_path / ".hidden").write_text("extra")
    with pytest.raises(Invalid, match="Inventory mismatch"):
        verify_inventory(tmp_path, expected)
    (tmp_path / "escape").symlink_to("../")
    with pytest.raises(Invalid, match="Escaping symlink"):
        inventory(tmp_path)


def test_evidence_is_exclusive(tmp_path):
    path = tmp_path / "evidence.json"
    write_new(path, {"first": True})
    original = path.read_bytes()
    with pytest.raises(FileExistsError):
        write_new(path, {"replaced": True})
    assert path.read_bytes() == original
