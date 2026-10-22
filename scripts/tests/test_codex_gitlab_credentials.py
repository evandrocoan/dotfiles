"""The monitor reads one origin-bound credential from either MCP transport."""
import io
import json
import os
from pathlib import Path
import runpy
import urllib.request
import urllib.response
from email.message import Message

import pytest


CLI = Path(os.environ.get("CODEX_MONITOR_TEST_CLI", Path(__file__).resolve().parents[2] / ".local/bin/codex-session-stats"))
ORIGIN = "https://gitlab.example.test"
TOKEN = "fixture-private-token"


@pytest.fixture
def reader(tmp_path):
    module = runpy.run_path(str(CLI))
    config = {"codex_home": str(tmp_path), "credential_mcp_server": "gitlab",
              "gitlab_url": ORIGIN, "http_timeout": 2, "max_response_bytes": 1024}

    def write(server):
        lines = ["[mcp_servers.gitlab]"]
        for key, value in server.items():
            if not isinstance(value, dict):
                lines.append(f"{json.dumps(key)} = {json.dumps(value)}")
        for key, values in server.items():
            if isinstance(values, dict):
                lines.append(f"[mcp_servers.gitlab.{key}]")
                lines.extend(f"{json.dumps(k)} = {json.dumps(v)}" for k, v in values.items())
        lines.extend(['[mcp_servers.unrelated.env]', 'GITLAB_PERSONAL_ACCESS_TOKEN = "other-secret"'])
        target = tmp_path / "config.toml"
        target.write_text("\n".join(lines) + "\n")
        target.chmod(0o600)

    return module, config, write


def http_server():
    return {"url": "http://127.0.0.1:3002/mcp", "http_headers": {
        "Private-Token": TOKEN, "X-Gitlab-Api-Url": ORIGIN + "/api/v4"}}


@pytest.mark.parametrize("endpoint", [ORIGIN, ORIGIN + "/api/v4", ORIGIN + "/api/v4/"])
@pytest.mark.parametrize("transport", ["http", "stdio"])
def test_resolves_exact_token_and_origin(reader, endpoint, transport):
    module, config, write = reader
    server = http_server() if transport == "http" else {"command": "docker", "env": {
        "GITLAB_PERSONAL_ACCESS_TOKEN": TOKEN, "GITLAB_API_URL": endpoint}}
    if transport == "http":
        server["http_headers"]["X-Gitlab-Api-Url"] = endpoint
    write(server)
    assert module["monitor_credential"](config) == (ORIGIN + "/api/v4", TOKEN)


@pytest.mark.parametrize("token", ["", " ", 7, True, ["token"], "bad\nsecret", "bad\rsecret", "bad\tsecret", "bad\x7fsecret"])
@pytest.mark.parametrize("transport", ["http", "stdio"])
def test_rejects_invalid_tokens_before_network(reader, monkeypatch, capsys, token, transport):
    module, config, write = reader
    server = http_server() if transport == "http" else {"command": "docker", "env": {
        "GITLAB_PERSONAL_ACCESS_TOKEN": TOKEN, "GITLAB_API_URL": ORIGIN}}
    server["http_headers" if transport == "http" else "env"][
        "Private-Token" if transport == "http" else "GITLAB_PERSONAL_ACCESS_TOKEN"] = token
    write(server)
    calls = []
    monkeypatch.setattr(urllib.request, "build_opener", lambda *args: calls.append(args))
    with pytest.raises(RuntimeError, match="selected MCP credential") as error:
        module["MonitorGitLab"](config)
    assert calls == []
    assert "secret" not in str(error.value)
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize("endpoint", ["", "http://gitlab.example.test", "https://other.test",
    ORIGIN + "/projects", ORIGIN + "?token=secret", ORIGIN + "#secret",
    "https://user:secret@gitlab.example.test", 3, "https://[invalid", ORIGIN + "\n"])
