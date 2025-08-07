#!/usr/bin/env python3
"""
tokopedia_reviews_scraper_firefox.py

Scrapes user reviews from:
  https://www.tokopedia.com/msi-official-store/review

Uses Selenium with Firefox to render & scroll, then BeautifulSoup to parse:
 - username
 - star rating
 - date
 - review text
"""

import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from webdriver_manager.firefox import GeckoDriverManager
import os
import sys
from tempfile import mkdtemp
from bs4 import BeautifulSoup

def scrape_tokopedia_reviews_firefox(
    url: str,
    headless: bool = True,
    max_scrolls: int = 10,
    scroll_pause: float = 2.0
):
    
    custom_tmp = os.path.expanduser("~/selenium_tmp")
    os.makedirs(custom_tmp, exist_ok=True)
    os.environ["TMPDIR"] = custom_tmp

    # ─── Setup Selenium WebDriver (Firefox) ──────────────────────────────────
    ff_opts = FirefoxOptions()
    ff_opts.binary_location = "/usr/bin/firefox"  # use the system Firefox binary
    if headless:
        ff_opts.add_argument("--headless")
    # optional performance flags
    ff_opts.add_argument("--disable-gpu")
    ff_opts.add_argument("--no-sandbox")
    ff_opts.add_argument("--width=1920")
    ff_opts.add_argument("--height=1080")


    profile_dir = mkdtemp(prefix="selenium-profile-", dir=custom_tmp)
    print(f">> Profile dir: {profile_dir}")
    if not os.path.isdir(profile_dir):
        print(f"✗ Profile dir does not exist: {profile_dir}", file=sys.stderr)
        sys.exit(1)
    if not os.access(profile_dir, os.W_OK):
        print(f"✗ No write permission on profile dir: {profile_dir}", file=sys.stderr)
        sys.exit(1)

    profile = FirefoxProfile(profile_dir)
    # In Selenium 4+, attach it to options instead of passing firefox_profile arg
    ff_opts.profile = profile


    service = FirefoxService(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=ff_opts)

    try:
        # ─── Load page ──────────────────────────────────────────────────────────
        driver.get(url)
        time.sleep(scroll_pause)  # initial load

        # ─── Scroll to load more reviews ───────────────────────────────────────
        # last_height = driver.execute_script("return document.body.scrollHeight")
        # for _ in range(max_scrolls):
        #     driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        #     time.sleep(scroll_pause)
        #     new_height = driver.execute_script("return document.body.scrollHeight")
        #     if new_height == last_height:
        #         break
        #     last_height = new_height

        # ─── Grab rendered HTML ─────────────────────────────────────────────────
        page_source = driver.page_source

    finally:
        driver.quit()
    
    print(">> Scraping completed, parsing reviews...")
    print(f">> Total reviews found: {len(page_source)}")
    # ─── Parse with BeautifulSoup ────────────────────────────────────────────
    soup = BeautifulSoup(page_source, "html.parser")
    products = []
    for item in soup.select(".css-79elbk"):
        image_el = item.select_one("img.wSt-NCwsL186UdS6D-IpAg\\=\\=")
        percentage_el = item.select_one('span._7UCYdN8MrOTwg0MKcGu8zg\\=\\=')
        name_el = item.select_one('div.SzILjt4fxHUFNVT48ZPhHA\\=\\= span.\\+tnoqZhn89\\+NHUA43BpiJg\\=\\=')
        price_el = item.select_one('div.urMOIDHH7I0Iy1Dv2oFaNw\\=\\=')
        original_price_el = item.select_one('div.e48Kml5BRW9dq8Mopwgv7w\\=\\= span.hC1B8wTAoPszbEZj80w6Qw\\=\\=')
    
        products.append({
            "image": image_el["src"] if image_el else None,
            "name": name_el.get_text(strip=True) if name_el else None,
            "price": int(price_el.get_text(strip=True).replace("Rp", "").replace(".", "")) if price_el else None,
            "original_price": int(original_price_el.get_text(strip=True).replace("Rp", "").replace(".", "")) if original_price_el else None,
            "discount_percentage": float(percentage_el.get_text(strip=True).replace("%", "")) if percentage_el else None,
        })
    return products

if __name__ == "__main__":
    URL = "https://www.tokopedia.com/msi-official-store/product"

    data = scrape_tokopedia_reviews_firefox(
        url=URL,
        headless=True,     # set False if you want to see the browser
        max_scrolls=8,     # increase for more reviews
        scroll_pause=5,  # seconds to wait after each scroll
    )

    for i, r in enumerate(data, 1):
        print (f"{i}. {r['name']} — {r['price']} IDR")
        print(f"   Original Price: {r['original_price']} IDR, Discount: {r['discount_percentage']}%")
        print(f"   Image URL: {r['image']}\n")
    print(">> Scraping completed.")
