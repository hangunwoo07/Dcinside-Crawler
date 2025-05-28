# DCInside Crawler

DCInside Crawler is a Python module for batch-crawling DCInside gallery posts (and optional comments) by date range or post number range, and saving the results in JSONL format.

---

## Features

- **Post Parsing**  
  - `DCArticleProcessor`: Parses a single post (and its comments) from HTML into an `ArticleData` dataclass instance.  
- **Batch Crawling**  
  - `DCArticleCrawler`: Iterates over a range of dates (`start_date`/`end_date`) or post numbers (`start_gall_no`/`end_gall_no`), fetches each post, and writes batches of results to a JSONL file.  
- **Deduplication & Batch Writes**  
  - Skips any post numbers that have already been collected, and writes out data every `maximum_batch_size` posts.  
- **Headless Mode**  
  - Supports running Selenium WebDriver in headless mode for CI or server environments.

---

## Repository Structure

```

.
├── DCArticleCrawler.py       # Batch crawling logic
├── DCArticleProcessor.py     # Single-post (and comment) parsing logic
├── test.py                   # Example script demonstrating usage
└── requirements.txt          # Python package dependencies

```

---

## Requirements

- Python 3.7 or higher  
- Google Chrome (installed locally)  
- ChromeDriver matching your Chrome version, or use `webdriver-manager` for automatic driver installation  
- Python packages (listed in `requirements.txt`):
```

selenium
webdriver-manager
beautifulsoup4
requests

````

---

## Installation

1. **Clone the repository**  
 ```bash
 git clone https://github.com/YourUsername/Dcinside-Crawler.git
 cd Dcinside-Crawler
````

2. **Create and activate a virtual environment (optional but recommended)**

   ```bash
   python -m venv .venv
   # macOS/Linux
   source .venv/bin/activate
   # Windows (PowerShell)
   .\.venv\Scripts\activate
   ```
3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

### 1) Run the example script

```bash
python test.py
```

In `test.py`, `DCArticleCrawler` is used like this:

```python
from DCArticleCrawler import DCArticleCrawler

crawler = DCArticleCrawler(
    gallery_id="forthegifted",
    gall_type="minor",             # "main", "minor", or "mini"
    start_date="2025.05.26",       # YYYY.MM.DD
    end_date="2025.05.28",         # YYYY.MM.DD
    is_headless=True,              # run in headless mode
    maximum_batch_size=10,         # how many posts per JSONL write
    jsonl_path="data/articles.jsonl"
)
crawler.run()
```

### 2) Use the module directly

```python
from DCArticleCrawler import DCArticleCrawler

crawler = DCArticleCrawler(
    gallery_id="funnygallery",
    gall_type="main",
    start_gall_no=1000,
    end_gall_no=950,
    is_crawl_comments=False,
    sleep_between_requests=1.0,
    jsonl_path="output/funny_articles.jsonl"
)
crawler.run()
```

* You must specify either `start_date`/`end_date` **or** `start_gall_no`/`end_gall_no` (exclusive).
* Setting `is_crawl_comments=False` will collect only the post bodies without comments.
* Adjust `sleep_between_requests` to throttle your requests as needed.

---

## Output Format

Each line in the JSONL output is a JSON object with the following structure:

```json
{
  "gall_no": 12345,
  "date": "2025.05.27",
  "title": "Post Title",
  "content": "Post body text…",
  "view_count": 100,
  "recommend_count": 5,
  "nonrecommend_count": 1,
  "comments": [
    {
      "text": "text",
      "replies": ["replies"]
    }
    // …
  ]
}
```

---

## Configuration

* **Date format**: Change the `DATE_FORMAT` constant in `DCArticleProcessor.py`.
* **Comment load wait time**: Adjust the `refresh_time_for_comment` parameter.
* **Request delay**: Customize `sleep_between_requests` in `DCArticleCrawler`.
* **Selenium options**: Modify Chrome options in `DCArticleCrawler._init_driver()`.
