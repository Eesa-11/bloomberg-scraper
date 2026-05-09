# Bloomberg News Scraper API

**Registration:** FA23-BAI-031  
**News Source:** Bloomberg News  
**Development Environment:** Python 3.11

## Description
A Docker-based Selenium automation system that searches Bloomberg News for a given keyword, fetches the first search result, summarizes the article, and exposes the result via a REST API.

## Tech Stack
- Python 3.11
- Flask (REST API)
- Selenium (web scraping)
- Google Chrome + ChromeDriver (headless browser)

## API Specification

**Endpoint:** `/get`  
**Method:** GET  
**Port:** 7000  
**Query Parameter:** `keyword` (string)

### Response JSON
```json
{
  "registration": "FA23-BAI-031",
  "newssource": "Bloomberg",
  "keyword": "string",
  "url": "string",
  "summary": "string"
}
```

### Sample Call
```
http://localhost:7000/get?keyword=bitcoin
```

## Running with Docker

```bash
# Pull the image
docker pull orakzaieesa11/bloomberg-scraper:latest

# Run the container
docker run -p 7000:7000 orakzaieesa11/bloomberg-scraper:latest

# Test the API
curl "http://localhost:7000/get?keyword=bitcoin"
```

## Building Locally

```bash
docker build -t bloomberg-scraper .
docker run -p 7000:7000 bloomberg-scraper
```
