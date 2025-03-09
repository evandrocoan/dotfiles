#!/usr/bin/env python3

import asyncio
import os
import random
import playwright

from datetime import datetime, time, timedelta

from playwright.async_api import async_playwright

from dotenv import load_dotenv
from loguru import logger

load_dotenv()
logger.level("TRACE")

TIME_BETWEEN_CHECKINGS = 600
VARIATION_BETWEEN_CHECKINGS = 200

USER_NAME = os.environ["USER_NAME"]
USER_PASSWORD = os.environ["USER_PASSWORD"]

"""
In case o error, the script check_clock_punches_playwright.py exits
and it is only restarted after 1 hours.
This leaves supervise_clock_punches_playwright.service to throw an notification
saying the script check_clock_punches_playwright.py exited,
therefore, allows you to check why the processes stop,
when it should never stop!

sudo apt-get install libnotify-bin
python3 -m pip install playwright loguru python-dotenv

vim .env
```
USER_NAME=''
USER_PASSWORD=''
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

                    await page.locator('[name="matricula"]').nth(1).fill(USER_NAME)
                    await page.locator('[name="senha"]').fill(USER_PASSWORD)

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

            # except playwright._impl._errors.TargetClosedError:
            #     logger.exception(f"Exiting")
            #     break

            except Exception as e:
                # logger.debug(f"An error occurred: {type(e)} {e}")
                logger.exception(f"Exiting")
                break

            await ensure_time_after_7am()


async def ensure_time_after_7am():
    now = datetime.now()
    current_time = now.time()

    # Define the night time range
    night_start = time(22, 0)  # 22:00 or 10 PM
    morning_end = time(7, 0)   # 07:00 or 7 AM

    # Check if current time is during the night
    if current_time >= night_start or current_time < morning_end:
        # Calculate how much time until 07:00
        if current_time >= night_start:
            # It's currently between 22:00 and 23:59
            tomorrow_morning = (now + timedelta(days=1)).replace(hour=7, minute=0, second=0, microsecond=0)
        else:
            # It's currently between 00:00 and 06:59
            tomorrow_morning = now.replace(hour=7, minute=0, second=0, microsecond=0)

        sleep_duration = (tomorrow_morning - now).total_seconds()
        logger.debug(f"Sleeping for {sleep_duration} seconds until 07:00.")
        await asyncio.sleep(sleep_duration)

    else:
        sleep_duration = random.randint(TIME_BETWEEN_CHECKINGS - VARIATION_BETWEEN_CHECKINGS, TIME_BETWEEN_CHECKINGS + VARIATION_BETWEEN_CHECKINGS)

        logger.debug(f"Waiting for {sleep_duration} seconds before the next check...")
        await asyncio.sleep(sleep_duration)


asyncio.run(check_elements())
