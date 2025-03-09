import asyncio
from playwright.async_api import async_playwright
import os
import time
import playwright

from dotenv import load_dotenv
from loguru import logger

load_dotenv()
logger.level("TRACE")

TIME_BETWEEN_CHECKINGS = 600
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

mkdir -p ~/.config/systemd/user/
vim ~/.config/systemd/user/check_clock_punches_playwright.service
```
[Unit]
Description=Run check_clock_punches_playwright.py
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=3600
WorkingDirectory=/home/your_username/Documents/
ExecStart=/bin/bash --login -c 'set -x; /usr/bin/python3 /home/your_username/Documents/check_clock_punches_playwright.py'

[Install]
WantedBy=multi-user.target
```

systemctl --user daemon-reload
systemctl --user enable check_clock_punches_playwright.service
systemctl --user start check_clock_punches_playwright.service
journalctl --user -u check_clock_punches_playwright.service -f


vim ~/.config/systemd/user/supervise_clock_punches_playwright.service
```
[Unit]
Description=Supervise if is running /home/your_username/Documents/check_clock_punches_playwright.py
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=600
WorkingDirectory=/home/your_username/Documents/
ExecStart=/bin/bash --login -c 'if [[ "w$(ps aux | grep chromium-unstable | grep chrome-ahgora-playwright | grep -v "chrome-ahgora-playwright process is not running" )" == "w" ]] ; then notify-send "Alert" "The chrome-ahgora-playwright process is not running!"; fi;'

[Install]
WantedBy=multi-user.target
```

systemctl --user daemon-reload
systemctl --user enable supervise_clock_punches_playwright.service
systemctl --user start supervise_clock_punches_playwright.service
journalctl --user -u supervise_clock_punches_playwright.service -f

"""

async def check_elements():

    async with async_playwright() as playcontext:

        # Launch persistent context using an existing Chrome installation
        context = await playcontext.chromium.launch_persistent_context(
            r"/home/your_username/chrome-ahgora-playwright/",  # Path to your custom profile
            headless=False,
            executable_path=r"/usr/bin/chromium-browser-unstable",
            args=[
                # '--start-maximized',
                # '--profile-directory=/home/your_username/chrome-ahgora-playwright',
            ]
        )

        await context.grant_permissions(["notifications"], origin='https://app.ahgora.com.br')

        # Open a new page
        # page = await context.new_page()
        page = context.pages[0]

        while True:
            try:
                # Navigate to your desired URL
                await page.goto('https://www.ahgora.com.br/externo/index/empresakhomp')
                await page.wait_for_load_state('networkidle')

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

            logger.debug(f"Waiting for {TIME_BETWEEN_CHECKINGS} seconds before the next check...")
            time.sleep(TIME_BETWEEN_CHECKINGS)

asyncio.run(check_elements())
