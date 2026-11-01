"""Wire ordering and GUI readiness are separate observations of the relay."""
import asyncio
import json
import os
from pathlib import Path
import runpy

import pytest


CLI = Path(os.environ.get('CODEX_MONITOR_TEST_CLI',
    Path(__file__).resolve().parents[2] / '.local/bin/codex-session-stats'))


class Native:
    def __init__(self, *, challenge=False, error=False, fail_ack=False):
        self.incoming = asyncio.Queue()
        self.frames = []
        self.initialized = False
        self.challenge, self.error, self.fail_ack = challenge, error, fail_ack
        self.rpc_seen = asyncio.Event()

    async def send(self, raw):
        message = json.loads(raw)
        method = message.get('method')
        if method == 'initialized' and self.fail_ack:
            raise OSError('fixture notification write failed')
        self.frames.append(message)
        if method == 'initialize':
            self.initialize = message
            if self.challenge:
                await self.incoming.put({'id': message['id'], 'method': 'attestation/generate',
                                         'params': {'challenge': 'fixture'}})
            else:
                await self.finish_initialize()
        elif method == 'initialized':
            assert not self.initialized, 'duplicate notification reached native peer'
            self.initialized = True
        elif method is None and self.challenge:
            assert message == {'id': self.initialize['id'], 'result': {'fixture': 'reply'}}
            await self.finish_initialize()
        else:
            assert self.initialized, 'ordinary RPC reached native before initialized'
            self.rpc_seen.set()
            await self.incoming.put({'id': message['id'], 'result':
                message['params'] if method == 'echo' else {'native': 'success'}})

    async def finish_initialize(self):
        response = {'id': self.initialize['id']}
        response.update({'error': {'code': -1}} if self.error else {'result': {'fixture': True}})
        await self.incoming.put(response)

    def __aiter__(self):
        return self

    async def __anext__(self):
        return json.dumps(await self.incoming.get())


class GuiOutput:
    def __init__(self, *, hold_initial_drain=False):
        self.frames = asyncio.Queue()
        self.initial_drain = asyncio.Event()
        if not hold_initial_drain:
            self.initial_drain.set()
        self.is_initialize = False

    def write(self, raw):
        message = json.loads(raw)
        self.is_initialize = message.get('id') == 'gui-init' and 'method' not in message
        self.frames.put_nowait(message)

    async def drain(self):
        if self.is_initialize:
            await self.initial_drain.wait()

    async def receive(self):
        return await asyncio.wait_for(self.frames.get(), 3)


class Session:
    def __init__(self, *, native=None, output=None, revoke=False):
        self.native = native or Native()
        self.output = output or GuiOutput()
        self.reader = asyncio.StreamReader(limit=64 * 1024 * 1024 + 1)
        self.ready = []
        self.verifications = 0
        self.revoke = revoke
        relay = runpy.run_path(str(CLI))['monitor_launcher']()['monitor_relay_protocol']
        self.task = asyncio.create_task(relay(self.native, self.reader, self.output,
            verify=self.verify, on_ready=self.ready.append, timeout=3))

    def verify(self):
        self.verifications += 1
        if self.revoke and self.verifications > 1:
            raise RuntimeError('fixture identity revoked')

    def send(self, message):
        self.reader.feed_data((json.dumps(message) + '\n').encode())

    async def initialize(self):
        self.send({'id': 'gui-init', 'method': 'initialize', 'params': {
            'clientInfo': {'name': 'real-gui-fixture', 'version': '1'},
            'capabilities': {'requestAttestation': True, 'experimentalApi': True}}})
        return await self.output.receive()

    async def close(self):
        self.reader.feed_eof()
        return await asyncio.wait_for(self.task, 3)


def test_response_only_gui_never_publishes_readiness():
    async def scenario():
        s = Session()
        assert (await s.initialize())['result'] == {'fixture': True}
        assert s.native.initialized
        with pytest.raises(RuntimeError, match='before readiness'):
            await s.close()
        assert s.ready == []
    asyncio.run(scenario())


