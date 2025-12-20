"""
State Machine Application Builder - Burr-inspired builder pattern.

This module provides the builder pattern for constructing state machines.
"""

from typing import List, Dict, Optional, Callable, Tuple, Any, TYPE_CHECKING
from .state import State, StateManager
from .actions import Action
from .transitions import Transition, TransitionCondition
from core.utils.logger import get_logger

if TYPE_CHECKING:
    from core.di.container import ExecutionContext

logger = get_logger(__name__)


class StateMachineApplication:
    """
    State machine application for managing workflows.
    
    This ties together actions, transitions, and state management.
    """
    
    def __init__(
        self,
        actions: Dict[str, Action],
        transitions: Dict[str, List[Transition]],
        entrypoint: str,
        state_manager: StateManager,
        hooks: Optional[Dict[str, Callable]] = None
    ):
        """
        Initialize state machine application.
        
        Args:
            actions: Dictionary of action name to Action instance
            transitions: Dictionary of action name to list of Transitions
            entrypoint: Name of starting action
            state_manager: StateManager instance
            hooks: Optional lifecycle hooks
        """
        self.actions = actions
        self.transitions = transitions
        self.entrypoint = entrypoint
        self.state_manager = state_manager
        self.hooks = hooks or {}
        self.current_action = entrypoint
        
        # Validate
        if entrypoint not in actions:
            raise ValueError(f"Entrypoint '{entrypoint}' not in actions")
    
    async def step(self, context: Optional['ExecutionContext'] = None, **inputs) -> Tuple[str, Any, State]:
        """
        Execute one step of the state machine.
        
        Args:
            context: Optional execution context with user permissions and services
            **inputs: Runtime inputs for the action
            
        Returns:
            Tuple of (action_name, result, new_state)
        """
        # Get current action
        action = self.actions[self.current_action]
        
        # Execute before hooks
        if "before_action" in self.hooks:
            await self.hooks["before_action"](self.current_action, self.state_manager.current)
        
        # Execute action with context
        new_state, result = await action.execute(self.state_manager.current, context, **inputs)
        
        # Update state manager
        self.state_manager.update(new_state)
        
        # Execute after hooks
        if "after_action" in self.hooks:
            await self.hooks["after_action"](
                self.current_action, 
                result, 
                self.state_manager.current
            )
        
        # Determine next action based on transitions
        next_action = await self._get_next_action(new_state, result)
        
        if next_action:
            self.current_action = next_action
        
        return self.current_action, result, new_state
    
    async def _get_next_action(self, state: State, result: Any) -> Optional[str]:
        """
        Determine next action based on transitions.
        
        Args:
            state: Current state
            result: Result from last action
            
        Returns:
            Name of next action or None if no valid transition
        """
        if self.current_action not in self.transitions:
            return None
        
        transitions = self.transitions[self.current_action]
        
        for transition in transitions:
            if await transition.should_transition(state, result):
                return transition.target
        
        return None
    
    async def run(
        self,
        context: Optional['ExecutionContext'] = None,
        halt_after: Optional[List[str]] = None,
        halt_before: Optional[List[str]] = None,
        max_steps: int = 100,
        **initial_inputs
    ) -> Tuple[str, Any, State]:
        """
        Run the state machine until halting condition.
        
        Args:
            halt_after: List of actions to halt after executing
            halt_before: List of actions to halt before executing
            max_steps: Maximum number of steps to prevent infinite loops
            **initial_inputs: Initial inputs for first action
            
        Returns:
            Tuple of (final_action, final_result, final_state)
        """
        halt_after = halt_after or []
        halt_before = halt_before or []
        steps = 0
        last_result = None
        
        while steps < max_steps:
            # Check halt before
            if self.current_action in halt_before:
                logger.info(f"Halting before action: {self.current_action}")
                break
            
            # Execute step with context
            action_name, result, state = await self.step(context, **initial_inputs)
            last_result = result
            steps += 1
            initial_inputs = {}  # Clear inputs after first step
            
            # Check halt after
            if action_name in halt_after:
                logger.info(f"Halting after action: {action_name}")
                break
            
            # Check if we're at a dead end
            if action_name not in self.transitions or not self.transitions[action_name]:
                logger.info(f"Reached end of state machine at: {action_name}")
                break
        
        if steps >= max_steps:
            logger.warning(f"State machine hit max_steps limit: {max_steps}")
        
        return self.current_action, last_result, self.state_manager.current
    
    async def iterate(
        self,
        halt_after: Optional[List[str]] = None,
        halt_before: Optional[List[str]] = None,
        max_steps: int = 100,
        **initial_inputs
    ):
        """
        Iterate through state machine steps.
        
        Yields each step for observation.
        
        Args:
            halt_after: List of actions to halt after executing
            halt_before: List of actions to halt before executing  
            max_steps: Maximum number of steps
            **initial_inputs: Initial inputs for first action
            
        Yields:
            Tuple of (action_name, result, state) for each step
        """
        halt_after = halt_after or []
        halt_before = halt_before or []
        steps = 0
        
        while steps < max_steps:
            if self.current_action in halt_before:
                break
            
            action_name, result, state = await self.step(**initial_inputs)
            yield action_name, result, state
            
            steps += 1
            initial_inputs = {}
            
            if action_name in halt_after:
                break
            
            if action_name not in self.transitions or not self.transitions[action_name]:
                break
    
    def get_graph(self) -> Dict[str, Any]:
        """
        Get graph representation of state machine.
        
        Returns:
            Dictionary with nodes and edges
        """
        nodes = list(self.actions.keys())
        edges = []
        
        for source, transitions in self.transitions.items():
            for transition in transitions:
                edges.append({
                    "source": source,
                    "target": transition.target,
                    "condition": transition.condition.__name__ if transition.condition else "default"
                })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "entrypoint": self.entrypoint
        }


