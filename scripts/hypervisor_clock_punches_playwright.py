#!/usr/bin/env python3

import subprocess
import re
import sys
from datetime import datetime, timedelta


def send_notification(title, message):
    print(title, message)
    try:
        # Execute the notify-send command with specified title and message
        subprocess.run(['/usr/bin/notify-send', title, message], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to send notification: {e}")


def get_last_10_lines(service_name, time_range_to_search):
    try:
        # Get last 10 log lines for the specified service
        cmd = ['/usr/bin/journalctl', '--user', '-u', service_name, "--since", f"{time_range_to_search} minutes ago", '-n', '10', '--no-pager']
        process = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return process.stdout.splitlines()
    except subprocess.CalledProcessError as e:
        send_notification("hypervisor_clock_punches_playwright", f"Error fetching logs: {e}")
        return []


def extract_and_check_log_entry(log_lines, time_range_to_search):
    # Regex pattern to match the log entry with 'Found x clock punches.'
    log_pattern = re.compile(r'(\w{3} \d{2} \d{2}:\d{2}:\d{2}) .+ Found (\d+) clock punches\.')

    now = datetime.now()
    fifteen_minutes_ago = now - timedelta(minutes=time_range_to_search)

    for line in log_lines:
        match = log_pattern.search(line)
        if match:
            timestamp_str = match.group(1)
            clock_punches = int(match.group(2))
            log_timestamp = datetime.strptime(timestamp_str, '%b %d %H:%M:%S')

            # Replace year with the current year as journalctl might not provide it
            log_timestamp = log_timestamp.replace(year=now.year)

            # print(f"Matched log entry: {line}")
            print(f"Extracted timestamp: {log_timestamp}, Clock Punches: {clock_punches}")

            if fifteen_minutes_ago <= log_timestamp <= now:
                print(f"The log entry is within the last {time_range_to_search} minutes.")
                break
    else:
        send_notification("hypervisor_clock_punches_playwright", "The log entry is NOT found within the last 15 minutes.")


def should_run_function():
    # Get current date and time
    now = datetime.now()

    # Check if it is not Sunday (weekday() returns 6 for Sunday)
    if now.weekday() != 6:
        # Check if the current time is between 07:00 and 22:00
        if 7 <= now.hour < 22:
            return True
        else:
            print("Current time is outside the permitted hours (07:00-22:00).")
    else:
        print("Today is Sunday, the function will not run.")


if __name__ == "__main__":
    service_name = "check_clock_punches_playwright"
    try:
        if should_run_function():
            time_range_to_search = 15
            log_lines = get_last_10_lines(service_name, time_range_to_search)
            extract_and_check_log_entry(log_lines, time_range_to_search)
    except:
        send_notification("hypervisor_clock_punches_playwright", f"Failed checking service: {service_name}")
        sys.exit(1)
