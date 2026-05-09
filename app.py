from flask import Flask, jsonify, request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re

app = Flask(__name__)

REGISTRATION = "FA23-BAI-031"
NEWS_SOURCE = "MinuteMirror"
BASE_SEARCH_URL = "https://minutemirror.com.pk/?s="


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
    """Simple extractive summarizer — picks first N meaningful sentences."""
    text = re.sub(r'\s+', ' ', text).strip()
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 40]
    summary = ' '.join(sentences[:max_sentences])
    return summary if summary else text[:600]


def scrape_minutemirror(keyword):
    driver = get_chrome_driver()
    result_url = ""
    summary = ""

    try:
        # Search Minute Mirror for Bloomberg-related articles about the keyword
        search_url = BASE_SEARCH_URL + keyword.replace(" ", "+") + "+bloomberg"
        driver.get(search_url)
        time.sleep(3)

        article_link = None

        # Minute Mirror search results: article links in headings or article cards
        selectors = [
            "h2.entry-title a",
            "h3.entry-title a",
            ".post-title a",
            "article h2 a",
            "article h3 a",
            ".entry-header a",
            "h2 a",
            "h3 a",
        ]

        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements:
                    href = el.get_attribute("href")
                    if href and "minutemirror.com.pk" in href:
                        article_link = href
                        break
                if article_link:
                    break
            except Exception:
                continue

        # Fallback: try without bloomberg filter
        if not article_link:
            fallback_url = BASE_SEARCH_URL + keyword.replace(" ", "+")
            driver.get(fallback_url)
            time.sleep(3)
            for selector in selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for el in elements:
                        href = el.get_attribute("href")
                        if href and "minutemirror.com.pk" in href and "/20" in href:
                            article_link = href
                            break
                    if article_link:
                        break
                except Exception:
                    continue

        if article_link:
            result_url = article_link
            driver.get(article_link)
            time.sleep(3)

            # Extract article text from Minute Mirror article page
            text_selectors = [
                ".entry-content p",
                ".post-content p",
                "article .content p",
                ".article-body p",
                "article p",
                "p",
            ]

            paragraphs = []
            for sel in text_selectors:
                try:
                    elems = driver.find_elements(By.CSS_SELECTOR, sel)
                    paragraphs = [
                        e.text.strip() for e in elems
                        if len(e.text.strip()) > 50
                    ]
                    if paragraphs:
                        break
                except Exception:
                    continue

            full_text = " ".join(paragraphs)
            if full_text:
                summary = summarize_text(full_text)
            else:
                summary = "Article content could not be extracted."
        else:
            result_url = BASE_SEARCH_URL + keyword.replace(" ", "+")
            summary = f"No article found for keyword '{keyword}' on Minute Mirror."

    except Exception as e:
        result_url = BASE_SEARCH_URL + keyword.replace(" ", "+")
        summary = f"Error during scraping: {str(e)}"
    finally:
        driver.quit()

    return result_url, summary


@app.route("/get", methods=["GET"])
def get_news():
    keyword = request.args.get("keyword", "").strip()
    if not keyword:
        return jsonify({"error": "keyword parameter is required"}), 400

    url, summary = scrape_minutemirror(keyword)

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
        "message": "Minute Mirror news scrapper",
        "usage": "/get?keyword=your_search_term",
        "port": 7000
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7000, debug=False)