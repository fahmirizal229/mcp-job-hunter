#!/home/arusuka/.crawl4ai-env/bin/python
"""
Playwright Stealth Job & Web Scraper
Extracts clean job details, requirements, company, and role from protected websites (Jobstreet, LinkedIn, Glints, etc.)
"""

import sys
import os
import re
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

STEALTH_JS = """
// Overwrite navigator.webdriver
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});

// Mock chrome object
window.chrome = {
    runtime: {},
    loadTimes: function() {},
    csi: function() {},
    app: {}
};

// Mock plugins
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5]
});

// Mock languages
Object.defineProperty(navigator, 'languages', {
    get: () => ['id-ID', 'id', 'en-US', 'en']
});
"""

async def extract_jobstreet(page) -> Dict[str, Any]:
    """Custom extractor for Jobstreet / SEEK layout."""
    title = ""
    company = ""
    location = ""
    description = ""
    
    try:
        await page.wait_for_selector('h1, [data-automation="job-detail-title"]', timeout=8000)
    except Exception:
        pass

    content = await page.content()
    soup = BeautifulSoup(content, 'html.parser')

    # 1. Job Title
    title_el = soup.find('h1', {'data-automation': 'job-detail-title'}) or soup.find('h1')
    if title_el:
        title = title_el.get_text(strip=True)

    # 2. Company Name
    comp_el = soup.find('span', {'data-automation': 'advertiser-name'}) or soup.find('a', {'data-automation': 'advertiser-name'})
    if comp_el:
        company = comp_el.get_text(strip=True)

    # 3. Location
    loc_el = soup.find('span', {'data-automation': 'job-detail-location'})
    if loc_el:
        location = loc_el.get_text(strip=True)

    # 4. Job Details / Description
    desc_el = soup.find('div', {'data-automation': 'jobAdDetails'}) or soup.find('div', {'data-automation': 'job-details'})
    if desc_el:
        for li in desc_el.find_all('li'):
            li.insert_before('\n• ')
        description = desc_el.get_text(separator='\n', strip=True)
    else:
        main_el = soup.find('main') or soup.find('article')
        if main_el:
            description = main_el.get_text(separator='\n', strip=True)
        else:
            description = soup.get_text(separator='\n', strip=True)

    description = re.sub(r'\n{3,}', '\n\n', description)

    return {
        "platform": "Jobstreet",
        "title": title or "Job Posting",
        "company": company or "Unknown Company",
        "location": location or "Indonesia",
        "description": description[:4000]
    }

async def extract_generic(page, url: str) -> Dict[str, Any]:
    """Generic full-page extractor using Playwright rendered DOM."""
    content = await page.content()
    soup = BeautifulSoup(content, 'html.parser')

    for tag in soup(['script', 'style', 'noscript', 'iframe', 'nav', 'footer', 'header', 'svg']):
        tag.decompose()

    title = ""
    title_el = soup.find('h1') or soup.find('title')
    if title_el:
        title = title_el.get_text(strip=True)

    for li in soup.find_all('li'):
        li.insert_before('\n• ')

    main_el = soup.find('main') or soup.find('article') or soup.find('body')
    raw_text = main_el.get_text(separator='\n', strip=True) if main_el else soup.get_text(separator='\n', strip=True)
    
    lines = [line.strip() for line in raw_text.splitlines() if len(line.strip()) > 20 and not line.strip().startswith(('Cookie', 'Sign in', 'Log in', 'Accept'))]
    clean_desc = "\n".join(lines[:60])

    return {
        "platform": "Web",
        "title": title or "Career Vacancy",
        "company": "Perusahaan",
        "location": "Indonesia / Remote",
        "description": clean_desc
    }

async def scrape_job_url(url: str, timeout: int = 20) -> Dict[str, Any]:
    """Scrapes any job URL using Playwright with stealth bypass."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-infobars',
                '--window-size=1920,1080'
            ]
        )
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='id-ID',
            timezone_id='Asia/Jakarta'
        )
        page = await context.new_page()
        await page.add_init_script(STEALTH_JS)

        result = {
            "status": "error",
            "url": url,
            "title": "",
            "company": "",
            "location": "",
            "description": "",
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)
            await asyncio.sleep(2)

            if "jobstreet" in url.lower():
                data = await extract_jobstreet(page)
            else:
                data = await extract_generic(page, url)

            result.update({
                "status": "success",
                "title": data.get("title", ""),
                "company": data.get("company", ""),
                "location": data.get("location", ""),
                "description": data.get("description", ""),
                "platform": data.get("platform", "Web")
            })
        except Exception as e:
            result["message"] = str(e)
        finally:
            await browser.close()

        return result

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("Usage: python3 playwright_scraper.py <JOB_URL>")
        sys.exit(0)

    url = sys.argv[1].strip()
    res = asyncio.run(scrape_job_url(url))
    print(json.dumps(res, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
