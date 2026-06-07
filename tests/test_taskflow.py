"""
TaskFlow-AI Test Suite
Comprehensive tests for core modules.
"""

import sys
import os
import time
import json
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from taskflow_ai.task import Task, TaskStatus, TaskPriority, TaskResult
from taskflow_ai.dag import DAGEngine, CycleDetectedError
from taskflow_ai.executor import TaskExecutor, ExecutionStrategy
from taskflow_ai.workflow import Workflow


class TestTask(unittest.TestCase):
    """Tests for Task model."""

    def test_task_creation(self):
        task = Task(name="test", description="Test task")
        self.assertEqual(task.name, "test")
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertEqual(task.retry_count, 0)

    def test_task_status_transitions(self):
        task = Task(name="test")
        task.mark_running()
        self.assertEqual(task.status, TaskStatus.RUNNING)
        self.assertIsNotNone(task.start_time)

        task.mark_success(output={"key": "value"})
        self.assertEqual(task.status, TaskStatus.SUCCESS)
        self.assertIsNotNone(task.end_time)
        self.assertTrue(task.result.success)
        self.assertGreater(task.duration_ms, 0)

    def test_task_failure(self):
        task = Task(name="test")
        task.mark_running()
        task.mark_failed("Something went wrong")
        self.assertEqual(task.status, TaskStatus.FAILED)
        self.assertFalse(task.result.success)
        self.assertEqual(task.result.error, "Something went wrong")

    def test_task_timeout(self):
        task = Task(name="test", timeout=5)
        task.mark_running()
        task.mark_timeout()
        self.assertEqual(task.status, TaskStatus.TIMEOUT)

    def test_task_skip(self):
        task = Task(name="test")
        task.mark_skipped("Reason")
        self.assertEqual(task.status, TaskStatus.SKIPPED)

    def test_task_reset(self):
        task = Task(name="test")
        task.mark_running()
        task.mark_success()
        task.reset()
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertIsNone(task.result)

    def test_task_serialization(self):
        task = Task(
            name="test",
            description="Test",
            dependencies=["dep1"],
            priority=TaskPriority.HIGH,
            timeout=10,
            max_retries=3,
            tags=["test"],
        )
        d = task.to_dict()
        self.assertEqual(d["name"], "test")
        self.assertEqual(d["priority"], "HIGH")
        self.assertEqual(d["dependencies"], ["dep1"])

    def test_task_result_serialization(self):
        result = TaskResult(
            success=True,
            output={"data": 42},
            metrics={"calls": 5},
            duration_ms=100.5,
        )
        d = result.to_dict()
        self.assertTrue(d["success"])
        self.assertEqual(d["metrics"]["calls"], 5)

        j = result.to_json()
        parsed = json.loads(j)
        self.assertEqual(parsed["output"]["data"], 42)

    def test_task_priority_colors(self):
        self.assertIsNotNone(TaskPriority.CRITICAL.color_code())
        self.assertEqual(TaskPriority.HIGH.label(), "HIGH")

    def test_task_status_icons(self):
        self.assertEqual(TaskStatus.SUCCESS.icon(), "✅")
        self.assertEqual(TaskStatus.FAILED.icon(), "❌")


