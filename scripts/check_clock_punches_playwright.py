#!/usr/bin/env python3

import asyncio
import os
import requests
import random
import http
import playwright
import subprocess

from datetime import datetime, time, timedelta

from playwright.async_api import async_playwright

from dotenv import load_dotenv
from loguru import logger

load_dotenv()
logger.level("TRACE")

TIME_BETWEEN_CHECKINGS = 600
VARIATION_BETWEEN_CHECKINGS = 200

AHGORA_USER_NAME = os.environ["AHGORA_USER_NAME"]
AHGORA_USER_PASSWORD = os.environ["AHGORA_USER_PASSWORD"]

# Your application's API token from Pushover (from application created).
PUSHOVER_API_TOKEN = os.environ["PUSHOVER_API_TOKEN"]  # https://pushover.net/

# Your Pushover user key (from Android device).
PUSHOVER_USER_NAME = os.environ["PUSHOVER_USER_NAME"]  # https://pushover.net/apps

"""
In case o error, the script check_clock_punches_playwright.py exits
and it is only restarted after 1 hours.
This leaves supervise_clock_punches_playwright.service to throw an notification
saying the script check_clock_punches_playwright.py exited,
therefore, allows you to check why the processes stop,
when it should never stop!

sudo apt-get install libnotify-bin
python3 -m pip install playwright loguru python-dotenv requests pytest
pytest -vs check_clock_punches_playwright.py

vim .env
```
AHGORA_USER_NAME=''
AHGORA_USER_PASSWORD=''
PUSHOVER_API_TOKEN=''
PUSHOVER_USER_NAME=''
```

cp -rv ./install/* ~/.config/
systemctl --user daemon-reload

systemctl --user enable check_clock_punches_playwright.service
systemctl --user enable supervise_clock_punches_playwright.service

systemctl --user start check_clock_punches_playwright.service
systemctl --user start supervise_clock_punches_playwright.service

journalctl --user -u check_clock_punches_playwright.service -f
journalctl --user -u supervise_clock_punches_playwright.service -f

"""


def send_pushover_notification(message, title="Notification", priority=0):
    """
    Sends a notification to an Android device using Pushover.

    :param message: The message to send.
    :param title: The title of the message. Optional.
    :param priority: Message priority. Optional.
    :return: Response from the Pushover API.
    """

    url = "https://api.pushover.net/1/messages.json"

    payload = {
        "token": PUSHOVER_API_TOKEN,
        "user": PUSHOVER_USER_NAME,
        "title": title,
        "message": message,
        "priority": priority,
    }
    response = requests.post(url, data=payload)
    logger.debug(f"Status Code: {response.status_code}, {response.text}.")
    return response


async def check_elements():

    async with async_playwright() as playcontext:

        browser = await playcontext.firefox.launch(headless=False, args=[
            '--check_clock_punches_playwright',
        ] )
        context = await browser.new_context(viewport={'width': 1900, 'height': 900})

        await context.grant_permissions(["notifications"], origin='https://app.ahgora.com.br')

        # Open a new page
        page = await context.new_page()
        # page = context.pages[0]

        page.set_default_timeout(30000)
        while True:
            try:
                # Navigate to your desired URL
                await page.goto('https://www.ahgora.com.br/externo/index/empresakhomp', wait_until='domcontentloaded')
                # await page.wait_for_load_state('networkidle')

                if "dashboard" not in page.url:
                    # click login button
                    button_selector = 'button[type="submit"].btn.btn-primary.pull-right'
                    await page.wait_for_selector(button_selector)

                    await page.locator('[name="matricula"]').nth(1).fill(AHGORA_USER_NAME)
                    await page.locator('[name="senha"]').fill(AHGORA_USER_PASSWORD)

                    await page.click(button_selector)
                    await page.wait_for_load_state('networkidle')

                mirror_selector = 'a[href="/externo/mirror"]'
                await page.wait_for_selector(mirror_selector)
                await page.click(mirror_selector)
                await page.wait_for_load_state('networkidle')

                iframe_handle = await page.wait_for_selector("#mirror")
                iframe = await iframe_handle.content_frame()

                know_more_selector = 'a[href="https://seusucesso.ahgora.com.br/kb/pt-br/article/82881"]'
                await iframe.wait_for_selector(know_more_selector)
                await iframe.wait_for_load_state('networkidle')

                # Select elements by class
                elements = await iframe.query_selector_all('.v-tooltip.batida.v-tooltip--top.original.exibirHora.exibirPrevista.exibirContratual')
                elementsCount = len(elements)
                logger.debug(f"Found {elementsCount} clock punches.")

                if elementsCount % 2 == 0:
                    # Trigger notification
                    await page.evaluate(r'''() => {
                        new Notification('Playwright Notification', {
                            body: `You are missing one clock punch! You have %s punches.`,
                            // icon: 'https://example.com/icon.png',  // Optionally use a URL to an icon image
                        });
                    }''' % elementsCount)

                if elementsCount % 2 == 1 and is_screen_locked():
                    current_time = datetime.now().time()
                    formatted_time = current_time.strftime("%H:%M")

                    texts = [await element.text_content() for element in elements]
                    message = f"You have {elementsCount} punches: {', '.join(texts)}"
                    response = send_pushover_notification(message, title=f"Missing punch {formatted_time}")

                    if response.status_code != http.HTTPStatus.OK:
                        logger.error(f"Failed to send notification: {response.text}")
                        # force the script to exit and restart so the error can be checked with
                        # journalctl --user -u check_clock_punches_playwright.service -f
                        raise RuntimeError(f"Failed to send notification: {response.text}")

            # except playwright._impl._errors.TargetClosedError:
            #     logger.exception(f"Exiting")
            #     break

            except Exception as e:
                # logger.debug(f"An error occurred: {type(e)} {e}")
                logger.exception(f"Exiting")
                break

            await wait_some_time()

            while not should_run_function():
                await wait_some_time()


def should_run_function():
    # Get current date and time
    now = datetime.now()

    # Check if it is not Sunday (weekday() returns 6 for Sunday)
    if now.weekday() != 6:
        # Check if the current time is between 07:00 and 22:00
        if 7 <= now.hour < 22:
            return True
        else:
            logger.debug("Current time is outside the permitted hours (07:00-22:00).")
    else:
        logger.debug("Today is Sunday, the function will not run.")


def is_screen_locked():
    result = subprocess.run(["xscreensaver-command", "-time"], capture_output=True, text=True, check=True)
    output = result.stdout.strip().lower()
    is_locked = "screen locked since" in output
    logger.debug(f"{is_locked}, {output}")
    return is_locked


async def wait_some_time():
    sleep_duration = random.randint(TIME_BETWEEN_CHECKINGS - VARIATION_BETWEEN_CHECKINGS, TIME_BETWEEN_CHECKINGS + VARIATION_BETWEEN_CHECKINGS)

    logger.debug(f"Waiting for {sleep_duration} seconds before the next check...")
    await asyncio.sleep(sleep_duration)


def test_notification_push():
    send_pushover_notification("Teste message", title="Missing clock punch")


if __name__ == "__main__":
    asyncio.run(check_elements())
