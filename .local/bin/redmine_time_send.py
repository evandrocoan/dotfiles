#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import sys
import json
import argparse
import requests

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


def parse_time_line(state, line):
    line = line.strip()
    if not line:
        state.first_date = ""
        state.last_date = ""

    match = state.regex.search(line)

    if match:
        state.first_date = match.group('date')

        if not state.last_date:
            state.last_date = state.first_date

        if state.first_date != state.last_date: raise RuntimeError("Each line group must be from the same date")
        state.last_date = state.first_date

        hours = match.group('hours')
        issue_id = match.group('issue_id')
        activity_id = match.group('activity_id')
        comment = match.group('comment')

        if not state.first_date: raise RuntimeError(f"Invalid data first_date {state.first_date}")
        if not hours: raise RuntimeError(f"Invalid data hours {hours}")
        if not issue_id: raise RuntimeError(f"Invalid data issue_id {issue_id}")
        if not activity_id or int(activity_id) not in (8, 9, 15): raise RuntimeError(f"Invalid data activity_id {activity_id}")

        entry = {
            "issue_id": int(issue_id),
            "hours": float(hours),
            "spent_on": state.first_date.replace('/', '-'),
            "activity_id": activity_id,
        }
        if comment: entry['comments'] = comment
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

    last_date = ""
    for data in state.entries:
        if last_date and last_date != data['spent_on']: print()
        last_date = data['spent_on']
        print(data)

    input("Press enter to send data...")
    for data in state.entries:
        data_json = json.dumps({ "time_entry": data })
        response = requests.post(f'{url}/time_entries.json', headers=headers, data=data_json)

        if response.status_code in (200, 201):
            print("Response was successful.", repr(response.text))
        else:
            print("Response was not successful:", response.status_code, repr(response.text))
            break


def test_basic_load():
    lines = """
1. Add 1.0 hours/8 (2023/04/12) #81448 inhere cradle unhoed increpate u
1. Add 1.0 hours/8 (2023/04/12) #80661 fishlike sc
1. Add 5.0 hours/8 (2023/04/12) #89081 roughet overintellectual bureaucratization s

1. Add 5.0 hours/8 (2023/04/15) #89081 deciduously the

1. Add 1.0 hours/8 (2023/04/16) #81352 bifocal somers repr
1. Add 1.0 hours/8 (2023/04/16) #81236 assaying pneumotherapy perceptibleness
1. Add 5.0 hours/8 (2023/04/16) #89081 salmonif
    """

    state = State()
    for line in lines.split('\n'):
        parse_time_line(state, line)


def test_mixed_data_raise_runtime_error():
    lines = """
1. Add 1.0 hours/8 (2023/04/12) #81448 jugated envision crackhemp
1. Add 1.0 hours/8 (2023/04/12) #80661 grasslike Monomya
1. Add 5.0 hours/8 (2023/04/12) #89081 unavailing fasciculus cursorary sca

1. Add 5.0 hours/8 (2023/04/15) #89081 abranchious Kokoona unprincipledness poluphloisboiotic ideolo

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

