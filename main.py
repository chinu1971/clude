"""
Leofame Instagram Automation - No Telegram Version
"""

import os
import time
import random
import logging
import json
import argparse
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth
from fake_useragent import UserAgent

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

# --- Argument parser ---
parser = argparse.ArgumentParser(description="Leofame Instagram Automation")
parser.add_argument(
    "--link",
    default=os.environ.get(
        "INSTAGRAM_LINK",
        "https://www.instagram.com/reel/DWwKjHqkkAm/?igsh=djUzOHNvbWxlYzVs"
    )
)
parser.add_argument("--wait-min", type=int, default=60)
parser.add_argument("--wait-max", type=int, default=90)
args = parser.parse_args()

# --- Config ---
INSTAGRAM_LINK = args.link
WAIT_MIN = args.wait_min
WAIT_MAX = args.wait_max

URLS = [
    "https://leofame.com/free-instagram-views",
    "https://leofame.com/free-instagram-likes",
    "https://leofame.com/free-instagram-saves",
    "https://leofame.com/free-instagram-shares",
]

SCREENSHOT_DIR = Path("screenshots")
SCREENSHOT_DIR.mkdir(exist_ok=True)

LOG_FILE = Path("run_log.json")


def is_valid_instagram_url(url: str) -> bool:
    return "instagram.com" in url and url.startswith("https://")


def take_screenshot(driver, name: str) -> Path:
    path = SCREENSHOT_DIR / name
    driver.save_screenshot(str(path))
    return path


def save_log(results: list):
    existing = []
    if LOG_FILE.exists():
        try:
            existing = json.loads(LOG_FILE.read_text())
        except Exception:
            pass
    existing.append({
        "run_time": datetime.now().isoformat(),
        "results": results
    })
    LOG_FILE.write_text(json.dumps(existing, indent=2))
    log.info(f"Run log saved to {LOG_FILE}")


def build_driver() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(f"--user-agent={UserAgent().random}")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )
    driver.set_page_load_timeout(30)

    stealth(
        driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )
    return driver


def submit_all_services():
    if not is_valid_instagram_url(INSTAGRAM_LINK):
        log.error(f"Invalid Instagram URL: {INSTAGRAM_LINK}")
        return

    driver = build_driver()
    wait = WebDriverWait(driver, 25)
    results = []

    try:
        for url in URLS:
            page_name = url.split("/")[-1]
            log.info(f"Processing: {url}")
            status = "success"

            try:
                driver.get(url)

                if "captcha" in driver.page_source.lower() or "error" in driver.title.lower():
                    log.warning(f"Blocked on {url}")
                    take_screenshot(driver, f"{page_name}_blocked.png")
                    status = "blocked"
                    results.append({"page": page_name, "status": status})
                    continue

                link_box = wait.until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "input[placeholder*='instagram.com']")
                    )
                )
                link_box.clear()
                link_box.send_keys(INSTAGRAM_LINK)

                button = wait.until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'get free')]",
                    ))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", button)
                button.click()
                log.info(f"Clicked for: {page_name}")

                take_screenshot(driver, f"{page_name}_after_click.png")

                wait_time = random.uniform(WAIT_MIN, WAIT_MAX)
                log.info(f"Waiting {wait_time:.1f}s...")
                time.sleep(wait_time)

                take_screenshot(driver, f"{page_name}_after_wait.png")

            except Exception as e:
                log.error(f"Failed on {url}: {e}")
                status = "failed"
                try:
                    take_screenshot(driver, f"{page_name}_error.png")
                except Exception:
                    pass

            results.append({"page": page_name, "status": status})

    finally:
        driver.quit()
        log.info("Driver closed.")

    success = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "failed")
    blocked = sum(1 for r in results if r["status"] == "blocked")

    summary = (
        f"Run complete — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"Success: {success} | Failed: {failed} | Blocked: {blocked}\n\n"
        + "\n".join(f"  {r['page']}: {r['status']}" for r in results)
    )

    save_log(results)
    log.info(summary)


if __name__ == "__main__":
    submit_all_services()
