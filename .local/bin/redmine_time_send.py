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


class State(object):
    regex = re.compile(r"Add\s+(?P<hours>[\d.]+)\s+hours/(?P<activity_id>[\d.]+)\s+\((?P<date>\d{4}/\d{2}/\d{2})\)\s+#(?P<issue_id>[^\s]+)(\s+\((?P<comment>[^)]+)\))?")

    def __init__(self):
        self.entries = []
        self.first_date = ""
        self.last_date = ""
        self.total_time = 0
        self.actual_date = datetime.datetime.strptime("1990/01/02", "%Y/%m/%d")
        self.last_block_date = datetime.datetime.strptime("1990/01/01", "%Y/%m/%d")
        self.warnings = []

    def __str__(self):
        return f"entries {self.entries}, first_date {self.first_date}, last_date {self.last_date}, total_time {self.total_time}, actual_date {self.actual_date}, last_block_date {self.last_block_date}, warnings {self.warnings}."

    def __repr__(self):
        return str(self)


def parse_time_line(state, line):
    line = line.strip()
    if not line:
        state.last_block_date = state.actual_date
        state.first_date = ""
        state.last_date = ""
        if state.total_time and state.total_time < 6 or state.total_time > 10:
            state.warnings.append(f"Invalid total time {state.total_time}, {state.entries[-1]}.")
        state.total_time = 0

    match = state.regex.search(line)

    if match:
        state.first_date = match.group('date')

        if not state.last_date:
            state.last_date = state.first_date

        if state.first_date != state.last_date: raise RuntimeError(f"Each line group must be from the same date {line}.")
        state.last_date = state.first_date

        hours = match.group('hours')
        issue_id = match.group('issue_id')
        activity_id = match.group('activity_id')
        comment = match.group('comment')
        state.total_time += float(hours)

        if comment:
            begin = match.start('comment')
            remaining = line[begin-1:]
            comment = extract_outermost_parenthesis_content(remaining)

        if not state.first_date: raise RuntimeError(f"Invalid data first_date {state.first_date}, {line}.")
        if not hours: raise RuntimeError(f"Invalid data hours {hours}, {line}.")
        if not issue_id: raise RuntimeError(f"Invalid data issue_id {issue_id}, {line}.")
        if not activity_id or int(activity_id) not in (8, 9, 15): raise RuntimeError(f"Invalid data activity_id {activity_id}, {line}.")

        entry = {
            "issue_id": int(issue_id),
            "hours": float(hours),
            "spent_on": state.first_date.replace('/', '-'),
            "activity_id": activity_id,
        }
        if comment and len(comment) > 1000:
            state.warnings.append(f"Warning: Comment {len(comment)} is too big for entry {entry}!")

        if comment: entry['comments'] = comment[:1000]

        next_date = datetime.datetime.strptime(state.first_date, "%Y/%m/%d")

        if state.actual_date > next_date: raise RuntimeError(f"Invalid date {state.actual_date}, should always be >= {line}.")
        state.actual_date = next_date

        if datetime.datetime.strptime(state.first_date, "%Y/%m/%d") <= state.last_block_date:
            raise RuntimeError(f"The next block must be from higher date {line}.")

        state.entries.append(entry)

    elif line:
        raise RuntimeError(f"Line with invalid data {line}.")


def main():
    state = State()
    arguments = g_argumentParser.parse_args()

    with open(arguments.file) as file:
        for line in file:
            parse_time_line(state, line)

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
            print('total', total)
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

    input("Press enter to send data...")
    input("Press enter to send data...")
    input("Press enter to send data...")
    errors = []
    for data in state.entries:
        data_json = json.dumps({ "time_entry": data })
        response = requests.post(f'{url}/time_entries.json', headers=headers, data=data_json)

        if response.status_code in (200, 201):
            print("Response was successful.", repr(response.text))
        else:
            print("Response was not successful:", response.status_code, repr(response.text), data_json)
            errors.append((data, response.status_code, response.text))

    if errors:
        print("\n\nWARNING\n\nThe following requests resulted in errors:")
        pprint.pprint(example_list)

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


def extract_outermost_parenthesis_content(input_data):
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
                raise RuntimeError(f"Unbalanced parentheses on input: {input_data}.")
            start = stack.pop()
            if not stack:
                result.append(input_data[start + 1: i])
    if has_parentheses and not result:
        raise RuntimeError(f"Unbalanced parentheses on input: {input_data}.")
    return " ".join(result)


