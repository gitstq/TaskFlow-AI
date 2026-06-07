"""
DAG Engine - Directed Acyclic Graph for task dependency resolution.
DAG引擎 - 基于有向无环图的任务依赖解析引擎。
"""

from collections import defaultdict, deque
from typing import Dict, List, Optional, Set, Tuple

from .task import Task, TaskStatus


class CycleDetectedError(Exception):
    """Raised when a cycle is detected in the task dependency graph."""
    pass


class DAGError(Exception):
    """Raised for general DAG-related errors."""
    pass


class DAGEngine:
    """Directed Acyclic Graph engine for task dependency management.

    Handles topological sorting, cycle detection, and execution order
    determination for tasks with complex dependency relationships.
    """

    def __init__(self):
        self._graph: Dict[str, Set[str]] = defaultdict(set)  # task -> dependents
        self._reverse: Dict[str, Set[str]] = defaultdict(set)  # task -> dependencies
        self._tasks: Dict[str, Task] = {}

    @property
    def task_count(self) -> int:
        return len(self._tasks)

    @property
    def task_names(self) -> List[str]:
        return list(self._tasks.keys())

    def add_task(self, task: Task) -> None:
        """Add a task to the DAG.

        Args:
            task: Task object to add

        Raises:
            DAGError: If a task with the same name already exists
        """
        if task.name in self._tasks:
            raise DAGError(f"Task '{task.name}' already exists in the DAG")

        self._tasks[task.name] = task
        self._graph[task.name] = set()
        self._reverse[task.name] = set()

        for dep in task.dependencies:
            if dep in self._tasks:
                self._graph[dep].add(task.name)
                self._reverse[task.name].add(dep)
            else:
                # Store dependency edge even if dep not yet added
                self._reverse[task.name].add(dep)

    def remove_task(self, name: str) -> None:
        """Remove a task and all its edges from the DAG."""
        if name not in self._tasks:
            return

        # Remove edges
        for dependent in self._graph.get(name, set()):
            self._reverse[dependent].discard(name)
        for dependency in self._reverse.get(name, set()):
            self._graph[dependency].discard(name)

        del self._tasks[name]
        self._graph.pop(name, None)
        self._reverse.pop(name, None)

    def get_task(self, name: str) -> Optional[Task]:
        """Get a task by name."""
        return self._tasks.get(name)

    def get_dependencies(self, name: str) -> Set[str]:
        """Get all direct dependencies of a task."""
        return self._reverse.get(name, set()).copy()

    def get_dependents(self, name: str) -> Set[str]:
        """Get all tasks that depend on this task."""
        return self._graph.get(name, set()).copy()

    def get_all_dependencies(self, name: str) -> Set[str]:
        """Get all transitive dependencies of a task."""
        visited = set()
        queue = deque(self._reverse.get(name, set()))

        while queue:
            dep = queue.popleft()
            if dep not in visited:
                visited.add(dep)
                queue.extend(self._reverse.get(dep, set()))

        return visited

    def detect_cycle(self) -> Optional[List[str]]:
        """Detect if there's a cycle in the DAG.

        Returns:
            List of task names forming the cycle, or None if no cycle exists.
        """
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {name: WHITE for name in self._tasks}
        parent = {}

        def dfs(node: str) -> Optional[List[str]]:
            color[node] = GRAY
            for neighbor in self._graph.get(node, set()):
                if color[neighbor] == GRAY:
                    # Found cycle - reconstruct path
                    cycle = [neighbor, node]
                    current = node
                    while current != neighbor:
                        current = parent.get(current)
                        if current is None:
                            break
                        cycle.append(current)
                    cycle.reverse()
                    return cycle
                if color[neighbor] == WHITE:
                    parent[neighbor] = node
                    result = dfs(neighbor)
                    if result:
                        return result
            color[node] = BLACK
            return None

        for name in self._tasks:
            if color[name] == WHITE:
                result = dfs(name)
                if result:
                    return result

        return None

    def topological_sort(self) -> List[str]:
        """Perform topological sort using Kahn's algorithm.

        Returns:
            List of task names in execution order.

        Raises:
            CycleDetectedError: If the DAG contains a cycle.
        """
        cycle = self.detect_cycle()
        if cycle:
            raise CycleDetectedError(
                f"Cycle detected: {' -> '.join(cycle)}"
            )

        in_degree = {name: 0 for name in self._tasks}
        for name in self._tasks:
            for dep in self._graph.get(name, set()):
                in_degree[dep] = in_degree.get(dep, 0)

        # Calculate in-degrees
        for name in self._tasks:
            in_degree[name] = len(self._reverse.get(name, set()))

        queue = deque()
        for name, degree in in_degree.items():
            if degree == 0:
                queue.append(name)

        # Sort by priority within same level
        result = []
        while queue:
            # Sort current level by priority
            level = sorted(queue, key=lambda n: self._tasks[n].priority.value)
            queue = deque()

            for name in level:
                result.append(name)
                for dependent in self._graph.get(name, set()):
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)

        return result

    def get_execution_levels(self) -> List[List[str]]:
        """Get tasks grouped by execution level (tasks that can run in parallel).

        Returns:
            List of levels, where each level is a list of task names
            that can be executed concurrently.
        """
        cycle = self.detect_cycle()
        if cycle:
            raise CycleDetectedError(
                f"Cycle detected: {' -> '.join(cycle)}"
            )

        in_degree = {name: len(self._reverse.get(name, set())) for name in self._tasks}
        levels = []
        current_level = [name for name, degree in in_degree.items() if degree == 0]

        while current_level:
            levels.append(sorted(current_level, key=lambda n: self._tasks[n].priority.value))
            next_level = []
            for name in current_level:
                for dependent in self._graph.get(name, set()):
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        next_level.append(dependent)
            current_level = next_level

        return levels

    def get_ready_tasks(self, completed: Set[str]) -> List[str]:
        """Get tasks that are ready to execute based on completed tasks.

        Args:
            completed: Set of completed task names.

        Returns:
            List of task names that can be executed next.
        """
        ready = []
        for name, task in self._tasks.items():
            if task.status != TaskStatus.PENDING:
                continue
            deps = self._reverse.get(name, set())
            if deps.issubset(completed):
                ready.append(name)

        return sorted(ready, key=lambda n: self._tasks[n].priority.value)

    def get_blocked_tasks(self, failed: Set[str]) -> Set[str]:
        """Get tasks that are blocked due to failed dependencies.

        Args:
            failed: Set of failed task names.

        Returns:
            Set of task names that cannot be executed.
        """
        blocked = set()
        for name in self._tasks:
            deps = self._reverse.get(name, set())
            if deps.intersection(failed):
                blocked.add(name)
        return blocked

    def validate(self) -> Tuple[bool, List[str]]:
        """Validate the DAG structure.

        Returns:
            Tuple of (is_valid, list_of_error_messages).
        """
        errors = []

        # Check for cycles
        cycle = self.detect_cycle()
        if cycle:
            errors.append(f"Cycle detected: {' -> '.join(cycle)}")

        # Check for missing dependencies
        for name, task in self._tasks.items():
            for dep in task.dependencies:
                if dep not in self._tasks:
                    errors.append(f"Task '{name}' has unknown dependency '{dep}'")

        # Check for orphan tasks (no deps and no dependents)
        for name in self._tasks:
            if not self._graph.get(name) and not self._reverse.get(name):
                pass  # Orphan tasks are valid (single task workflows)

        return len(errors) == 0, errors

    def to_dict(self) -> Dict:
        """Export DAG structure as dictionary."""
        return {
            "tasks": {name: task.to_dict() for name, task in self._tasks.items()},
            "edges": [
                {"from": dep, "to": name}
                for name in self._tasks
                for dep in self._reverse.get(name, set())
            ],
            "execution_order": self.topological_sort(),
            "execution_levels": self.get_execution_levels(),
        }

    def __repr__(self) -> str:
        return f"DAGEngine(tasks={self.task_count})"
