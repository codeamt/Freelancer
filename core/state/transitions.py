"""
Transitions and conditions for state machine flow control.

This module provides transition logic and condition checking.
"""

from typing import Callable, Optional, Any
from dataclasses import dataclass
from .state import State


@dataclass
class TransitionCondition:
    """Represents a condition for transitioning between actions."""
    func: Callable[[State, Any], bool]
    name: str
    
    async def evaluate(self, state: State, result: Any) -> bool:
        """Evaluate the condition."""
        return self.func(state, result)


class Transition:
    """
    Represents a transition from one action to another.
    
    Transitions can be conditional or unconditional (default).
    """
    
    def __init__(
        self, 
        target: str, 
        condition: Optional[Callable[[State, Any], bool]] = None
    ):
        """
        Initialize transition.
        
        Args:
            target: Target action name
            condition: Optional condition function that returns bool
        """
        self.target = target
        self.condition = condition
    
    async def should_transition(self, state: State, result: Any) -> bool:
        """
        Check if transition should occur.
        
        Args:
            state: Current state
            result: Result from previous action
            
        Returns:
            True if transition should occur
        """
        if self.condition is None:
            return True  # Default/unconditional transition
        
        try:
            return self.condition(state, result)
        except Exception as e:
            # If condition fails, don't transition
            return False
    
    def __repr__(self) -> str:
        cond_name = self.condition.__name__ if self.condition else "default"
        return f"Transition(target='{self.target}', condition={cond_name})"


# ============================================================================
# Condition Helper Functions
# ============================================================================

def condition(func: Callable[[State, Any], bool]) -> Callable:
    """
    Decorator for condition functions.
    
    Makes condition functions more readable.
    
    Example:
        @condition
        def is_valid(state, result):
            return result.success and state.get("validated")
    """
    func.__is_condition__ = True
    return func


def default() -> None:
    """
    Placeholder for default transitions (always transition).
    
    Usage:
        .with_transitions(
            ("action_a", "action_b", default())
        )
    """
    return None


# ============================================================================
# Common Site Management Conditions
# ============================================================================

@condition
def on_success(state: State, result: Any) -> bool:
    """Transition only if action succeeded."""
    return hasattr(result, 'success') and result.success


@condition
def on_failure(state: State, result: Any) -> bool:
    """Transition only if action failed."""
    return hasattr(result, 'success') and not result.success


@condition
def has_validation_errors(state: State, result: Any) -> bool:
    """Transition if validation errors exist."""
    errors = state.get("validation_errors", [])
    return len(errors) > 0


@condition
def no_validation_errors(state: State, result: Any) -> bool:
    """Transition if no validation errors."""
    errors = state.get("validation_errors", [])
    return len(errors) == 0


@condition
def is_published(state: State, result: Any) -> bool:
    """Transition if site is published."""
    return state.get("status") == "published"


@condition
def is_draft(state: State, result: Any) -> bool:
    """Transition if site is draft."""
    return state.get("status") == "draft"


@condition
def has_sections(state: State, result: Any) -> bool:
    """Transition if site has sections."""
    site_graph = state.get("site_graph", {})
    return len(site_graph.get("sections", [])) > 0


@condition
def no_sections(state: State, result: Any) -> bool:
    """Transition if site has no sections."""
    site_graph = state.get("site_graph", {})
    return len(site_graph.get("sections", [])) == 0


def state_equals(key: str, value: Any) -> Callable[[State, Any], bool]:
    """
    Create condition that checks if state key equals value.
    
    Args:
        key: State key to check
        value: Value to compare against
        
    Returns:
        Condition function
    """
    @condition
    def check(state: State, result: Any) -> bool:
        return state.get(key) == value
    
    check.__name__ = f"state[{key}]=={value}"
    return check


def state_contains(key: str, value: Any) -> Callable[[State, Any], bool]:
    """
    Create condition that checks if state list/dict contains value.
    
    Args:
        key: State key to check (must be list or dict)
        value: Value to check for
        
    Returns:
        Condition function
    """
    @condition
    def check(state: State, result: Any) -> bool:
        container = state.get(key)
        if container is None:
            return False
        return value in container
    
    check.__name__ = f"{value} in state[{key}]"
    return check


