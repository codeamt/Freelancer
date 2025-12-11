from contextvars import ContextVar
from dataclasses import dataclass
from typing import Set, Optional
from enum import Enum
  
class Permission(Enum):
    VIEW_USERS = "users.view"
    CREATE_USERS = "users.create"
    EDIT_USERS = "users.edit"
    DELETE_USERS = "users.delete"
    VIEW_ORDERS = "commerce.orders.view"
    VIEW_OWN_ORDERS = "commerce.orders.view_own"
    PROCESS_REFUNDS = "commerce.refunds.process"
    MANAGE_TAX_SETTINGS = "commerce.settings.tax"
    VIEW_ANALYTICS = "system.analytics.view"
    CHANGE_GLOBAL_SETTINGS = "system.settings.global"
    # Add more permissions
  
@dataclass
class UserContext:
    user_id: int
    role: str
    permissions: Set[Permission]
    request_cookies: dict
    ip_address: str
    _outgoing_cookies: dict = field(default_factory=dict)
      
    def has_permission(self, permission: Permission) -> bool:
        return permission in self.permissions
      
    def can_access_resource(self, permission: Permission, resource_owner_id: int) -> bool:
        if self.user_id == resource_owner_id:
            return True
        return self.has_permission(permission)
      
    def set_cookie(self, key: str, value: str, **kwargs):
        self._outgoing_cookies[key] = (value, kwargs)
      
    def get_cookie(self, key: str, default=None):
        if key in self._outgoing_cookies:
            return self._outgoing_cookies[key][0]
        return self.request_cookies.get(key, default)
  
# Global context variable
current_user_context: ContextVar[UserContext] = ContextVar('current_user_context')