class TestDAG(unittest.TestCase):
    """Tests for DAG engine."""

    def test_add_task(self):
        dag = DAGEngine()
        task = Task(name="a")
        dag.add_task(task)
        self.assertEqual(dag.task_count, 1)
        self.assertIsNotNone(dag.get_task("a"))

    def test_add_duplicate_task(self):
        dag = DAGEngine()
        dag.add_task(Task(name="a"))
        with self.assertRaises(Exception):
            dag.add_task(Task(name="a"))

    def test_dependency_edges(self):
        dag = DAGEngine()
        dag.add_task(Task(name="a"))
        dag.add_task(Task(name="b", dependencies=["a"]))
        self.assertEqual(dag.get_dependencies("b"), {"a"})
        self.assertEqual(dag.get_dependents("a"), {"b"})

    def test_topological_sort_simple(self):
        dag = DAGEngine()
        dag.add_task(Task(name="a"))
        dag.add_task(Task(name="b", dependencies=["a"]))
        dag.add_task(Task(name="c", dependencies=["b"]))
        order = dag.topological_sort()
        self.assertTrue(order.index("a") < order.index("b"))
        self.assertTrue(order.index("b") < order.index("c"))

    def test_topological_sort_parallel(self):
        dag = DAGEngine()
        dag.add_task(Task(name="a"))
        dag.add_task(Task(name="b", dependencies=["a"]))
        dag.add_task(Task(name="c", dependencies=["a"]))
        order = dag.topological_sort()
        self.assertEqual(order[0], "a")

    def test_cycle_detection(self):
        dag = DAGEngine()
        dag.add_task(Task(name="a"))
        dag.add_task(Task(name="b", dependencies=["a"]))
        dag.add_task(Task(name="c", dependencies=["b"]))
        # Now add a cycle: a depends on c
        dag._reverse["a"].add("c")
        dag._graph["c"].add("a")
        cycle = dag.detect_cycle()
        self.assertIsNotNone(cycle)

        with self.assertRaises(CycleDetectedError):
            dag.topological_sort()

    def test_execution_levels(self):
        dag = DAGEngine()
        dag.add_task(Task(name="a"))
        dag.add_task(Task(name="b", dependencies=["a"]))
        dag.add_task(Task(name="c", dependencies=["a"]))
        dag.add_task(Task(name="d", dependencies=["b", "c"]))
        levels = dag.get_execution_levels()
        self.assertEqual(len(levels), 3)
        self.assertEqual(levels[0], ["a"])
        self.assertEqual(set(levels[1]), {"b", "c"})
        self.assertEqual(levels[2], ["d"])

    def test_remove_task(self):
        dag = DAGEngine()
        dag.add_task(Task(name="a"))
        dag.add_task(Task(name="b", dependencies=["a"]))
        dag.remove_task("b")
        self.assertEqual(dag.task_count, 1)
        self.assertIsNone(dag.get_task("b"))

    def test_validate(self):
        dag = DAGEngine()
        dag.add_task(Task(name="a"))
        dag.add_task(Task(name="b", dependencies=["a"]))
        is_valid, errors = dag.validate()
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_get_ready_tasks(self):
        dag = DAGEngine()
        dag.add_task(Task(name="a"))
        dag.add_task(Task(name="b", dependencies=["a"]))
        dag.add_task(Task(name="c", dependencies=["a"]))

        ready = dag.get_ready_tasks(set())
        self.assertIn("a", ready)
        self.assertNotIn("b", ready)

        ready = dag.get_ready_tasks({"a"})
        self.assertIn("b", ready)
        self.assertIn("c", ready)

    def test_get_blocked_tasks(self):
        dag = DAGEngine()
        dag.add_task(Task(name="a"))
        dag.add_task(Task(name="b", dependencies=["a"]))
        dag.add_task(Task(name="c", dependencies=["b"]))

        blocked = dag.get_blocked_tasks({"a"})
        self.assertIn("b", blocked)
        # c depends on b (not directly on a), so it's not in direct blocked set
        # unless we also fail b
        blocked_all = dag.get_blocked_tasks({"a", "b"})
        self.assertIn("c", blocked_all)

    def test_dag_to_dict(self):
        dag = DAGEngine()
        dag.add_task(Task(name="a"))
        dag.add_task(Task(name="b", dependencies=["a"]))
        d = dag.to_dict()
        self.assertIn("tasks", d)
        self.assertIn("edges", d)
        self.assertIn("execution_order", d)


