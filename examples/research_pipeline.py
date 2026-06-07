"""
Example: AI Agent Research Pipeline
示例：AI Agent研究流水线
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from taskflow_ai.workflow import Workflow


def main():
    """Run an AI agent research pipeline demo."""

    wf = Workflow(
        "ai-research-pipeline",
        "AI Agent Automated Research Pipeline"
    )

    # Step 1: Define research scope
    wf.add_task(
        "define_scope",
        "Define research scope and keywords",
        handler=lambda task, results: {
            "topic": "Large Language Models",
            "keywords": ["LLM", "transformer", "attention mechanism"],
            "date_range": "2025-01-01 to 2025-06-07",
            "sources": ["arxiv", "github", "hackernews"],
        },
        priority="critical",
        tags=["planning"],
    )

    # Step 2: Fetch data from multiple sources (parallel)
    wf.add_task(
        "fetch_arxiv",
        "Fetch papers from arXiv",
        handler=lambda task, results: {
            "papers_found": 45,
            "relevant": 12,
            "top_paper": "Attention Is All You Need (Revisited)",
        },
        deps=["define_scope"],
        priority="high",
        tags=["fetch", "academic"],
    )

    wf.add_task(
        "fetch_github",
        "Fetch trending repos from GitHub",
        handler=lambda task, results: {
            "repos_found": 30,
            "starred": 8,
            "top_repo": "awesome-llm-resources",
        },
        deps=["define_scope"],
        priority="high",
        tags=["fetch", "code"],
    )

    wf.add_task(
        "fetch_hackernews",
        "Fetch discussions from Hacker News",
        handler=lambda task, results: {
            "threads": 25,
            "insights": 10,
            "top_discussion": "The Future of LLM Agents",
        },
        deps=["define_scope"],
        priority="high",
        tags=["fetch", "community"],
    )

    # Step 3: Analyze all fetched data
    wf.add_task(
        "analyze_data",
        "Cross-analyze all collected data",
        handler=lambda task, results: {
            "total_sources": 3,
            "key_findings": 15,
            "trends": ["multimodal", "agent frameworks", "efficiency"],
            "confidence": 0.92,
        },
        deps=["fetch_arxiv", "fetch_github", "fetch_hackernews"],
        priority="high",
        tags=["analysis"],
    )

    # Step 4: Generate insights
    wf.add_task(
        "generate_insights",
        "Generate actionable insights",
        handler=lambda task, results: {
            "insights_count": 7,
            "action_items": 4,
            "risk_factors": 2,
        },
        deps=["analyze_data"],
        priority="medium",
        tags=["synthesis"],
    )

    # Step 5: Create final report
    wf.add_task(
        "create_report",
        "Create comprehensive research report",
        handler=lambda task, results: {
            "format": "markdown",
            "sections": 8,
            "word_count": 3500,
            "ready_for_review": True,
        },
        deps=["generate_insights"],
        priority="medium",
        tags=["output"],
    )

    # Run the workflow
    results = wf.run_and_export("research_report.json")

    print(f"\n  🎯 Workflow {'succeeded' if results['success'] else 'failed'}!")
    print(f"  📊 Completed: {results['completed']}/{results['total_tasks']}")
    print(f"  ⏱️  Duration: {results['total_duration_ms']:.0f}ms")


if __name__ == "__main__":
    main()
