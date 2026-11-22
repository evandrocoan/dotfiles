#!/usr/bin/env python3
"""Deliver Netdata disk-space alarms and smartd NVMe warnings to the desktop."""

import argparse
from contextlib import closing
from http.client import HTTPConnection, HTTPException
import html
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time


MOUNTS = ('/', '/home', '/myfiles')
SEVERITIES = {'WARNING': 'normal', 'CRITICAL': 'critical'}
MAX_RESPONSE = 2 * 1024 * 1024
REMINDER_SECONDS = 3600
SMART_LOOKBACK_SECONDS = 24 * 3600
SMART_CURSOR = 'smart_cursor'
NVME_MESSAGE = re.compile(r'^Device: /dev/nvme[0-9]+(?:n[0-9]+)?[, ]')


def read_alarms():
    with closing(HTTPConnection('127.0.0.1', 19999, timeout=3)) as connection:
        connection.request('GET', '/api/v1/alarms?all')
        with connection.getresponse() as response:
            if response.status != 200:
                raise ValueError(f'Netdata alarm request returned HTTP {response.status}')
            raw = response.read(MAX_RESPONSE + 1)
    if len(raw) > MAX_RESPONSE:
        raise ValueError('Netdata alarm response exceeds the size limit')
    document = json.loads(raw)
    if (not isinstance(document, dict) or document.get('status') is not True
            or not isinstance(document.get('alarms'), dict)):
        raise ValueError('Netdata alarm state is unavailable')
    return document['alarms']


def smart_events(output):
    for line in output.splitlines():
        event = json.loads(line)
        if (not isinstance(event, dict) or not isinstance(event.get('MESSAGE'), str)
                or not isinstance(event.get('__CURSOR'), str) or not event['__CURSOR']):
            raise ValueError('invalid smartd journal entry')
        if (event.get('_UID') == '0' and event.get('_SYSTEMD_UNIT') == 'smartmontools.service'
                and event.get('SYSLOG_IDENTIFIER') == 'smartd'
                and event.get('PRIORITY') in ('0', '1', '2')):
            yield event


def read_smart(cursor, now):
    position = ('--after-cursor=' + cursor if isinstance(cursor, str) and cursor
                else '--since=@' + str(max(0, now - SMART_LOOKBACK_SECONDS)))
    response = subprocess.run(['/usr/bin/journalctl', '--quiet', '--no-pager', '--output=json',
        '--output-fields=MESSAGE,PRIORITY,_SYSTEMD_UNIT,SYSLOG_IDENTIFIER,_UID', '--priority=crit',
        position, '_SYSTEMD_UNIT=smartmontools.service', 'SYSLOG_IDENTIFIER=smartd', '_UID=0'],
        capture_output=True, text=True, timeout=5)
    if response.returncode:
        raise ValueError(f'journalctl exited with status {response.returncode}: {response.stderr.strip()[:500]}')
    return list(smart_events(response.stdout))


def send_desktop(app, urgency, title, body):
    subprocess.run(['/usr/bin/notify-send', '--app-name=' + app,
                    '--urgency=' + urgency, '--icon=drive-harddisk',
                    '--expire-time=30000', '--', title, html.escape(body)],
                   check=True, timeout=5)


def notify_disk(mount, status, percent):
    level = 'critically low space' if status == 'CRITICAL' else 'low space'
    send_desktop('Netdata', SEVERITIES[status], f'Netdata: {level} on {mount}',
                 f'{mount} is {percent:.1f}% used. Open the local Netdata dashboard for details.')


def notify_smart(body):
    send_desktop('SMART', 'critical', 'SMART: NVMe SSD health warning', body)


def save_state(path, state):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, prefix='.disk-', delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(state, stream)
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def check_disk(state, alarms, now, sender):
    sent, statuses, unavailable, failures = [], {}, [], []
    for mount in MOUNTS:
        chart = f'disk_space.{mount}'
        alarm = alarms.get(f'{chart}.disk_space_usage')
        if not isinstance(alarm, dict) or alarm.get('chart') != chart:
            unavailable.append(mount)
            continue
        status, percent = alarm.get('status'), alarm.get('value')
        if (status not in ('CLEAR', *SEVERITIES) or type(percent) not in (int, float)
                or not math.isfinite(percent) or not 0 <= percent <= 100):
            unavailable.append(mount)
            continue
        statuses[mount] = status
        if status == 'CLEAR':
            state.pop(mount, None)
            continue
        last = state.get(mount)
        if (isinstance(last, dict) and last.get('status') == status
                and last.get('transition') == alarm.get('last_status_change')
                and type(last.get('sent_at')) is int and 0 <= now - last['sent_at'] < REMINDER_SECONDS):
            continue
        try:
            sender(mount, status, percent)
        except (OSError, subprocess.SubprocessError) as error:
            print(f'Netdata disk alert delivery failed for {mount}: {error}', file=sys.stderr)
            failures.append(mount)
        else:
            state[mount] = {'status': status, 'transition': alarm.get('last_status_change'), 'sent_at': now}
            sent.append(mount)
    return {'alarms': statuses, 'sent': sent, 'unavailable': unavailable, 'delivery_failures': failures}


def check_smart(state, events, sender):
    if not events:
        return 0
    messages = [event['MESSAGE'] for event in events if NVME_MESSAGE.match(event['MESSAGE'])]
    if messages:
        # One bounded popup per check even if the journal accumulated several events.
        summary = '\n'.join(dict.fromkeys(message[:360] for message in messages[-3:]))
        sender(summary)
    state[SMART_CURSOR] = events[-1]['__CURSOR']
    return len(messages)


def check(path, now, *, disk_source=read_alarms, smart_source=read_smart,
          disk_sender=notify_disk, smart_sender=notify_smart):
    try:
        previous = json.loads(path.read_text())
        if not isinstance(previous, dict):
            raise ValueError('invalid storage alert state')
    except FileNotFoundError:
        previous = {}
    except (OSError, ValueError) as error:
        print(f'Storage alert could not read reminder state: {error}', file=sys.stderr)
        previous = {}

    state = previous.copy()
    result = {'alarms': {}, 'sent': [], 'unavailable': [], 'delivery_failures': [],
              'smart_warnings': 0, 'errors': {}}
    try:
        result.update(check_disk(state, disk_source(), now, disk_sender))
    except (OSError, HTTPException, ValueError) as error:
        result['errors']['netdata'] = str(error)
    try:
        result['smart_warnings'] = check_smart(state, smart_source(state.get(SMART_CURSOR), now),
                                              smart_sender)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        result['errors']['smart'] = str(error)
    if state != previous:
        try:
            save_state(path, state)
        except OSError as error:
            result['errors']['state'] = str(error)
    for source, error in result['errors'].items():
        print(f'Storage alert {source}: {error}', file=sys.stderr)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('state', type=Path, help='path to the desktop reminder state')
    args = parser.parse_args()
    result = check(args.state, int(time.time()))
    print(json.dumps(result))
    return int(bool(result['unavailable'] or result['delivery_failures'] or result['errors']))


if __name__ == '__main__':
    raise SystemExit(main())