class TestExecutor(unittest.TestCase):
    """Tests for TaskExecutor."""

    def _create_simple_workflow(self):
        dag = DAGEngine()
        dag.add_task(Task(
            name="step1",
            handler=lambda task, results: {"step": 1, "data": "hello"},
        ))
        dag.add_task(Task(
            name="step2",
            handler=lambda task, results: {"step": 2, "prev": results["step1"].output.get("data") if results.get("step1") else None},
            dependencies=["step1"],
        ))
        return dag

    def test_sequential_execution(self):
        dag = self._create_simple_workflow()
        executor = TaskExecutor(dag, strategy=ExecutionStrategy.SEQUENTIAL, verbose=False)
        results = executor.execute()
        self.assertEqual(len(results), 2)
        self.assertTrue(results["step1"].success)
        self.assertTrue(results["step2"].success)
        self.assertEqual(results["step2"].output.get("prev"), "hello")

    def test_level_based_execution(self):
        dag = self._create_simple_workflow()
        executor = TaskExecutor(dag, strategy=ExecutionStrategy.LEVEL_BASED, verbose=False)
        results = executor.execute()
        self.assertTrue(results["step1"].success)
        self.assertTrue(results["step2"].success)

    def test_parallel_execution(self):
        dag = DAGEngine()
        dag.add_task(Task(
            name="a",
            handler=lambda task, results: {"value": "a"},
        ))
        dag.add_task(Task(
            name="b",
            handler=lambda task, results: {"value": "b"},
        ))
        executor = TaskExecutor(dag, strategy=ExecutionStrategy.PARALLEL, verbose=False)
        results = executor.execute()
        self.assertTrue(results["a"].success)
        self.assertTrue(results["b"].success)

    def test_retry_on_failure(self):
        call_count = {"n": 0}

        def failing_handler(task, results):
            call_count["n"] += 1
            if call_count["n"] < 3:
                raise ValueError("Not yet!")
            return {"finally": "success"}

        dag = DAGEngine()
        dag.add_task(Task(
            name="retry_task",
            handler=failing_handler,
            max_retries=3,
            retry_delay=0.01,
        ))
        executor = TaskExecutor(dag, strategy=ExecutionStrategy.SEQUENTIAL, verbose=False)
        results = executor.execute()
        self.assertTrue(results["retry_task"].success)
        self.assertEqual(results["retry_task"].retries_used, 2)

    def test_timeout_handling(self):
        def slow_handler(task, results):
            time.sleep(10)
            return "done"

        dag = DAGEngine()
        dag.add_task(Task(
            name="slow",
            handler=slow_handler,
            timeout=0.5,
        ))
        executor = TaskExecutor(dag, strategy=ExecutionStrategy.SEQUENTIAL, verbose=False)
        results = executor.execute()
        self.assertFalse(results["slow"].success)
        self.assertIn("timed out", results["slow"].error)

    def test_conditional_execution(self):
        dag = DAGEngine()
        dag.add_task(Task(
            name="conditional",
            handler=lambda task, results: "executed",
            condition=lambda task, results: False,
        ))
        executor = TaskExecutor(dag, strategy=ExecutionStrategy.SEQUENTIAL, verbose=False)
        results = executor.execute()
        self.assertTrue(results["conditional"].success)
        self.assertEqual(results["conditional"].output, "Condition not met")

    def test_failure_propagation(self):
        dag = DAGEngine()
        dag.add_task(Task(
            name="fail",
            handler=lambda task, results: (_ for _ in ()).throw(ValueError("Boom")),
        ))
        dag.add_task(Task(
            name="dependent",
            handler=lambda task, results: "should not run",
            dependencies=["fail"],
        ))
        executor = TaskExecutor(dag, strategy=ExecutionStrategy.SEQUENTIAL, verbose=False)
        results = executor.execute()
        self.assertFalse(results["fail"].success)
        # Dependent should be skipped
        self.assertIn("Blocked by failed dependencies", results["dependent"].output)

    def test_no_handler_skip(self):
        dag = DAGEngine()
        dag.add_task(Task(name="no_handler"))
        executor = TaskExecutor(dag, strategy=ExecutionStrategy.SEQUENTIAL, verbose=False)
        results = executor.execute()
        self.assertTrue(results["no_handler"].success)
        self.assertEqual(results["no_handler"].output, "No handler defined")

    def test_callbacks(self):
        events = []

        def on_start(task):
            events.append(("start", task.name))

        def on_complete(task, result):
            events.append(("complete", task.name))

        dag = DAGEngine()
        dag.add_task(Task(
            name="cb_task",
            handler=lambda task, results: "done",
        ))
        executor = TaskExecutor(dag, strategy=ExecutionStrategy.SEQUENTIAL, verbose=False)
        executor.on("on_task_start", on_start)
        executor.on("on_task_complete", on_complete)
        executor.execute()

        self.assertEqual(len(events), 2)
        self.assertEqual(events[0], ("start", "cb_task"))
        self.assertEqual(events[1], ("complete", "cb_task"))


