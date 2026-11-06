"""Real Unix sockets exercise private inode pinning, peer checks and generation cleanup."""
import json
import os
from pathlib import Path
import runpy
import socket
import subprocess
import sys
import threading
import tempfile

import pytest


CLI = Path(os.environ.get('CODEX_MONITOR_TEST_CLI',
    Path(__file__).resolve().parents[2] / '.local/bin/codex-session-stats'))


def listener(path, label):
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(path))
    server.listen(5)
    def serve():
        while True:
            try:
                connection, _ = server.accept()
            except OSError:
                return
            with connection:
                if connection.recv(1):
                    connection.sendall(label)
    threading.Thread(target=serve, daemon=True).start()
    return server


def request(path):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(2)
        client.connect(str(path))
        client.sendall(b'?')
        return client.recv(20)


@pytest.fixture
def binding(tmp_path):
    module = runpy.run_path(str(CLI))['monitor_launcher']()
    with tempfile.TemporaryDirectory(prefix='cmt-') as name:
        directory = Path(name)
        gui = module['monitor_process'](os.getpid())
        yield module, directory, gui


def test_private_socket_keeps_original_host_after_public_name_replacement(binding, tmp_path):
    m, directory, gui = binding
    public = tmp_path / 'public.sock'
    first = listener(public, b'original')
    replacement = None
    try:
        receipt = m['monitor_app_tools_bind'](directory, public, gui, gui, 'first')
        assert request(directory / 'host.sock') == b'original'
        public.unlink()
        replacement = listener(public, b'replacement')
        assert request(public) == b'replacement'
        assert request(directory / 'host.sock') == b'original'
        assert [ (directory/'host.sock').stat().st_dev,
                 (directory/'host.sock').stat().st_ino ] == receipt['socket_identity']
        assert m['monitor_app_tools_unbind'](directory, receipt) is True
        assert not (directory/'host.sock').exists()
        assert request(public) == b'replacement'
    finally:
        first.close()
        if replacement is not None:
            replacement.close()


def test_old_cleanup_cannot_remove_new_generation(binding, tmp_path):
    m, directory, gui = binding
    first_path, next_path = tmp_path/'one.sock', tmp_path/'two.sock'
    first, second = listener(first_path, b'one'), listener(next_path, b'two')
    try:
        old = m['monitor_app_tools_bind'](directory, first_path, gui, gui, 'old')
        new = m['monitor_app_tools_bind'](directory, next_path, gui, gui, 'new')
        assert m['monitor_app_tools_unbind'](directory, old) is False
        assert request(directory/'host.sock') == b'two'
        assert json.loads((directory/'binding.json').read_text()) == new
        assert m['monitor_app_tools_unbind'](directory, new) is True
    finally:
        first.close();second.close()


def test_same_gui_rebind_requires_old_relay_termination(binding, tmp_path):
    m, directory, gui = binding
    first_path, next_path = tmp_path/'old.sock', tmp_path/'new.sock'
    first, second = listener(first_path, b'old'), listener(next_path, b'new')
    child = subprocess.Popen(['/bin/sleep', '30'])
    try:
        proxy = m['monitor_process'](child.pid)
        old = m['monitor_app_tools_bind'](directory, first_path, gui, proxy, 'old-relay')
        with pytest.raises(RuntimeError, match='proxy is still live'):
            m['monitor_app_tools_bind'](directory, next_path, gui, gui, 'new-relay')
        assert json.loads((directory/'binding.json').read_text()) == old
        assert request(directory/'host.sock') == b'old'
        child.terminate(); child.wait(timeout=5)
        new = m['monitor_app_tools_bind'](directory, next_path, gui, gui, 'new-relay')
        assert m['monitor_app_tools_unbind'](directory, old) is False
        assert json.loads((directory/'binding.json').read_text()) == new
        assert request(directory/'host.sock') == b'new'
        assert m['monitor_app_tools_unbind'](directory, new) is True
    finally:
        if child.poll() is None:
            child.terminate(); child.wait(timeout=5)
        first.close(); second.close()


def test_wrong_peer_is_not_published(binding, tmp_path):
    m, directory, proxy = binding
    public = tmp_path/'other.sock'
    server = listener(public, b'wrong')
    child = subprocess.Popen(['/bin/sleep','20'])
    try:
        gui = m['monitor_process'](child.pid)
        with pytest.raises(RuntimeError, match='peer is not the selected GUI'):
            m['monitor_app_tools_bind'](directory, public, gui, proxy, 'wrong')
        assert not (directory/'host.sock').exists()
        assert not (directory/'binding.json').exists()
        assert list(directory.glob('pending-*')) == []
    finally:
        child.terminate();child.wait(timeout=5);server.close()


def test_symbolic_source_is_rejected(binding, tmp_path):
    m, directory, gui = binding
    public = tmp_path/'real.sock'
    server = listener(public, b'real')
    alias = tmp_path/'alias.sock';alias.symlink_to(public)
    try:
        with pytest.raises(RuntimeError, match='owned same-filesystem Unix socket'):
            m['monitor_app_tools_bind'](directory, alias, gui, gui, 'alias')
        assert not (directory/'host.sock').exists()
        assert not (directory/'binding.json').exists()
    finally:
        server.close()


def test_abrupt_host_exit_cannot_redirect_private_socket_and_successor_rebinds(binding, tmp_path):
    m, directory, proxy = binding
    public = tmp_path/'abrupt.sock'
    code = '''import socket,sys
s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
s.bind(sys.argv[1]);s.listen(5)
print('ready',flush=True)
while True:
 c,_=s.accept()
 with c:
  if c.recv(1):c.sendall(b'first')
'''
    child = subprocess.Popen([sys.executable,'-u','-c',code,str(public)],
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    successor = None
    try:
        assert child.stdout.readline() == 'ready\n'
        gui = m['monitor_process'](child.pid)
        old = m['monitor_app_tools_bind'](directory,public,gui,proxy,'abrupt')
        assert request(directory/'host.sock') == b'first'
        child.kill();child.wait(timeout=5)
        public.unlink()
        successor = listener(public,b'successor')
        assert request(public) == b'successor'
        with pytest.raises(ConnectionRefusedError):
            request(directory/'host.sock')
        assert json.loads((directory/'binding.json').read_text()) == old
        new = m['monitor_app_tools_bind'](directory,public,proxy,proxy,'successor')
        assert new['socket_identity'] != old['socket_identity']
        assert m['monitor_app_tools_unbind'](directory,old) is False
        assert request(directory/'host.sock') == b'successor'
        assert m['monitor_app_tools_unbind'](directory,new) is True
    finally:
        if child.poll() is None:
            child.kill();child.wait(timeout=5)
        child.stdout.close();child.stderr.close()
        if successor is not None:successor.close()
