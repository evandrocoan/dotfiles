#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import sys
import json
import datetime
import argparse
import requests
import pprint

try:
    import pytest
except:
    pytest = None


def get_day_of_the_week(entry) -> str:
    spent_on_str = entry['spent_on']
    spent_on_date = datetime.datetime.strptime(spent_on_str, "%Y-%m-%d")
    day_of_week = spent_on_date.strftime("%A")
    return day_of_week


class State(object):
    regex = re.compile(r"Add\s+(?P<hours>[\d.]+)\s+hours/(?P<activity_id>[\d.]+)\s+\((?P<date>\d{4}/\d{2}/\d{2})\)\s+#(?P<issue_id>[^\s]+)")

    def __init__(self):
        self.entries = []
        self.first_date = ""
        self.last_date = ""
        self.total_time = 0
        self.line_count = 0
        self.actual_date = datetime.datetime.strptime("1990/01/02", "%Y/%m/%d")
        self.last_block_date = datetime.datetime.strptime("1990/01/01", "%Y/%m/%d")
        self.warnings = []
        self.errors = []

    def __str__(self):
        return f"entries {self.entries}, first_date {self.first_date}, last_date {self.last_date}, total_time {self.total_time}, actual_date {self.actual_date}, last_block_date {self.last_block_date}, warnings {self.warnings}, errors {self.errors}."

    def __repr__(self):
        return str(self)


def parse_time_line(state, line):
    line = line.strip()
    if not line:
        state.last_block_date = state.actual_date
        state.first_date = ""
        state.last_date = ""
        if state.entries:
            day = get_day_of_the_week(state.entries[-1])
            if day == 'Sunday' and state.total_time:
                state.warnings.append(f"on {day:10} Invalid total time {state.total_time}, Line {state.line_count}: {state.entries[-1]}.")
            elif day == 'Saturday' and state.total_time > 10:
                state.warnings.append(f"on {day:10} Invalid total time {state.total_time}, Line {state.line_count}: {state.entries[-1]}.")
            elif day not in ('Saturday', 'Sunday') and (state.total_time and state.total_time < 6 or state.total_time > 10):
                state.warnings.append(f"on {day:10} Invalid total time {state.total_time}, Line {state.line_count}: {state.entries[-1]}.")
        state.total_time = 0

    state.line_count += 1
    match = state.regex.search(line)

    if match:
        state.first_date = match.group('date')

        if not state.last_date:
            state.last_date = state.first_date

        if state.first_date != state.last_date:
            state.errors.append(f"Each line group must be from the same date! Line {state.line_count}: {line}.")
            return
        state.last_date = state.first_date

        hours = match.group('hours')
        issue_id = match.group('issue_id')
        activity_id = match.group('activity_id')

        remaining = line[match.end('issue_id'):]
        note_marker = re.search(r'\(:', remaining)
        if note_marker:
            try:
                raw = extract_outermost_parenthesis_content(state, remaining[note_marker.start():])
            except RuntimeError as e:
                state.errors.append(str(e))
                return
            comment = raw[1:].strip()
            before_note = remaining[:note_marker.start()].strip()
            depth = 0
            end_pos = len(remaining)
            for i, c in enumerate(remaining[note_marker.start():]):
                if c == '(':
                    depth += 1
                elif c == ')':
                    depth -= 1
                    if depth == 0:
                        end_pos = note_marker.start() + i + 1
                        break
            after_note = remaining[end_pos:].strip()
            title = ' '.join(filter(None, [before_note, after_note]))
        else:
            comment = ''
            title = remaining.strip()

        try:
            issue_id_int = int(issue_id)
        except ValueError:
            state.errors.append(f"Invalid data issue_id {issue_id!r}, Line {state.line_count}: {line}.")
            return

        try:
            if int(activity_id) not in (8, 9, 15):
                raise ValueError
        except ValueError:
            state.errors.append(f"Invalid data activity_id {activity_id}, Line {state.line_count}: {line}.")
            return

        entry = {
            "issue_id": issue_id_int,
            "hours": float(hours),
            "spent_on": state.first_date.replace('/', '-'),
            "activity_id": activity_id,
        }
        if comment and len(comment) > 1000:
            state.warnings.append(f"on {get_day_of_the_week(entry):10} Line {state.line_count}: Comment {len(comment)} is too big for entry {entry}!")

        if comment: entry['comments'] = comment[:1000]
        if title: entry['title'] = title

        next_date = datetime.datetime.strptime(state.first_date, "%Y/%m/%d")

        if state.actual_date > next_date:
            state.errors.append(f"Invalid date {state.actual_date}, should always be >= Line {state.line_count}: {line}.")
            return
        state.actual_date = next_date

        if datetime.datetime.strptime(state.first_date, "%Y/%m/%d") <= state.last_block_date:
            state.errors.append(f"The next block must be from higher date! Line {state.line_count}! Line {state.line_count}: {line}.")
            return

        state.total_time += float(hours)
        state.entries.append(entry)

    elif line:
        state.errors.append(f"Line with invalid data! Line {state.line_count}: {line}.")


