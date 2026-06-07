#!/usr/bin/env python3
"""
TaskFlow-AI CLI - Command-line interface for the task flow orchestration engine.
TaskFlow-AI CLI - 任务流编排引擎的命令行接口。
"""

import sys
import os
import json
import argparse

# Ensure src directory is in path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from taskflow_ai.workflow import Workflow
from taskflow_ai.task import Task, TaskPriority
from taskflow_ai.dag import DAGEngine
from taskflow_ai.executor import ExecutionStrategy
from taskflow_ai.ui import TerminalUI, Colors
from taskflow_ai import __version__


def cmd_version(args):
    """Show version information."""
    print(f"\n  🔄 TaskFlow-AI v{__version__}")
    print(f"  📝 Lightweight AI Agent Task Flow Orchestration Engine")
    print(f"  📝 轻量级AI Agent任务流编排引擎\n")


def cmd_demo(args):
    """Run the built-in demo workflow."""
    print(f"\n  🔄 Running TaskFlow-AI Demo Workflow...\n")

    wf = Workflow("demo-workflow", "TaskFlow-AI Demo - AI Agent Task Pipeline")

    # Define tasks simulating an AI agent workflow
    wf.add_task(
        "fetch_data",
        "Fetch raw data from sources",
        handler=lambda task, results: {
            "records": 150,
            "sources": ["web", "api", "database"],
            "timestamp": "2025-06-07T10:00:00Z"
        },
        priority="high",
        tags=["io", "fetch"],
    )

    wf.add_task(
        "validate_data",
        "Validate and clean fetched data",
        handler=lambda task, results: {
            "valid": 142,
            "invalid": 8,
            "cleaned": True
        },
        deps=["fetch_data"],
        priority="high",
    )

    wf.add_task(
        "analyze_patterns",
        "Analyze patterns in validated data",
        handler=lambda task, results: {
            "patterns_found": 23,
            "confidence": 0.87,
            "anomalies": 3
        },
        deps=["validate_data"],
        priority="medium",
    )

    wf.add_task(
        "generate_summary",
        "Generate executive summary",
        handler=lambda task, results: {
            "summary_length": 500,
            "key_findings": 5,
            "recommendations": 3
        },
        deps=["analyze_patterns"],
        priority="medium",
    )

    wf.add_task(
        "format_report",
        "Format final report for delivery",
        handler=lambda task, results: {
            "format": "markdown",
            "pages": 3,
            "ready": True
        },
        deps=["generate_summary"],
        priority="low",
    )

    wf.config(strategy=args.strategy or "level_based", verbose=True)
    results = wf.run()

    return results


def cmd_quick(args):
    """Run a quick task from command line."""
    wf = Workflow("quick-task", args.description or "Quick Task")

    # Build a simple handler from command
    if args.command:
        def handler(task, results):
            os.system(args.command)
            return f"Executed: {args.command}"
    else:
        handler = lambda task, results: {"status": "completed", "message": "Quick task done"}

    wf.add_task(
        args.name or "quick",
        args.description or "Quick task",
        handler=handler,
        timeout=args.timeout or 0,
        max_retries=args.retries or 0,
    )

    wf.config(strategy="sequential", verbose=not args.quiet)
    return wf.run()


def cmd_validate(args):
    """Validate a workflow JSON file."""
    filepath = args.file
    if not os.path.exists(filepath):
        print(f"  ❌ File not found: {filepath}")
        return

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    wf = Workflow(data.get("name", "unknown"), data.get("description", ""))

    for task_data in data.get("tasks", []):
        wf.add_task(
            name=task_data["name"],
            description=task_data.get("description", ""),
            deps=task_data.get("dependencies", []),
            priority=task_data.get("priority", "medium"),
            timeout=task_data.get("timeout", 0),
            max_retries=task_data.get("max_retries", 0),
        )

    print(f"\n  📋 Validating workflow: {Colors.BOLD}{data.get('name', 'unknown')}{Colors.RESET}\n")
    is_valid = wf.validate()

    if is_valid:
        print(f"\n  ✅ Workflow is valid!")
        print(f"  📊 Tasks: {wf.dag.task_count}")
        print(f"  📊 Levels: {len(wf.dag.get_execution_levels())}")
        wf.plan()
    else:
        print(f"\n  ❌ Workflow validation failed!")

    return {"valid": is_valid}


def cmd_info(args):
    """Show system information."""
    print(f"\n  🔄 TaskFlow-AI v{__version__}")
    print(f"  {'─' * 40}")
    print(f"  🐍 Python: {sys.version.split()[0]}")
    print(f"  💻 Platform: {os.name}")
    print(f"  📁 Working Dir: {os.getcwd()}")
    print(f"  📦 Dependencies: Zero (pure stdlib)")
    print(f"  📋 Execution Strategies: sequential, parallel, level_based")
    print(f"  🔧 Features: DAG, retry, timeout, conditions, callbacks\n")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="taskflow",
        description="TaskFlow-AI - Lightweight AI Agent Task Flow Orchestration Engine",
    )
    parser.add_argument("-v", "--version", action="store_true", help="Show version")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # demo command
    demo_parser = subparsers.add_parser("demo", help="Run demo workflow")
    demo_parser.add_argument("-s", "--strategy", help="Execution strategy")

    # quick command
    quick_parser = subparsers.add_parser("quick", help="Run a quick task")
    quick_parser.add_argument("-n", "--name", help="Task name")
    quick_parser.add_argument("-d", "--description", help="Task description")
    quick_parser.add_argument("-c", "--command", help="Shell command to execute")
    quick_parser.add_argument("-t", "--timeout", type=float, help="Timeout in seconds")
    quick_parser.add_argument("-r", "--retries", type=int, help="Max retries")
    quick_parser.add_argument("-q", "--quiet", action="store_true", help="Quiet mode")

    # validate command
    validate_parser = subparsers.add_parser("validate", help="Validate workflow JSON")
    validate_parser.add_argument("file", help="Workflow JSON file path")

    # info command
    subparsers.add_parser("info", help="Show system information")

    args = parser.parse_args()

    if args.version:
        cmd_version(args)
    elif args.command == "demo":
        cmd_demo(args)
    elif args.command == "quick":
        cmd_quick(args)
    elif args.command == "validate":
        cmd_validate(args)
    elif args.command == "info":
        cmd_info(args)
    else:
        parser.print_help()
        print(f"\n  💡 Quick start: {Colors.CYAN}python -m taskflow_ai demo{Colors.RESET}\n")


if __name__ == "__main__":
    main()
