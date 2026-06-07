"""
Terminal UI - Rich terminal interface for workflow visualization.
终端UI - 工作流可视化的富终端界面。
"""

import time
import json
from typing import Dict, List, Optional

from .task import Task, TaskStatus, TaskPriority
from .dag import DAGEngine
from .executor import TaskExecutor


class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"
    BG_GREEN = "\033[42m"
    BG_RED = "\033[41m"


class TerminalUI:
    """Rich terminal UI for TaskFlow-AI workflow visualization."""

    WIDTH = 60

    def __init__(self, verbose: bool = True):
        self.verbose = verbose

    def banner(self) -> None:
        """Display the TaskFlow-AI banner."""
        banner_text = """
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   🔄 TaskFlow-AI                                         ║
║   Lightweight AI Agent Task Flow Orchestration Engine     ║
║   轻量级AI Agent任务流编排引擎                            ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
"""
        print(f"{Colors.CYAN}{banner_text}{Colors.RESET}")

    def separator(self, char: str = "─", width: int = None) -> None:
        """Print a separator line."""
        w = width or self.WIDTH
        print(f"{Colors.GRAY}{char * w}{Colors.RESET}")

    def section(self, title: str, icon: str = "📋") -> None:
        """Print a section header."""
        print(f"\n{Colors.BOLD}{Colors.WHITE}{icon} {title}{Colors.RESET}")
        self.separator()

    def task_summary(self, task: Task, show_deps: bool = False) -> None:
        """Print a summary of a single task."""
        status_icon = task.status.icon()
        status_color = task.status.color_code()
        priority_color = task.priority.color_code()

        print(f"  {status_icon} {Colors.BOLD}{task.name}{Colors.RESET}")
        print(f"     {Colors.DIM}{task.description or 'No description'}{Colors.RESET}")
        print(f"     Status: {status_color}{task.status.value.upper()}{Colors.RESET}  "
              f"Priority: {priority_color}{task.priority.label()}{Colors.RESET}")

        if show_deps and task.dependencies:
            print(f"     Dependencies: {Colors.CYAN}{', '.join(task.dependencies)}{Colors.RESET}")

        if task.result:
            r = task.result
            if r.success:
                print(f"     {Colors.GREEN}✓ Completed in {r.duration_ms:.1f}ms{Colors.RESET}")
                if r.output and r.output != "Condition not met" and r.output != "Blocked by failed dependencies":
                    output_str = str(r.output)[:100]
                    print(f"     Output: {Colors.DIM}{output_str}{Colors.RESET}")
            else:
                print(f"     {Colors.RED}✗ Failed: {r.error}{Colors.RESET}")

    def workflow_overview(self, dag: DAGEngine) -> None:
        """Print an overview of the workflow."""
        self.section("Workflow Overview", "📊")

        tasks = list(dag._tasks.values())
        total = len(tasks)

        # Count by status
        status_counts = {}
        for task in tasks:
            status_counts[task.status] = status_counts.get(task.status, 0) + 1

        print(f"  Total Tasks: {Colors.BOLD}{total}{Colors.RESET}")
        print(f"  Execution Levels: {Colors.BOLD}{len(dag.get_execution_levels())}{Colors.RESET}")

        # Status breakdown
        print(f"\n  Status Breakdown:")
        for status, count in sorted(status_counts.items(), key=lambda x: x[0].value):
            icon = status.icon()
            color = status.color_code()
            bar = "█" * count + "░" * (total - count)
            print(f"    {icon} {color}{status.value.upper():<12}{Colors.RESET} "
                  f"{color}{bar}{Colors.RESET} {count}")

    def execution_plan(self, dag: DAGEngine) -> None:
        """Print the execution plan."""
        self.section("Execution Plan", "🗺️")

        levels = dag.get_execution_levels()
        for idx, level in enumerate(levels):
            print(f"\n  {Colors.CYAN}Level {idx + 1}{Colors.RESET} "
                  f"({len(level)} tasks, can run in parallel):")
            for name in level:
                task = dag.get_task(name)
                deps = dag.get_dependencies(name)
                dep_str = f" ← {Colors.DIM}{', '.join(deps)}{Colors.RESET}" if deps else ""
                priority_color = task.priority.color_code()
                print(f"    {Colors.WHITE}• {task.name}{Colors.RESET} "
                      f"[{priority_color}{task.priority.label()}{Colors.RESET}]{dep_str}")

    def execution_progress(self, executor: TaskExecutor, dag: DAGEngine) -> None:
        """Print execution progress summary."""
        self.section("Execution Results", "📈")

        total = dag.task_count
        completed = executor.completed_count
        failed = executor.failed_count
        skipped = sum(1 for t in dag._tasks.values() if t.status == TaskStatus.SKIPPED)

        # Progress bar
        progress = (completed + failed + skipped) / total if total > 0 else 0
        filled = int(progress * 40)
        bar = "█" * filled + "░" * (40 - filled)

        print(f"\n  Progress: [{Colors.CYAN}{bar}{Colors.RESET}] {progress*100:.0f}%")
        print(f"  {Colors.GREEN}✅ Success: {completed}{Colors.RESET}  "
              f"{Colors.RED}❌ Failed: {failed}{Colors.RESET}  "
              f"{Colors.GRAY}⏭️ Skipped: {skipped}{Colors.RESET}")
        print(f"  Success Rate: {Colors.BOLD}{executor.success_rate:.1f}%{Colors.RESET}")

        # Task details
        print(f"\n  Task Details:")
        order = dag.topological_sort()
        for name in order:
            task = dag.get_task(name)
            self.task_summary(task)

    def workflow_report(self, dag: DAGEngine, executor: TaskExecutor,
                        total_duration_ms: float) -> Dict:
        """Generate and display a complete workflow report.

        Returns:
            Report dictionary for JSON export.
        """
        self.section("Workflow Report", "📝")

        total = dag.task_count
        completed = executor.completed_count
        failed = executor.failed_count

        # Calculate total duration from task results
        task_durations = []
        for name, result in executor._results.items():
            if result.duration_ms > 0:
                task_durations.append(result.duration_ms)

        avg_duration = sum(task_durations) / len(task_durations) if task_durations else 0

        print(f"\n  ⏱️  Total Duration: {Colors.BOLD}{total_duration_ms:.1f}ms{Colors.RESET}")
        print(f"  📊 Avg Task Duration: {Colors.BOLD}{avg_duration:.1f}ms{Colors.RESET}")
        print(f"  🎯 Success Rate: {Colors.BOLD}{executor.success_rate:.1f}%{Colors.RESET}")
        print(f"  📈 Throughput: {Colors.BOLD}{total / (total_duration_ms / 1000):.1f} tasks/s{Colors.RESET}" if total_duration_ms > 0 else "")

        # Build report dict
        report = {
            "total_tasks": total,
            "completed": completed,
            "failed": failed,
            "success_rate": f"{executor.success_rate:.1f}%",
            "total_duration_ms": round(total_duration_ms, 2),
            "avg_task_duration_ms": round(avg_duration, 2),
            "tasks": {},
        }

        for name, task in dag._tasks.items():
            report["tasks"][name] = {
                "status": task.status.value,
                "duration_ms": round(task.duration_ms, 2),
                "retries": task.retry_count,
                "result": task.result.to_dict() if task.result else None,
            }

        return report

    def export_json(self, data: Dict, filepath: str) -> None:
        """Export data to JSON file."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n  💾 Report exported to: {Colors.CYAN}{filepath}{Colors.RESET}")