def test_comment_with_parentheses_1():
    state = State()
    parse_time_line(state,
        "1. Add 1.0 hours/8 (2023/04/12) #80661 (some comment with (parentheses) inside) fusilier Octocorallia reprovingly Rickettsiales m"
    )
    assert state.entries[0]['comments'] == "some comment with (parentheses) inside"


def test_comment_with_parentheses_2():
    state = State()
    with pytest.raises(RuntimeError, match="Unbalanced parentheses on input"):
        parse_time_line(state,
            "1. Add 1.0 hours/8 (2023/04/12) #80661 (some comment with (parentheses inside) fusilier Octocorallia reprovingly Rickettsiales m"
        )
        assert not state


def test_comment_with_parentheses_3():
    state = State()
    with pytest.raises(RuntimeError, match="Unbalanced parentheses on input"):
        parse_time_line(state,
            "1. Add 1.0 hours/8 (2023/04/12) #80661 (some comment with parentheses) inside) fusilier Octocorallia reprovingly Rickettsiales m"
        )
        assert not state


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
    with pytest.raises(RuntimeError, match="Each line group must be from the same date"):
        for line in lines.split('\n'):
            parse_time_line(state, line)


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
    with pytest.raises(ValueError, match=r"invalid literal for int\(\) with base 10:"):
        for line in lines.split('\n'):
            parse_time_line(state, line)


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
    with pytest.raises(RuntimeError, match=r"Line with invalid data"):
        for line in lines.split('\n'):
            parse_time_line(state, line)


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
    with pytest.raises(RuntimeError, match=r"Invalid date 2023-04-15 00:00:00, should always be >="):
        for line in lines.split('\n'):
            parse_time_line(state, line)


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
    with pytest.raises(RuntimeError, match=r"The next block must be from higher date"):
        for line in lines.split('\n'):
            parse_time_line(state, line)


def test_too_much_hours_raises_runtime_error():
    lines = """
1. Add 1.0 hours/8 (2023/04/12) #81448 colostric uncultivate So
1. Add 1.0 hours/8 (2023/04/12) #80661 fusilier Octocorallia reprovingly Rickettsiales m
1. Add 5.0 hours/8 (2023/04/12) #89081 collectibility cartmaker dropsied le

1. Add 2.0 hours/8 (2023/04/15) #89081 Jacaltec sepi
1. Add 5.0 hours/8 (2023/04/15) #89081 foremasthand ungeniu

1. Add 5.0 hours/8 (2023/04/16) #81352 Serapis unwomanlike prominency ba
1. Add 1.0 hours/8 (2023/04/16) #81236 mesomorphy scandalizer u
1. Add 5.0 hours/8 (2023/04/16) #89081 emanatory radiolocator
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

1. Add 5.0 hours/8 (2023/04/15) #89081 foremasthand ungeniu

1. Add 5.0 hours/8 (2023/04/16) #81352 Serapis unwomanlike prominency ba
1. Add 1.0 hours/8 (2023/04/16) #81236 mesomorphy scandalizer u
1. Add 5.0 hours/8 (2023/04/16) #89081 emanatory radiolocator
    """

    state = State()
    for line in lines.split('\n'):
        parse_time_line(state, line)

    assert "Invalid total time 5.0" in str(state.warnings)


g_argumentParser = argparse.ArgumentParser(
        description = \
"""
Single test and main file example.
Run your code and your tests with a single file.
""",
        formatter_class=argparse.RawTextHelpFormatter,
    )

g_argumentParser.add_argument( "-f", "--file", action="store", default="test.txt",
        help=
"""
File to open and parse contents to send to redmine time api.
<select name="activity_id">
<option value="8">Development</option>
<option value="9">Testing</option>
<option value="15">Merge</option></select>
# File format:
1. Add 5.0 hours/8 (2023/04/12) #89081 collectibility cartmaker dropsied le

1. Add 2.0 hours/8 (2023/04/15) #8xxxx Jacaltec sepi
1. Add 5.0 hours/8 (2023/04/15) #89081 foremasthand ungeniu

1. Add 1.0 hours/8 (2023/04/16) #81352 Serapis unwomanlike prominency ba
""" )


if __name__ == "__main__":
    main()