@pytest.mark.parametrize('gui_ack', [False, True])
def test_gui_round_trip_and_one_native_notification(gui_ack):
    async def scenario():
        s = Session()
        await s.initialize()
        if gui_ack:
            s.send({'method': 'initialized', 'params': {}})
        s.send({'id': 'gui-rpc', 'method': 'config/read', 'params': {}})
        assert await s.output.receive() == {'id': 'gui-rpc', 'result': {'native': 'success'}}
        await s.close()
        assert s.ready == [{'native_ack_owner': 'relay', 'gui_rpc_id': 'gui-rpc'}]
        assert [f.get('method') for f in s.native.frames] == [
            'initialize', 'initialized', 'config/read']
        assert s.native.frames[0]['params']['capabilities'] == {
            'requestAttestation': True, 'experimentalApi': True}
    asyncio.run(scenario())


def test_gui_rpc_is_admitted_while_initial_response_drain_is_pending():
    async def scenario():
        s = Session(output=GuiOutput(hold_initial_drain=True))
        await s.initialize()  # Bytes are readable even though drain has not returned.
        s.send({'id': 'gui-rpc', 'method': 'config/read', 'params': {}})
        await asyncio.wait_for(s.native.rpc_seen.wait(), 3)
        assert s.native.initialized and s.ready == []
        s.output.initial_drain.set()
        assert (await s.output.receive())['id'] == 'gui-rpc'
        await s.close()
        assert len(s.ready) == 1
    asyncio.run(scenario())


def test_server_request_during_initialization_with_overlapping_directional_id():
    async def scenario():
        s = Session(native=Native(challenge=True))
        assert (await s.initialize())['method'] == 'attestation/generate'
        s.send({'id': 'gui-init', 'result': {'fixture': 'reply'}})
        assert (await s.output.receive())['result'] == {'fixture': True}
        s.send({'id': 'gui-rpc', 'method': 'config/read', 'params': {}})
        await s.output.receive()
        await s.close()
        assert [f.get('method') for f in s.native.frames] == [
            'initialize', None, 'initialized', 'config/read']
        assert len(s.ready) == 1
    asyncio.run(scenario())


@pytest.mark.parametrize('failure', ['native-error', 'ack-write', 'revoked-identity'])
def test_failed_startup_has_no_gui_readiness(failure):
    async def scenario():
        s = Session(native=Native(error=failure == 'native-error', fail_ack=failure == 'ack-write'),
                    revoke=failure == 'revoked-identity')
        s.send({'id': 'gui-init', 'method': 'initialize', 'params': {}})
        if failure == 'revoked-identity':
            await s.output.receive()
            s.send({'id': 'gui-rpc', 'method': 'config/read', 'params': {}})
        with pytest.raises((RuntimeError, OSError)):
            await asyncio.wait_for(s.task, 3)
        assert s.ready == []
        if failure != 'revoked-identity':
            assert not s.native.initialized
    asyncio.run(scenario())


def test_premature_gui_notification_cannot_complete_native_handshake():
    async def scenario():
        s = Session()
        s.send({'method': 'initialized', 'params': {}})
        with pytest.raises(RuntimeError, match='premature'):
            await asyncio.wait_for(s.task, 3)
        assert s.native.frames == [] and s.ready == []
    asyncio.run(scenario())


def test_large_message_round_trip_keeps_the_gui_result():
    async def scenario():
        s = Session()
        await s.initialize()
        content = 'x' * (9 * 1024 * 1024)
        s.send({'id': 'large', 'method': 'echo', 'params': {'content': content}})
        assert await s.output.receive() == {'id': 'large', 'result': {'content': content}}
        assert s.native.frames[-1]['params']['content'] == content
        await s.close()
        assert len(s.ready) == 1
    asyncio.run(scenario())


def test_oversize_message_is_rejected_before_native_send(monkeypatch):
    async def scenario():
        s = Session()
        await s.initialize()
        # Session uses its own module instance; obtain the active coroutine's globals.
        namespace = s.task.get_coro().cr_frame.f_globals
        assert namespace['MONITOR_RELAY_LIMIT'] == 64 * 1024 * 1024
        monkeypatch.setitem(namespace, 'MONITOR_RELAY_LIMIT', 1024)
        s.send({'id': 'large', 'method': 'echo', 'params': {'content': 'x' * 2048}})
        with pytest.raises(RuntimeError, match='exceeds 64 MiB'):
            await asyncio.wait_for(s.task, 3)
        assert [item.get('method') for item in s.native.frames] == ['initialize', 'initialized']
        assert s.ready == []
    asyncio.run(scenario())
