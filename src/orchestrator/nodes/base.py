"""
Base node interface
Dependency Inversion Principle: Depend on abstractions, not implementations
"""

from abc import ABC, abstractmethod
from typing import Protocol
from src.orchestrator.state import PolygonGeneratorState


class NodeFunction(Protocol):
    """
    Protocol for node functions

    All nodes must follow this interface:
    - Accept PolygonGeneratorState
    - Return dict with state updates
    """

    def __call__(self, state: PolygonGeneratorState) -> dict:
        """
        Execute node logic

        Args:
            state: Current workflow state

        Returns:
            Dict with state updates (will be merged into state)
        """
        ...


class BaseNode(ABC):
    """
    Abstract base class for workflow nodes
    """

    @abstractmethod
    def execute(self, state: PolygonGeneratorState) -> dict:
        """
        Execute node logic

        Args:
            state: Current workflow state

        Returns:
            Dict with state updates

        Raises:
            Exception: If node execution fails
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Node name for logging and identification"""
        pass

    def log(self, message: str):
        """Helper for consistent logging"""
        print(f"{self.name}: {message}")
