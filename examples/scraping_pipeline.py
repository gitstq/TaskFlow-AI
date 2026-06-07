"""
Example: Web Scraping Pipeline with Error Handling
示例：带错误处理的网页抓取流水线
"""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from taskflow_ai.workflow import Workflow


def main():
    """Run a web scraping pipeline with retries and error handling."""

    wf = Workflow(
        "scraping-pipeline",
        "Multi-Source Web Scraping Pipeline with Error Handling"
    )

    # Step 1: Initialize scraper
    wf.add_task(
        "init_scraper",
        "Initialize scraping session and load configs",
        handler=lambda task, results: {
            "session_id": "sess_abc123",
            "user_agent": "TaskFlow-Bot/1.0",
            "rate_limit": 10,
        },
        priority="critical",
    )

    # Step 2: Scrape multiple pages (some may fail)
    wf.add_task(
        "scrape_page_1",
        "Scrape product listing page",
        handler=lambda task, results: {
            "url": "https://example.com/products",
            "items": 50,
            "pages": 5,
        },
        deps=["init_scraper"],
        priority="high",
        max_retries=3,
        retry_delay=0.5,
    )

    wf.add_task(
        "scrape_page_2",
        "Scrape reviews page (simulated failure then success)",
        handler=lambda task, results: (_ for _ in ()).throw(
            ConnectionError("Connection timeout")
        ) if not hasattr(task, '_retry_count') or task.retry_count == 0
        else {"url": "https://example.com/reviews", "reviews": 200},
        deps=["init_scraper"],
        priority="high",
        max_retries=2,
        retry_delay=0.3,
    )

    wf.add_task(
        "scrape_page_3",
        "Scrape pricing page",
        handler=lambda task, results: {
            "url": "https://example.com/pricing",
            "plans": 3,
            "currency": "USD",
        },
        deps=["init_scraper"],
        priority="medium",
    )

    # Step 3: Process scraped data
    wf.add_task(
        "process_data",
        "Process and normalize scraped data",
        handler=lambda task, results: {
            "normalized": True,
            "duplicates_removed": 5,
            "total_records": 248,
        },
        deps=["scrape_page_1", "scrape_page_3"],
        priority="high",
    )

    # Step 4: Export results
    wf.add_task(
        "export_results",
        "Export processed data to JSON",
        handler=lambda task, results: {
            "output_file": "scraped_data.json",
            "size_kb": 125.5,
            "records": 248,
        },
        deps=["process_data"],
        priority="low",
    )

    # Run
    results = wf.run()

    print(f"\n  🎯 Pipeline {'succeeded' if results['success'] else 'partially completed'}")
    print(f"  ✅ Completed: {results['completed']}/{results['total_tasks']}")
    print(f"  ❌ Failed: {results['failed']}/{results['total_tasks']}")


if __name__ == "__main__":
    main()