def verify_titles(entries, url, headers):
    mismatches = []
    issue_cache = {}
    seen = set()

    for entry in entries:
        issue_id = entry['issue_id']
        local_title = entry.get('title', '')
        if not local_title:
            continue

        if issue_id not in issue_cache:
            response = requests.get(f'{url}/issues/{issue_id}.json', headers=headers)
            if response.status_code == 200:
                issue_cache[issue_id] = response.json()['issue']['subject']
            else:
                issue_cache[issue_id] = None

        remote_subject = issue_cache[issue_id]
        key = (issue_id, local_title.strip())
        if key in seen:
            continue
        seen.add(key)

        if remote_subject is None:
            mismatches.append((issue_id, local_title, f'<erro ao consultar #{issue_id}>'))
        elif local_title.strip() != remote_subject.strip():
            mismatches.append((issue_id, local_title, remote_subject))

    return mismatches


def main():
    state = State()
    arguments = g_argumentParser.parse_args()

    with open(arguments.file) as file:
        for line in file:
            parse_time_line(state, line)

    # flush current day for warnings check
    parse_time_line(state, '')

    with open( os.path.expanduser('~/Documents/redmine_api_key.json') ) as file:
        data = json.load(file)

    url = data['url']  # "https://redmine.com"
    api_key = data['key']  # "jsebfyjsebfyjsebfyjsebfyjsebfyebfyjsebfy"

    headers = {
        'Content-Type': 'application/json',
        'X-Redmine-API-Key': api_key,
    }

    total = 0
    last_date = ""

    for data in state.entries + [{
        "issue_id": 0,
        "hours": 0,
        "spent_on": None,
        "activity_id": "",
    }]:
        if last_date and last_date != data['spent_on'] or data['hours'] == 0:
            day = datetime.datetime.strptime(last_date, "%Y-%m-%d").strftime("%A")
            print(f'total {total} ({day})')
            print()
            total = 0
        if data['hours'] == 0:
            break
        last_date = data['spent_on']
        total += data['hours']
        print(data)

    if state.warnings:
        for warning in state.warnings:
            print("warning", warning, '\n')

    title_mismatches = verify_titles(state.entries, url, headers)
    if title_mismatches:
        print("\nTítulos divergentes:")
        for issue_id, local, remote in title_mismatches:
            print(f"  #{issue_id} - {local}")
            print(f"  #{issue_id} + {remote}")
            print()

    if state.errors:
        print("\nErros de parse:")
        for error in state.errors:
            print(f"  {error}")
        print("\nEnvio abortado.")
        return

    if arguments.dry_run:
        print("\nDry run — nenhum dado enviado.")
        return

    input("Press enter to send data...")
    input("Press enter to send data...")
    input("Press enter to send data...")
    errors = []
    for data in state.entries:
        payload = {k: v for k, v in data.items() if k != 'title'}
        data_json = json.dumps({ "time_entry": payload })
        response = requests.post(f'{url}/time_entries.json', headers=headers, data=data_json)

        if response.status_code in (200, 201):
            print("Response was successful.", repr(response.text))
        else:
            print("Response was not successful:", response.status_code, repr(response.text), data_json)
            errors.append((payload, response.status_code, response.text))

    if errors:
        print("\n\nWARNING\n\nThe following requests resulted in errors:")
        pprint.pprint(errors)

    else:
        print("\nSuccessfully sent all requests.")


