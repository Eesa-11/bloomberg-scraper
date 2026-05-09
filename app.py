from flask import Flask, jsonify, request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re

app = Flask(__name__)

REGISTRATION = "FA23-BAI-031"
NEWS_SOURCE = "Bloomberg"
NEWS_URL = "https://www.bloomberg.com"


def get_chrome_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    service = Service("/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def summarize_text(text, max_sentences=4):
    """Simple extractive summarizer - picks first N meaningful sentences."""
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    # Filter short/garbage sentences
    sentences = [s.strip() for s in sentences if len(s.strip()) > 40]
    summary = ' '.join(sentences[:max_sentences])
    return summary if summary else text[:600]


def scrape_bloomberg(keyword):
    driver = get_chrome_driver()
    result_url = ""
    summary = ""

    try:
        # Go to Bloomberg search
        search_url = f"https://www.bloomberg.com/search?query={keyword}"
        driver.get(search_url)
        time.sleep(4)

        # Try to find first search result link
        wait = WebDriverWait(driver, 15)

        # Bloomberg search results are typically in story cards
        selectors = [
            "a[href*='/news/articles/']",
            "a[href*='/news/videos/']",
            ".story-list-story__info__headline a",
            "[data-component='headline'] a",
            ".search-result-story__headline a",
            "h3 a",
            "h2 a",
        ]

        article_link = None
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements:
                    href = el.get_attribute("href")
                    if href and "bloomberg.com" in href and keyword.lower() in el.text.lower():
                        article_link = href
                        break
                if not article_link:
                    # Just grab first valid Bloomberg article link
                    for el in elements:
                        href = el.get_attribute("href")
                        if href and "bloomberg.com/news" in href:
                            article_link = href
                            break
                if article_link:
                    break
            except Exception:
                continue

        if not article_link:
            # Fallback: grab any article link on page
            links = driver.find_elements(By.TAG_NAME, "a")
            for link in links:
                href = link.get_attribute("href") or ""
                if "bloomberg.com/news/articles" in href:
                    article_link = href
                    break

        if article_link:
            result_url = article_link
            driver.get(article_link)
            time.sleep(3)

            # Extract article text
            text_selectors = [
                "[data-component='body-text'] p",
                ".body-content p",
                "article p",
                ".article-body p",
                "p",
            ]
            paragraphs = []
            for sel in text_selectors:
                try:
                    elems = driver.find_elements(By.CSS_SELECTOR, sel)
                    paragraphs = [e.text.strip() for e in elems if len(e.text.strip()) > 50]
                    if paragraphs:
                        break
                except Exception:
                    continue

            full_text = " ".join(paragraphs)
            summary = summarize_text(full_text) if full_text else "Article content could not be extracted (may require subscription)."
        else:
            result_url = search_url
            summary = f"No article found for keyword '{keyword}' on Bloomberg."

    except Exception as e:
        result_url = search_url
        summary = f"Error during scraping: {str(e)}"
    finally:
        driver.quit()

    return result_url, summary


@app.route("/get", methods=["GET"])
def get_news():
    keyword = request.args.get("keyword", "").strip()
    if not keyword:
        return jsonify({"error": "keyword parameter is required"}), 400

    url, summary = scrape_bloomberg(keyword)

    return jsonify({
        "registration": REGISTRATION,
        "newssource": NEWS_SOURCE,
        "keyword": keyword,
        "url": url,
        "summary": summary
    })


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "registration": REGISTRATION,
        "message": "Bloomberg News Scraper API",
        "usage": "/get?keyword=your_search_term",
        "port": 7000
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7000, debug=False)