def test_rejects_invalid_origin(reader, endpoint):
    module, config, write = reader
    server = http_server()
    server["http_headers"]["X-Gitlab-Api-Url"] = endpoint
    write(server)
    with pytest.raises(RuntimeError, match="selected MCP credential"):
        module["monitor_credential"](config)


@pytest.mark.parametrize("url", ["", 3, "file:///mcp", "http:///mcp", "http://[invalid",
    "http://127.0.0.1:not-a-port/mcp", "http://127.0.0.1:99999/mcp", "http://@localhost/mcp",
    "http://user:password@localhost/mcp", "http://bad host/mcp"])
def test_rejects_malformed_http_transport(reader, url):
    module, config, write = reader
    server = http_server()
    server["url"] = url
    write(server)
    with pytest.raises(RuntimeError, match="selected MCP credential"):
        module["monitor_credential"](config)


@pytest.mark.parametrize("extra", [
    {"command": "docker"}, {"args": []},
    {"env": {"GITLAB_PERSONAL_ACCESS_TOKEN": TOKEN, "GITLAB_API_URL": ORIGIN}},
    {"env_vars": ["GITLAB_PERSONAL_ACCESS_TOKEN"]},
    {"env_http_headers": {"Private-Token": "AMBIENT_TOKEN"}},
    {"http_headers_helper": {"command": "must-never-run"}},
    {"bearer_token_env_var": "AMBIENT_TOKEN"},
])
def test_http_rejects_competing_sources(reader, extra):
    module, config, write = reader
    write(http_server() | extra)
    with pytest.raises(RuntimeError, match="selected MCP credential"):
        module["monitor_credential"](config)


@pytest.mark.parametrize("extra", [
    {"private-token": "second-token"}, {"x-gitlab-api-url": ORIGIN},
    {"Authorization": "Bearer second-token"}, {"JOB-TOKEN": "second-token"},
])
def test_http_rejects_duplicate_or_competing_headers(reader, extra):
    module, config, write = reader
    server = http_server()
    server["http_headers"].update(extra)
    write(server)
    with pytest.raises(RuntimeError, match="selected MCP credential"):
        module["monitor_credential"](config)


@pytest.mark.parametrize("remove", ["Private-Token", "X-Gitlab-Api-Url"])
def test_missing_http_credential_never_uses_ambient_token(reader, monkeypatch, remove):
    module, config, write = reader
    server = http_server()
    del server["http_headers"][remove]
    write(server)
    monkeypatch.setenv("GITLAB_PERSONAL_ACCESS_TOKEN", TOKEN)
    with pytest.raises(RuntimeError, match="selected MCP credential"):
        module["monitor_credential"](config)


def test_header_matching_is_case_insensitive(reader):
    module, config, write = reader
    server = http_server()
    server["http_headers"] = {k.lower(): v for k, v in server["http_headers"].items()}
    write(server)
    assert module["monitor_credential"](config) == (ORIGIN + "/api/v4", TOKEN)


@pytest.mark.parametrize("status", [200, 302])
def test_real_client_routes_header_and_refuses_redirect(reader, monkeypatch, status):
    module, config, write = reader
    write(http_server())
    requests = []

    def external_response(handler, request):
        requests.append((request.full_url, request.get_header("Private-token")))
        headers = Message()
        headers["Content-Type"] = "application/json"
        if status == 302:
            headers["Location"] = "https://other.test/steal"
        response = urllib.response.addinfourl(io.BytesIO(b'{"id":42}'), headers, request.full_url, status)
        response.msg = "fixture response"
        return response

    monkeypatch.setattr(urllib.request.HTTPSHandler, "https_open", external_response)
    api = module["MonitorGitLab"](config)
    if status == 200:
        assert api.get("/user") == {"id": 42}
    else:
        with pytest.raises(RuntimeError, match="HTTP 302.*no redirect followed"):
            api.get("/user")
    assert requests == [(ORIGIN + "/api/v4/user", TOKEN)]
