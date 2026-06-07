"""
TaskFlow-AI - Lightweight AI Agent Task Flow Orchestration Engine
轻量级AI Agent任务流编排引擎

A zero-dependency, pure Python tool for defining, orchestrating, and
monitoring complex AI agent task workflows with DAG-based dependency
resolution, multiple execution strategies, and rich terminal UI.
"""

import sys
import os

# Add src to path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from taskflow_ai import __version__

__all__ = ["__version__"]
