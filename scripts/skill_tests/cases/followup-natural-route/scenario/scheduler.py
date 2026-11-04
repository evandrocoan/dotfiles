"""Expose a captured scheduler tool and record attempts without external effects."""

import argparse
import json
from pathlib import Path
import sys
import time


def serve(descriptor, receipt):
    tool = json.loads(descriptor.read_text())
    states = {}
    for line in sys.stdin:
        request = json.loads(line)
        if 'id' not in request:
            continue
        method = request['method']
        if method == 'initialize':
            result = {
                'protocolVersion': request['params']['protocolVersion'],
                'capabilities': {'tools': {}},
                'serverInfo': {'name': 'local-scheduler-fixture', 'version': '1'},
            }
        elif method == 'tools/list':
            receipt.with_name(receipt.stem + '-catalog.json').write_text(json.dumps(tool))
            result = {'tools': [tool]}
        elif method == 'tools/call':
            call = request['params']
            with receipt.open('a', encoding='utf-8') as stream:
                print(json.dumps({'time': time.time(), **call}), file=stream, flush=True)
            if call['name'] != tool['name']:
                result = {'content': [{'type': 'text', 'text': 'Unknown fixture tool'}],
                          'isError': True}
            else:
                arguments = call.get('arguments', {})
                identity = arguments.get('id', 'fixture-heartbeat')
                if arguments.get('mode') == 'delete':
                    states.pop(identity, None)
                    value = {'id': identity, 'deleted': True}
                elif arguments.get('mode') == 'view':
                    value = states.get(identity, {'id': identity, 'status': 'ABSENT'})
                else:
                    value = {'id': identity, **arguments}
                    states[identity] = value
                result = {'content': [{'type': 'text', 'text': json.dumps(value)}]}
        elif method == 'ping':
            result = {}
        else:
            print(json.dumps({'jsonrpc': '2.0', 'id': request['id'],
                              'error': {'code': -32601, 'message': 'Unknown method'}}),
                  flush=True)
            continue
        print(json.dumps({'jsonrpc': '2.0', 'id': request['id'], 'result': result}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--descriptor', required=True, type=Path)
    parser.add_argument('--receipt', required=True, type=Path)
    args = parser.parse_args()
    serve(args.descriptor, args.receipt)
