from DCArticleCrawler import DCArticleCrawler

# Example usage
crawler = DCArticleCrawler(
    gallery_id="forthegifted",
    gall_type="minor",
    start_date="2025.05.26",
    end_date="2025.06.06",
    is_headless=True,
    maximum_batch_size=10,
    jsonl_path="stockus_data/stockus_articles_all_test.jsonl"
)
crawler.run()