class SiteStateBuilder:
    """
    Builder for constructing site state machine applications.
    
    Provides fluent API for building state machines.
    """
    
    def __init__(self):
        """Initialize builder."""
        self._actions: Dict[str, Action] = {}
        self._transitions: Dict[str, List[Transition]] = {}
        self._entrypoint: Optional[str] = None
        self._initial_state: Optional[State] = None
        self._hooks: Dict[str, Callable] = {}
    
    def with_actions(self, *actions: Action) -> "SiteStateBuilder":
        """
        Add actions to the builder.
        
        Args:
            *actions: Action instances to add
            
        Returns:
            Self for chaining
        """
        for action in actions:
            self._actions[action.name] = action
        return self
    
    def with_transitions(self, *transitions: Tuple[str, str, Optional[Callable]]) -> "SiteStateBuilder":
        """
        Add transitions between actions.
        
        Args:
            *transitions: Tuples of (source_action, target_action, condition)
                         condition is optional - defaults to always transition
            
        Returns:
            Self for chaining
        """
        for transition_tuple in transitions:
            if len(transition_tuple) == 2:
                source, target = transition_tuple
                condition = None
            else:
                source, target, condition = transition_tuple
            
            if source not in self._transitions:
                self._transitions[source] = []
            
            self._transitions[source].append(
                Transition(target=target, condition=condition)
            )
        
        return self
    
    def with_conditional_transitions(
        self, 
        source: str, 
        conditions: List[Tuple[Callable, str]],
        default: Optional[str] = None
    ) -> "SiteStateBuilder":
        """
        Add conditional transitions from a source action.
        
        Args:
            source: Source action name
            conditions: List of (condition_func, target_action) tuples
            default: Optional default target if no conditions match
            
        Returns:
            Self for chaining
        """
        if source not in self._transitions:
            self._transitions[source] = []
        
        for condition, target in conditions:
            self._transitions[source].append(
                Transition(target=target, condition=condition)
            )
        
        if default:
            self._transitions[source].append(
                Transition(target=default, condition=None)
            )
        
        return self
    
    def with_entrypoint(self, action_name: str) -> "SiteStateBuilder":
        """
        Set the entrypoint action.
        
        Args:
            action_name: Name of starting action
            
        Returns:
            Self for chaining
        """
        self._entrypoint = action_name
        return self
    
    def with_state(self, **initial_data) -> "SiteStateBuilder":
        """
        Set initial state data.
        
        Args:
            **initial_data: Initial state key-value pairs
            
        Returns:
            Self for chaining
        """
        self._initial_state = State(initial_data)
        return self
    
    def with_hook(self, hook_name: str, hook_func: Callable) -> "SiteStateBuilder":
        """
        Add lifecycle hook.
        
        Args:
            hook_name: Name of hook (before_action, after_action, etc.)
            hook_func: Hook function
            
        Returns:
            Self for chaining
        """
        self._hooks[hook_name] = hook_func
        return self
    
    def build(self) -> StateMachineApplication:
        """
        Build the state machine application.
        
        Returns:
            StateMachineApplication instance
            
        Raises:
            ValueError: If required components are missing
        """
        if not self._actions:
            raise ValueError("State machine must have at least one action")
        
        if not self._entrypoint:
            raise ValueError("State machine must have an entrypoint")
        
        # Create state manager
        state_manager = StateManager(self._initial_state or State())
        
        return StateMachineApplication(
            actions=self._actions,
            transitions=self._transitions,
            entrypoint=self._entrypoint,
            state_manager=state_manager,
            hooks=self._hooks
        )