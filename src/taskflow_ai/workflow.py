"""
Workflow - High-level workflow builder and manager.
工作流 - 高层工作流构建器与管理器。
"""

import time
import json
from typing import Any, Callable, Dict, List, Optional

from .task import Task, TaskStatus, TaskPriority
from .dag import DAGEngine
from .executor import TaskExecutor, ExecutionStrategy
from .ui import TerminalUI


class Workflow:
    """High-level workflow builder for TaskFlow-AI.

    Provides a fluent API for defining, configuring, and executing
    complex AI agent task workflows.

    Example:
        >>> wf = Workflow("my-workflow", "My AI Agent Workflow")
        >>> wf.add_task("research", "Research topic", handler=research_fn)
        >>> wf.add_task("analyze", "Analyze data", handler=analyze_fn, deps=["research"])
        >>> wf.add_task("report", "Generate report", handler=report_fn, deps=["analyze"])
        >>> results = wf.run()
    """

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.dag = DAGEngine()
        self.executor: Optional[TaskExecutor] = None
        self.ui = TerminalUI()
        self._strategy = ExecutionStrategy.LEVEL_BASED
        self._max_workers = 4
        self._verbose = True
        self._metadata: Dict[str, Any] = {}

    def config(
        self,
        strategy: str = None,
        max_workers: int = None,
        verbose: bool = None,
    ) -> "Workflow":
        """Configure workflow execution parameters.

        Args:
            strategy: Execution strategy (sequential/parallel/level_based)
            max_workers: Maximum parallel workers
            verbose: Enable/disable verbose output

        Returns:
            Self for method chaining.
        """
        if strategy is not None:
            self._strategy = strategy
        if max_workers is not None:
            self._max_workers = max_workers
        if verbose is not None:
            self._verbose = verbose
        return self

    def add_task(
        self,
        name: str,
        description: str = "",
        handler: Callable = None,
        deps: List[str] = None,
        priority: str = "medium",
        timeout: float = 0,
        max_retries: int = 0,
        retry_delay: float = 1.0,
        condition: Callable = None,
        tags: List[str] = None,
        metadata: Dict = None,
    ) -> "Workflow":
        """Add a task to the workflow.

        Args:
            name: Unique task name
            description: Task description
            handler: Callable(task, results) -> Any
            deps: List of dependency task names
            priority: Task priority (critical/high/medium/low)
            timeout: Maximum execution time in seconds
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries in seconds
            condition: Optional condition function
            tags: Task tags
            metadata: Task metadata

        Returns:
            Self for method chaining.
        """
        priority_map = {
            "critical": TaskPriority.CRITICAL,
            "high": TaskPriority.HIGH,
            "medium": TaskPriority.MEDIUM,
            "low": TaskPriority.LOW,
        }

        task = Task(
            name=name,
            description=description,
            handler=handler,
            dependencies=deps or [],
            priority=priority_map.get(priority.lower(), TaskPriority.MEDIUM),
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            condition=condition,
            tags=tags or [],
            metadata=metadata or {},
        )

        self.dag.add_task(task)
        return self

    def remove_task(self, name: str) -> "Workflow":
        """Remove a task from the workflow."""
        self.dag.remove_task(name)
        return self

    def get_task(self, name: str) -> Optional[Task]:
        """Get a task by name."""
        return self.dag.get_task(name)

    def on(self, event: str, callback: Callable) -> "Workflow":
        """Register an event callback. Creates executor lazily."""
        if self.executor is None:
            self.executor = TaskExecutor(
                self.dag, self._strategy, self._max_workers, self._verbose
            )
        self.executor.on(event, callback)
        return self

    def validate(self) -> bool:
        """Validate the workflow configuration."""
        is_valid, errors = self.dag.validate()
        if not is_valid:
            for error in errors:
                print(f"  ❌ Validation Error: {error}")
        return is_valid

    def plan(self) -> None:
        """Display the execution plan without running."""
        self.ui.banner()
        self.ui.workflow_overview(self.dag)
        self.ui.execution_plan(self.dag)

    def run(self) -> Dict[str, Any]:
        """Execute the workflow.

        Returns:
            Dictionary containing execution results and report.
        """
        start_time = time.time()

        if self._verbose:
            self.ui.banner()
            self.ui.workflow_overview(self.dag)
            self.ui.execution_plan(self.dag)

        # Validate
        is_valid, errors = self.dag.validate()
        if not is_valid:
            for error in errors:
                print(f"  ❌ {error}")
            return {"success": False, "errors": errors}

        # Create executor
        self.executor = TaskExecutor(
            self.dag, self._strategy, self._max_workers, self._verbose
        )

        # Execute
        results = self.executor.execute()

        end_time = time.time()
        total_duration_ms = (end_time - start_time) * 1000

        # Display results
        if self._verbose:
            self.ui.execution_progress(self.executor, self.dag)
            report = self.ui.workflow_report(self.dag, self.executor, total_duration_ms)

        # Build final output
        output = {
            "success": self.executor.failed_count == 0,
            "workflow": self.name,
            "description": self.description,
            "strategy": self._strategy,
            "total_tasks": self.dag.task_count,
            "completed": self.executor.completed_count,
            "failed": self.executor.failed_count,
            "success_rate": f"{self.executor.success_rate:.1f}%",
            "total_duration_ms": round(total_duration_ms, 2),
            "results": {name: r.to_dict() for name, r in results.items()},
            "dag": self.dag.to_dict(),
        }

        return output

    def run_and_export(self, filepath: str = "workflow_report.json") -> Dict[str, Any]:
        """Execute workflow and export results to JSON.

        Args:
            filepath: Path to export JSON report.

        Returns:
            Execution results dictionary.
        """
        output = self.run()
        self.ui.export_json(output, filepath)
        return output

    def to_dict(self) -> Dict:
        """Export workflow configuration as dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "strategy": self._strategy,
            "max_workers": self._max_workers,
            "metadata": self._metadata,
            "dag": self.dag.to_dict(),
        }

    def to_json(self) -> str:
        """Export workflow configuration as JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2, default=str)

    def __repr__(self) -> str:
        return f"Workflow(name={self.name!r}, tasks={self.dag.task_count})"