def result_data_equals(key: str, value: Any) -> Callable[[State, Any], bool]:
    """
    Create condition that checks if result data key equals value.
    
    Args:
        key: Result data key to check
        value: Value to compare against
        
    Returns:
        Condition function
    """
    @condition
    def check(state: State, result: Any) -> bool:
        if not hasattr(result, 'data') or result.data is None:
            return False
        return result.data.get(key) == value
    
    check.__name__ = f"result.data[{key}]=={value}"
    return check


def all_conditions(*conditions: Callable) -> Callable[[State, Any], bool]:
    """
    Combine multiple conditions with AND logic.
    
    Args:
        *conditions: Condition functions to combine
        
    Returns:
        Combined condition function
    """
    @condition
    def combined(state: State, result: Any) -> bool:
        return all(cond(state, result) for cond in conditions)
    
    cond_names = [c.__name__ for c in conditions]
    combined.__name__ = f"all({', '.join(cond_names)})"
    return combined


def any_condition(*conditions: Callable) -> Callable[[State, Any], bool]:
    """
    Combine multiple conditions with OR logic.
    
    Args:
        *conditions: Condition functions to combine
        
    Returns:
        Combined condition function
    """
    @condition
    def combined(state: State, result: Any) -> bool:
        return any(cond(state, result) for cond in conditions)
    
    cond_names = [c.__name__ for c in conditions]
    combined.__name__ = f"any({', '.join(cond_names)})"
    return combined


def not_condition(condition_func: Callable) -> Callable[[State, Any], bool]:
    """
    Negate a condition.
    
    Args:
        condition_func: Condition to negate
        
    Returns:
        Negated condition function
    """
    @condition
    def negated(state: State, result: Any) -> bool:
        return not condition_func(state, result)
    
    negated.__name__ = f"not({condition_func.__name__})"
    return negated


# ============================================================================
# Expression-based Conditions
# ============================================================================

class Expression:
    """
    Expression-based condition builder.
    
    Provides a more readable way to create complex conditions.
    
    Example:
        expr = Expression()
        condition = expr["status"].equals("published") & expr["sections"].length() > 0
    """
    
    def __init__(self):
        self._conditions = []
    
    def __getitem__(self, key: str) -> "ExpressionBuilder":
        """Start building expression for a state key."""
        return ExpressionBuilder(key)
    
    def build(self) -> Callable[[State, Any], bool]:
        """Build the final condition function."""
        @condition
        def evaluate(state: State, result: Any) -> bool:
            return all(cond(state, result) for cond in self._conditions)
        return evaluate


class ExpressionBuilder:
    """Builder for expression-based conditions."""
    
    def __init__(self, key: str):
        self.key = key
    
    def equals(self, value: Any) -> Callable[[State, Any], bool]:
        """Check if state[key] equals value."""
        return state_equals(self.key, value)
    
    def contains(self, value: Any) -> Callable[[State, Any], bool]:
        """Check if value in state[key]."""
        return state_contains(self.key, value)
    
    def length(self) -> "LengthExpressionBuilder":
        """Check length of state[key]."""
        return LengthExpressionBuilder(self.key)


class LengthExpressionBuilder:
    """Builder for length-based conditions."""
    
    def __init__(self, key: str):
        self.key = key
    
    def __gt__(self, value: int) -> Callable[[State, Any], bool]:
        """Check if len(state[key]) > value."""
        @condition
        def check(state: State, result: Any) -> bool:
            container = state.get(self.key, [])
            return len(container) > value
        
        check.__name__ = f"len(state[{self.key}]) > {value}"
        return check
    
    def __lt__(self, value: int) -> Callable[[State, Any], bool]:
        """Check if len(state[key]) < value."""
        @condition
        def check(state: State, result: Any) -> bool:
            container = state.get(self.key, [])
            return len(container) < value
        
        check.__name__ = f"len(state[{self.key}]) < {value}"
        return check
    
    def __eq__(self, value: int) -> Callable[[State, Any], bool]:
        """Check if len(state[key]) == value."""
        @condition
        def check(state: State, result: Any) -> bool:
            container = state.get(self.key, [])
            return len(container) == value
        
        check.__name__ = f"len(state[{self.key}]) == {value}"
        return check