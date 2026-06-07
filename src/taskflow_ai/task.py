"""
Task model - Core data structures for task definition and state management.
任务模型 - 任务定义与状态管理的核心数据结构。
"""

import time
import json
import uuid
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


class TaskStatus(Enum):
    """Task execution status enumeration."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

    def color_code(self) -> str:
        """Return ANSI color code for terminal display."""
        colors = {
            TaskStatus.PENDING: "\033[90m",      # Gray
            TaskStatus.QUEUED: "\033[96m",        # Cyan
            TaskStatus.RUNNING: "\033[93m",       # Yellow
            TaskStatus.SUCCESS: "\033[92m",      # Green
            TaskStatus.FAILED: "\033[91m",        # Red
            TaskStatus.SKIPPED: "\033[90m",      # Gray
            TaskStatus.RETRYING: "\033[95m",      # Magenta
            TaskStatus.CANCELLED: "\033[90m",    # Gray
            TaskStatus.TIMEOUT: "\033[91m",       # Red
        }
        return colors.get(self, "\033[0m")

    def icon(self) -> str:
        """Return icon for display."""
        icons = {
            TaskStatus.PENDING: "⏳",
            TaskStatus.QUEUED: "📥",
            TaskStatus.RUNNING: "⚡",
            TaskStatus.SUCCESS: "✅",
            TaskStatus.FAILED: "❌",
            TaskStatus.SKIPPED: "⏭️",
            TaskStatus.RETRYING: "🔄",
            TaskStatus.CANCELLED: "🚫",
            TaskStatus.TIMEOUT: "⏰",
        }
        return icons.get(self, "❓")


class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3

    def color_code(self) -> str:
        colors = {
            TaskPriority.CRITICAL: "\033[91m",
            TaskPriority.HIGH: "\033[93m",
            TaskPriority.MEDIUM: "\033[96m",
            TaskPriority.LOW: "\033[90m",
        }
        return colors.get(self, "\033[0m")

    def label(self) -> str:
        labels = {
            TaskPriority.CRITICAL: "CRITICAL",
            TaskPriority.HIGH: "HIGH",
            TaskPriority.MEDIUM: "MEDIUM",
            TaskPriority.LOW: "LOW",
        }
        return labels.get(self, "UNKNOWN")


@dataclass
class TaskResult:
    """Result of a task execution."""
    success: bool = False
    output: Any = None
    error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    duration_ms: float = 0.0
    retries_used: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)


@dataclass
class Task:
    """A single task in the workflow.

    Attributes:
        name: Unique task identifier
        description: Human-readable task description
        handler: Callable that executes the task logic
        dependencies: List of task names this task depends on
        priority: Task execution priority
        timeout: Maximum execution time in seconds (0 = no timeout)
        max_retries: Maximum retry attempts on failure
        retry_delay: Delay between retries in seconds
        condition: Optional condition function - task runs only if True
        tags: Optional tags for categorization
        metadata: Optional metadata dictionary
    """
    name: str
    description: str = ""
    handler: Optional[callable] = None
    dependencies: List[str] = field(default_factory=list)
    priority: TaskPriority = TaskPriority.MEDIUM
    timeout: float = 0.0
    max_retries: int = 0
    retry_delay: float = 1.0
    condition: Optional[callable] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Runtime state (not serialized)
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[TaskResult] = None
    retry_count: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize task to dictionary (excluding runtime state and handler)."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "dependencies": self.dependencies,
            "priority": self.priority.label(),
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "tags": self.tags,
            "metadata": self.metadata,
            "status": self.status.value,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @property
    def duration_ms(self) -> float:
        """Calculate task execution duration in milliseconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0.0

    def reset(self) -> None:
        """Reset task to initial state for re-execution."""
        self.status = TaskStatus.PENDING
        self.result = None
        self.retry_count = 0
        self.start_time = None
        self.end_time = None

    def mark_running(self) -> None:
        """Mark task as running."""
        self.status = TaskStatus.RUNNING
        self.start_time = time.time()

    def mark_success(self, output: Any = None, metrics: Dict = None) -> None:
        """Mark task as successfully completed."""
        self.end_time = time.time()
        self.status = TaskStatus.SUCCESS
        self.result = TaskResult(
            success=True,
            output=output,
            metrics=metrics or {},
            duration_ms=self.duration_ms,
            retries_used=self.retry_count,
        )

    def mark_failed(self, error: str = None) -> None:
        """Mark task as failed."""
        self.end_time = time.time()
        self.status = TaskStatus.FAILED
        self.result = TaskResult(
            success=False,
            error=error,
            duration_ms=self.duration_ms,
            retries_used=self.retry_count,
        )

    def mark_timeout(self) -> None:
        """Mark task as timed out."""
        self.end_time = time.time()
        self.status = TaskStatus.TIMEOUT
        self.result = TaskResult(
            success=False,
            error="Task execution timed out",
            duration_ms=self.duration_ms,
            retries_used=self.retry_count,
        )

    def mark_skipped(self, reason: str = "Condition not met") -> None:
        """Mark task as skipped."""
        self.status = TaskStatus.SKIPPED
        self.result = TaskResult(
            success=True,
            output=reason,
            duration_ms=0,
        )

    def __repr__(self) -> str:
        return f"Task(name={self.name!r}, status={self.status.value}, priority={self.priority.label()})"
