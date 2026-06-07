"""
Executor - Task execution engine with retry, timeout, and error handling.
执行器 - 支持重试、超时和错误处理的任务执行引擎。
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError
from typing import Any, Callable, Dict, List, Optional, Set

from .task import Task, TaskStatus, TaskResult
from .dag import DAGEngine


class ExecutionStrategy:
    """Execution strategy constants."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    LEVEL_BASED = "level_based"


class TaskExecutor:
    """Task execution engine.

    Supports multiple execution strategies, automatic retry on failure,
    timeout management, and conditional execution.
    """

    def __init__(
        self,
        dag: DAGEngine,
        strategy: str = ExecutionStrategy.LEVEL_BASED,
        max_workers: int = 4,
        verbose: bool = True,
    ):
        self.dag = dag
        self.strategy = strategy
        self.max_workers = max_workers
        self.verbose = verbose
        self._lock = threading.Lock()
        self._completed: Set[str] = set()
        self._failed: Set[str] = set()
        self._results: Dict[str, TaskResult] = {}
        self._callbacks: Dict[str, List[Callable]] = {
            "on_task_start": [],
            "on_task_complete": [],
            "on_task_fail": [],
            "on_workflow_complete": [],
        }

    def on(self, event: str, callback: Callable) -> None:
        """Register a callback for an event."""
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def _emit(self, event: str, *args, **kwargs) -> None:
        """Emit an event to registered callbacks."""
        for callback in self._callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception:
                pass  # Callback errors should not break execution

    def _execute_single_task(self, task: Task) -> TaskResult:
        """Execute a single task with retry and timeout support.

        Args:
            task: Task to execute

        Returns:
            TaskResult with execution outcome.
        """
        if task.handler is None:
            task.mark_skipped("No handler defined")
            return task.result

        # Check condition
        if task.condition is not None:
            try:
                if not task.condition(task, self._results):
                    task.mark_skipped("Condition not met")
                    return task.result
            except Exception as e:
                task.mark_failed(f"Condition check failed: {e}")
                return task.result

        while True:
            try:
                task.mark_running()
                self._emit("on_task_start", task)

                # Execute with timeout if specified
                if task.timeout > 0:
                    result = self._execute_with_timeout(task)
                else:
                    result = task.handler(task, self._results)

                task.mark_success(output=result)
                self._emit("on_task_complete", task, task.result)
                return task.result

            except Exception as e:
                task.retry_count += 1

                if task.retry_count <= task.max_retries:
                    task.status = TaskStatus.RETRYING
                    if self.verbose:
                        print(f"  🔄 Retrying task '{task.name}' "
                              f"(attempt {task.retry_count}/{task.max_retries}), "
                              f"error: {e}")
                    time.sleep(task.retry_delay)
                    continue
                else:
                    task.mark_failed(str(e))
                    self._emit("on_task_fail", task, str(e))
                    return task.result

    def _execute_with_timeout(self, task: Task) -> Any:
        """Execute a task with timeout using threading."""
        result_container = {}
        error_container = {}

        def worker():
            try:
                result_container["result"] = task.handler(task, self._results)
            except Exception as e:
                error_container["error"] = e

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        thread.join(timeout=task.timeout)

        if thread.is_alive():
            task.mark_timeout()
            raise TimeoutError(f"Task '{task.name}' timed out after {task.timeout}s")

        if error_container:
            raise error_container["error"]

        return result_container.get("result")

    def execute_sequential(self) -> Dict[str, TaskResult]:
        """Execute tasks sequentially in topological order."""
        order = self.dag.topological_sort()

        for name in order:
            task = self.dag.get_task(name)
            if task.status != TaskStatus.PENDING:
                continue

            # Check if dependencies are met
            deps = self.dag.get_dependencies(name)
            failed_deps = deps.intersection(self._failed)
            if failed_deps:
                task.mark_skipped(f"Blocked by failed dependencies: {failed_deps}")
                self._failed.add(name)
                self._results[name] = task.result
                continue

            result = self._execute_single_task(task)
            self._results[name] = result

            if result.success:
                self._completed.add(name)
            else:
                self._failed.add(name)

        return self._results

    def execute_parallel(self) -> Dict[str, TaskResult]:
        """Execute all ready tasks in parallel."""
        while len(self._completed) + len(self._failed) < self.dag.task_count:
            ready = self.dag.get_ready_tasks(self._completed)
            if not ready:
                break

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {}
                for name in ready:
                    task = self.dag.get_task(name)
                    if task.status == TaskStatus.PENDING:
                        futures[executor.submit(self._execute_single_task, task)] = name

                for future in as_completed(futures):
                    name = futures[future]
                    try:
                        result = future.result()
                        self._results[name] = result
                        if result.success:
                            with self._lock:
                                self._completed.add(name)
                        else:
                            with self._lock:
                                self._failed.add(name)
                    except Exception as e:
                        with self._lock:
                            self._failed.add(name)
                            self._results[name] = TaskResult(
                                success=False, error=str(e)
                            )

        return self._results

    def execute_level_based(self) -> Dict[str, TaskResult]:
        """Execute tasks level by level (tasks at same level run in parallel)."""
        levels = self.dag.get_execution_levels()

        for level_idx, level in enumerate(levels):
            if self.verbose:
                print(f"\n  📊 Level {level_idx + 1}/{len(levels)}: "
                      f"{', '.join(level)}")

            # Filter out non-pending tasks
            pending_in_level = [
                name for name in level
                if self.dag.get_task(name).status == TaskStatus.PENDING
            ]

            if not pending_in_level:
                continue

            # Check for blocked tasks
            blocked = self.dag.get_blocked_tasks(self._failed)
            for name in pending_in_level:
                if name in blocked:
                    task = self.dag.get_task(name)
                    task.mark_skipped(f"Blocked by failed dependencies")
                    self._failed.add(name)
                    self._results[name] = task.result

            # Execute unblocked tasks
            executable = [
                name for name in pending_in_level
                if name not in blocked
            ]

            if len(executable) == 1:
                # Single task - execute directly
                task = self.dag.get_task(executable[0])
                result = self._execute_single_task(task)
                self._results[executable[0]] = result
                if result.success:
                    self._completed.add(executable[0])
                else:
                    self._failed.add(executable[0])
            elif executable:
                # Multiple tasks - execute in parallel
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    futures = {}
                    for name in executable:
                        task = self.dag.get_task(name)
                        futures[executor.submit(self._execute_single_task, task)] = name

                    for future in as_completed(futures):
                        name = futures[future]
                        try:
                            result = future.result()
                            self._results[name] = result
                            if result.success:
                                with self._lock:
                                    self._completed.add(name)
                            else:
                                with self._lock:
                                    self._failed.add(name)
                        except Exception as e:
                            with self._lock:
                                self._failed.add(name)
                                self._results[name] = TaskResult(
                                    success=False, error=str(e)
                                )

        return self._results

    def execute(self) -> Dict[str, TaskResult]:
        """Execute all tasks using the configured strategy.

        Returns:
            Dictionary mapping task names to their results.
        """
        # Validate DAG
        is_valid, errors = self.dag.validate()
        if not is_valid:
            for error in errors:
                print(f"  ❌ DAG Error: {error}")
            return self._results

        if self.verbose:
            print(f"\n  🚀 Executing workflow with strategy: {self.strategy}")
            print(f"  📋 Total tasks: {self.dag.task_count}")

        if self.strategy == ExecutionStrategy.SEQUENTIAL:
            self.execute_sequential()
        elif self.strategy == ExecutionStrategy.PARALLEL:
            self.execute_parallel()
        elif self.strategy == ExecutionStrategy.LEVEL_BASED:
            self.execute_level_based()
        else:
            raise ValueError(f"Unknown execution strategy: {self.strategy}")

        self._emit("on_workflow_complete", self._results)
        return self._results

    @property
    def completed_count(self) -> int:
        return len(self._completed)

    @property
    def failed_count(self) -> int:
        return len(self._failed)

    @property
    def success_rate(self) -> float:
        total = self.completed_count + self.failed_count
        return (self.completed_count / total * 100) if total > 0 else 0.0
