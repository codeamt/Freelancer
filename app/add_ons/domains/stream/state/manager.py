"""State manager - orchestrates action execution with context"""
from typing import Any, Tuple
from core.utils.logger import get_logger
from app.add_ons.domains.stream.state.actions import Action, ActionResult
from app.add_ons.domains.stream.services.stream_uow import StreamUnitOfWork

logger = get_logger(__name__)


class StreamStateManager:
    """
    Orchestrates action execution with proper context injection
    
    Responsibilities:
    - Inject dependencies (UoW, settings, integrations)
    - Handle permissions (via middleware)
    - Log actions (audit trail)
    - Coordinate transactions
    """
    
    def __init__(self, settings, integrations, analytics=None, tasks=None):
        self.settings = settings
        self.integrations = integrations
        self.analytics = analytics
        self.tasks = tasks
    
    async def execute(self, action: Action, current_state: Any = None, 
                     user_context: dict = None) -> Tuple[Any, ActionResult]:
        """
        Execute an action with full context
        
        Args:
            action: The action to execute
            current_state: Current state (if applicable)
            user_context: User context for permissions
        
        Returns:
            (new_state, ActionResult)
        """
        
        action_name = action.__class__.__name__
        logger.info(f"Executing action: {action_name}")
        
        # 1. Build execution context
        context = {
            'uow': StreamUnitOfWork(),  # Fresh UoW for each action
            'settings': self.settings,
            'integrations': self.integrations,
            'analytics': self.analytics,
            'tasks': self.tasks,
            'user_context': user_context
        }
        
        try:
            # 2. Execute action (with automatic transaction handling via UoW)
            new_state, result = await action.execute(current_state, context)
            
            # 3. Log result
            if result.success:
                logger.info(f"Action {action_name} succeeded: {result.message}")
            else:
                logger.warning(f"Action {action_name} failed: {result.message}")
            
            return new_state, result
        
        except Exception as e:
            logger.error(f"Action {action_name} raised exception: {e}")
            return current_state, ActionResult(
                False,
                "Action failed with error",
                [str(e)]
            )