class TestWorkflow(unittest.TestCase):
    """Tests for Workflow builder."""

    def test_workflow_creation(self):
        wf = Workflow("test", "Test workflow")
        self.assertEqual(wf.name, "test")

    def test_add_tasks(self):
        wf = Workflow("test")
        wf.add_task("a", "Task A", handler=lambda t, r: "a")
        wf.add_task("b", "Task B", handler=lambda t, r: "b", deps=["a"])
        self.assertEqual(wf.dag.task_count, 2)

    def test_workflow_run(self):
        wf = Workflow("test")
        wf.add_task("a", handler=lambda t, r: {"val": 1})
        wf.add_task("b", handler=lambda t, r: {"val": 2}, deps=["a"])
        wf.config(verbose=False)
        results = wf.run()
        self.assertTrue(results["success"])
        self.assertEqual(results["completed"], 2)

    def test_workflow_serialization(self):
        wf = Workflow("test", "Test")
        wf.add_task("a", "Task A")
        d = wf.to_dict()
        self.assertEqual(d["name"], "test")
        j = wf.to_json()
        parsed = json.loads(j)
        self.assertEqual(parsed["name"], "test")

    def test_workflow_config_chain(self):
        wf = Workflow("test")
        result = wf.config(strategy="sequential", max_workers=2, verbose=False)
        self.assertIs(result, wf)

    def test_workflow_remove_task(self):
        wf = Workflow("test")
        wf.add_task("a")
        wf.add_task("b")
        wf.remove_task("a")
        self.assertEqual(wf.dag.task_count, 1)

    def test_workflow_export(self):
        import tempfile
        wf = Workflow("export-test")
        wf.add_task("a", handler=lambda t, r: "done")
        wf.config(verbose=False)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=True, mode="w") as f:
            filepath = f.name

        wf.run_and_export(filepath)
        self.assertTrue(os.path.exists(filepath))
        with open(filepath) as f:
            data = json.load(f)
        self.assertEqual(data["workflow"], "export-test")
        os.unlink(filepath)


class TestIntegration(unittest.TestCase):
    """Integration tests for complex scenarios."""

    def test_complex_diamond_workflow(self):
        """Test diamond dependency pattern: A -> B, A -> C, B -> D, C -> D"""
        wf = Workflow("diamond", "Diamond Dependency Test")
        wf.config(verbose=False)

        wf.add_task("a", handler=lambda t, r: {"a": True})
        wf.add_task("b", handler=lambda t, r: {"b": True}, deps=["a"])
        wf.add_task("c", handler=lambda t, r: {"c": True}, deps=["a"])
        wf.add_task("d", handler=lambda t, r: {
            "a_in": "a" in r, "b_in": "b" in r, "c_in": "c" in r
        }, deps=["b", "c"])

        results = wf.run()
        self.assertTrue(results["success"])
        self.assertEqual(results["completed"], 4)

    def test_priority_ordering(self):
        """Test that higher priority tasks execute first within same level."""
        wf = Workflow("priority-test")
        wf.config(strategy="level_based", verbose=False)

        execution_order = []

        def make_handler(name):
            def handler(t, r):
                execution_order.append(name)
                return name
            return handler

        wf.add_task("low", handler=make_handler("low"), priority="low")
        wf.add_task("critical", handler=make_handler("critical"), priority="critical")
        wf.add_task("high", handler=make_handler("high"), priority="high")

        wf.run()
        # Critical should be first
        self.assertEqual(execution_order[0], "critical")

    def test_large_workflow(self):
        """Test with many tasks."""
        wf = Workflow("large", "Large workflow test")
        wf.config(verbose=False)

        # Create a chain of 20 tasks
        prev = None
        for i in range(20):
            name = f"task_{i}"
            deps = [prev] if prev else []
            wf.add_task(name, handler=lambda t, r: {"i": t.name}, deps=deps)
            prev = name

        results = wf.run()
        self.assertTrue(results["success"])
        self.assertEqual(results["completed"], 20)

    def test_mixed_success_failure(self):
        """Test workflow with mixed success and failure."""
        wf = Workflow("mixed", "Mixed results test")
        wf.config(strategy="sequential", verbose=False)

        wf.add_task("ok", handler=lambda t, r: "ok")
        wf.add_task("fail", handler=lambda t, r: (_ for _ in ()).throw(ValueError("fail")))
        wf.add_task("after_fail", handler=lambda t, r: "should be skipped", deps=["fail"])
        wf.add_task("independent", handler=lambda t, r: "independent")

        results = wf.run()
        self.assertFalse(results["success"])
        self.assertEqual(results["completed"], 2)  # ok + independent
        self.assertEqual(results["failed"], 2)  # fail + after_fail


if __name__ == "__main__":
    unittest.main(verbosity=2)