def test_basic_load():
    lines = """
1. Add 1.0 hours/8 (2023/04/12) #81448 inhere cradle unhoed increpate u
1. Add 1.0 hours/8 (2023/04/12) #80661 fishlike sc
1. Add 5.0 hours/8 (2023/04/12) #89081 roughet overintellectual bureaucratization s

1. Add 6.0 hours/8 (2023/04/15) #89081 deciduously the

1. Add 1.0 hours/8 (2023/04/16) #81352 bifocal somers repr
1. Add 1.0 hours/8 (2023/04/16) #81236 assaying pneumotherapy perceptibleness
1. Add 5.0 hours/8 (2023/04/16) #89081 salmonif
    """

    state = State()
    for line in lines.split('\n'):
        parse_time_line(state, line)


def extract_outermost_parenthesis_content(state, input_data):
    stack = []
    result = []
    has_parentheses = False
    for i, char in enumerate(input_data):
        if char == '(':
            has_parentheses = True
            stack.append(i)
        elif char == ')':
            has_parentheses = True
            if not stack:
                raise RuntimeError(f"Unbalanced parentheses on input! Line {state.line_count}: {input_data}.")
            start = stack.pop()
            if not stack:
                result.append(input_data[start + 1: i])
    if has_parentheses and not result:
        raise RuntimeError(f"Unbalanced parentheses on input! Line {state.line_count}: {input_data}.")
    return " ".join(result)


def test_comment_with_parentheses_1():
    state = State()
    parse_time_line(state,
        "1. Add 1.0 hours/8 (2023/04/12) #80661 fusilier Octocorallia reprovingly Rickettsiales m (:some comment with (parentheses) inside)"
    )
    assert state.entries[0]['comments'] == "some comment with (parentheses) inside"


def test_comment_with_parentheses_2():
    state = State()
    parse_time_line(state,
        "1. Add 1.0 hours/8 (2023/04/12) #80661 fusilier Octocorallia reprovingly Rickettsiales m (:some comment with (parentheses inside)"
    )
    assert not state.entries
    assert any("Unbalanced parentheses on input" in e for e in state.errors)


def test_comment_with_parentheses_3():
    state = State()
    parse_time_line(state,
        "1. Add 1.0 hours/8 (2023/04/12) #80661 fusilier Octocorallia reprovingly Rickettsiales m (:some comment with parentheses) inside)"
    )
    assert not state.entries
    assert any("Unbalanced parentheses on input" in e for e in state.errors)


def test_comment_before_title():
    state = State()
    parse_time_line(state,
        "1. Add 1.0 hours/8 (2023/04/12) #80661 (:some note) fusilier Octocorallia reprovingly"
    )
    assert state.entries[0]['comments'] == "some note"
    assert state.entries[0]['title'] == "fusilier Octocorallia reprovingly"


def test_mixed_data_raise_runtime_error():
    lines = """
1. Add 1.0 hours/8 (2023/04/12) #81448 jugated envision crackhemp
1. Add 1.0 hours/8 (2023/04/12) #80661 grasslike Monomya
1. Add 5.0 hours/8 (2023/04/12) #89081 unavailing fasciculus cursorary sca

1. Add 6.0 hours/8 (2023/04/15) #89081 abranchious Kokoona unprincipledness poluphloisboiotic ideolo

1. Add 1.0 hours/8 (2023/04/16) #81352 Guttera enfila
1. Add 1.0 hours/8 (2023/04/15) #81236 Welf overbearing yeomanwis
1. Add 5.0 hours/8 (2023/04/16) #89081 thumb
    """

    state = State()
    for line in lines.split('\n'):
        parse_time_line(state, line)
    assert any("Each line group must be from the same date" in e for e in state.errors)


def test_invalid_issue_id_raises_runtime_error():
    lines = """
1. Add 1.0 hours/8 (2023/04/12) #81448 colostric uncultivate So
1. Add 1.0 hours/8 (2023/04/12) #80661 fusilier Octocorallia reprovingly Rickettsiales m
1. Add 5.0 hours/8 (2023/04/12) #89081 collectibility cartmaker dropsied le

1. Add 2.0 hours/8 (2023/04/15) #8xxxx Jacaltec sepi
1. Add 5.0 hours/8 (2023/04/15) #89081 foremasthand ungeniu

1. Add 1.0 hours/8 (2023/04/16) #81352 Serapis unwomanlike prominency ba
1. Add 1.0 hours/8 (2023/04/16) #81236 mesomorphy scandalizer u
1. Add 5.0 hours/8 (2023/04/16) #89081 emanatory radiolocator
    """

    state = State()
    for line in lines.split('\n'):
        parse_time_line(state, line)
    assert any("Invalid data issue_id" in e for e in state.errors)


def test_invalid_line_parse_raises_runtime_error():
    lines = """
1. Add 1.0 hours/8 (2023/04/12) #81448 colostric uncultivate So
1. Add 1.0 hours/8 (2023/04/12) #80661 fusilier Octocorallia reprovingly Rickettsiales m
1. Add 5.0 hours/8 (2023/04/12) #89081 collectibility cartmaker dropsied le

1. Add 2.0 hours8 (2023/04/15) #8xxxx Jacaltec sepi
1. Add 5.0 hours/8 (2023/04/15) #89081 foremasthand ungeniu

1. Add 1.0 hours/8 (2023/04/16) #81352 Serapis unwomanlike prominency ba
1. Add 1.0 hours/8 (2023/04/16) #81236 mesomorphy scandalizer u
1. Add 5.0 hours/8 (2023/04/16) #89081 emanatory radiolocator
    """

    state = State()
    for line in lines.split('\n'):
        parse_time_line(state, line)
    assert any("Line with invalid data" in e for e in state.errors)


def test_invalid_date_raises_runtime_error():
    lines = """
1. Add 1.0 hours/8 (2023/04/12) #81448 colostric uncultivate So
1. Add 1.0 hours/8 (2023/04/12) #80661 fusilier Octocorallia reprovingly Rickettsiales m
1. Add 5.0 hours/8 (2023/04/12) #89081 collectibility cartmaker dropsied le

1. Add 2.0 hours/8 (2023/04/15) #89081 Jacaltec sepi
1. Add 5.0 hours/8 (2023/04/15) #89081 foremasthand ungeniu

1. Add 1.0 hours/8 (2023/04/14) #81352 Serapis unwomanlike prominency ba
1. Add 1.0 hours/8 (2023/04/14) #81236 mesomorphy scandalizer u
1. Add 5.0 hours/8 (2023/04/14) #89081 emanatory radiolocator
    """

    state = State()
    for line in lines.split('\n'):
        parse_time_line(state, line)
    assert any("Invalid date 2023-04-15 00:00:00, should always be >=" in e for e in state.errors)


def test_same_date_different_blocks_raises_runtime_error():
    lines = """
1. Add 1.0 hours/8 (2023/04/12) #81448 colostric uncultivate So
1. Add 1.0 hours/8 (2023/04/12) #80661 fusilier Octocorallia reprovingly Rickettsiales m
1. Add 5.0 hours/8 (2023/04/12) #89081 collectibility cartmaker dropsied le

1. Add 2.0 hours/8 (2023/04/15) #89081 Jacaltec sepi
1. Add 5.0 hours/8 (2023/04/15) #89081 foremasthand ungeniu

1. Add 1.0 hours/8 (2023/04/15) #81352 Serapis unwomanlike prominency ba
1. Add 1.0 hours/8 (2023/04/15) #81236 mesomorphy scandalizer u
1. Add 5.0 hours/8 (2023/04/15) #89081 emanatory radiolocator
    """

    state = State()
    for line in lines.split('\n'):
        parse_time_line(state, line)
    assert any("The next block must be from higher date" in e for e in state.errors)


def test_too_much_hours_raises_runtime_error():
    lines = """
1. Add 1.0 hours/8 (2023/04/12) #81448 colostric uncultivate So
1. Add 1.0 hours/8 (2023/04/12) #80661 fusilier Octocorallia reprovingly Rickettsiales m
1. Add 5.0 hours/8 (2023/04/12) #89081 collectibility cartmaker dropsied le

1. Add 2.0 hours/8 (2023/04/14) #89081 Jacaltec sepi
1. Add 5.0 hours/8 (2023/04/14) #89081 foremasthand ungeniu

1. Add 5.0 hours/8 (2023/04/17) #81352 Serapis unwomanlike prominency ba
1. Add 1.0 hours/8 (2023/04/17) #81236 mesomorphy scandalizer u
1. Add 5.0 hours/8 (2023/04/17) #89081 emanatory radiolocator
    """

    state = State()
    for line in lines.split('\n'):
        parse_time_line(state, line)

    assert "Invalid total time 11.0" in str(state.warnings)


def test_too_less_hours_raises_runtime_error():
    lines = """
1. Add 1.0 hours/8 (2023/04/12) #81448 colostric uncultivate So
1. Add 1.0 hours/8 (2023/04/12) #80661 fusilier Octocorallia reprovingly Rickettsiales m
1. Add 5.0 hours/8 (2023/04/12) #89081 collectibility cartmaker dropsied le

1. Add 5.0 hours/8 (2023/04/14) #89081 foremasthand ungeniu

1. Add 5.0 hours/8 (2023/04/17) #81352 Serapis unwomanlike prominency ba
1. Add 1.0 hours/8 (2023/04/17) #81236 mesomorphy scandalizer u
1. Add 5.0 hours/8 (2023/04/17) #89081 emanatory radiolocator
    """

    state = State()
    for line in lines.split('\n'):
        parse_time_line(state, line)

    assert "Invalid total time 5.0" in str(state.warnings)


def test_saturday_allows_less_than_6h():
    # 2023/04/15 is a Saturday — no minimum applies
    lines = """
1. Add 3.0 hours/8 (2023/04/15) #89081 some saturday work
    """
    state = State()
    for line in lines.split('\n'):
        parse_time_line(state, line)
    assert not state.warnings


def test_saturday_warns_above_10h():
    # 2023/04/15 is a Saturday — maximum of 10h still applies
    lines = """
1. Add 6.0 hours/8 (2023/04/15) #89081 some saturday work
1. Add 5.0 hours/8 (2023/04/15) #81448 more saturday work
    """
    state = State()
    for line in lines.split('\n'):
        parse_time_line(state, line)
    assert "Invalid total time 11.0" in str(state.warnings)


def test_sunday_warns_any_hours():
    # 2023/04/16 is a Sunday — any logged hours generate a warning
    lines = """
1. Add 2.0 hours/8 (2023/04/16) #89081 should not work on sunday
    """
    state = State()
    for line in lines.split('\n'):
        parse_time_line(state, line)
    assert "Invalid total time 2.0" in str(state.warnings)


g_argumentParser = argparse.ArgumentParser(
        description = \
"""
Single test and main file example.
Run your code and your tests with a single file.
""",
        formatter_class=argparse.RawTextHelpFormatter,
    )

g_argumentParser.add_argument( "--dry-run", action="store_true", default=False,
        help="Roda todas as validações sem enviar dados ao Redmine." )

g_argumentParser.add_argument( "-f", "--file", action="store", default="test.txt",
        help=
"""
File to open and parse contents to send to redmine time api.
<select name="activity_id">
<option value="8">Development</option>
<option value="9">Testing</option>
<option value="15">Merge</option></select>
# File format:
1. Add 5.0 hours/8 (2023/04/12) #89081 (:nota opcional) collectibility cartmaker dropsied le

1. Add 2.0 hours/8 (2023/04/15) #8xxxx Jacaltec sepi
1. Add 5.0 hours/8 (2023/04/15) #89081 foremasthand ungeniu

1. Add 1.0 hours/8 (2023/04/16) #81352 Serapis unwomanlike prominency ba
""" )


if __name__ == "__main__":
    main()

