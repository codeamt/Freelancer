"""
Admin Role Management Routes

API endpoints for administrators to manage user roles.
"""
from fasthtml.common import *
from monsterui.all import *
from starlette.responses import JSONResponse
from typing import List, Optional
from core.services.auth.decorators import require_auth, requires_role
from core.services.auth.models import UserRole, RoleAssignment
from core.services.auth.role_hierarchy import RoleHierarchy, RoleConflictError
from core.services.auth.role_audit_service import RoleAuditService
from core.utils.logger import get_logger

logger = get_logger(__name__)
router_admin_roles = APIRouter()


@router_admin_roles.get("/admin/api/users/{user_id}/roles")
@requires_role(UserRole.ADMIN, UserRole.SUPER_ADMIN)
async def get_user_roles(request: Request, user_id: int):
    """Get a user's current roles"""
    user_service = request.app.state.user_service
    
    try:
        user = await user_service.get_user_by_id(user_id)
        if not user:
            return JSONResponse(
                {"error": "User not found"},
                status_code=404
            )
        
        # Get role summary
        role_summary = RoleHierarchy.get_role_summary(user.roles)
        
        return JSONResponse({
            "user_id": user.id,
            "email": user.email,
            "roles": user.roles,
            "role_summary": role_summary
        })
        
    except Exception as e:
        logger.error(f"Failed to get user roles: {e}")
        return JSONResponse(
            {"error": "Internal server error"},
            status_code=500
        )


@router_admin_roles.post("/admin/api/users/{user_id}/roles")
@requires_role(UserRole.ADMIN, UserRole.SUPER_ADMIN)
async def assign_user_roles(
    request: Request,
    user_id: int,
    role_data: RoleAssignment
):
    """Assign roles to a user"""
    user_service = request.app.state.user_service
    audit_service = RoleAuditService(user_service.user_repo)
    
    try:
        # Get current user
        current_user = await user_service.get_user_by_id(user_id)
        if not current_user:
            return JSONResponse(
                {"error": "User not found"},
                status_code=404
            )
        
        # Validate role assignment
        is_valid, errors = RoleHierarchy.validate_role_assignment(
            current_user.roles,
            role_data.roles
        )
        
        if not is_valid:
            return JSONResponse(
                {"error": "Invalid role assignment", "details": errors},
                status_code=400
            )
        
        # Check if the assigning user has permission to assign these roles
        current_admin = await user_service.get_user_by_email(
            request.ctx.user.get("email")
        )
        admin_roles = current_admin.roles if current_admin else []
        
        # Only super admins can assign super admin role
        if UserRole.SUPER_ADMIN in role_data.roles and UserRole.SUPER_ADMIN not in admin_roles:
            return JSONResponse(
                {"error": "Only Super Admins can assign Super Admin role"},
                status_code=403
            )
        
        # Log the change
        await audit_service.log_role_change(
            user_id=user_id,
            action="assign",
            previous_roles=current_user.roles,
            new_roles=role_data.roles,
            changed_by=current_admin.id if current_admin else None,
            reason=role_data.__dict__.get("reason", "Role assignment via API"),
            request=request
        )
        
        # Update user roles
        await user_service.update_user_roles(user_id, role_data.roles)
        
        # Increment role version for JWT revocation
        await user_service.increment_role_version(user_id)
        
        logger.info(f"Roles updated for user {user_id}: {role_data.roles}")
        
        return JSONResponse({
            "success": True,
            "message": "Roles updated successfully",
            "previous_roles": current_user.roles,
            "new_roles": role_data.roles
        })
        
    except Exception as e:
        logger.error(f"Failed to assign user roles: {e}")
        return JSONResponse(
            {"error": "Internal server error"},
            status_code=500
        )


@router_admin_roles.delete("/admin/api/users/{user_id}/roles/{role}")
@requires_role(UserRole.ADMIN, UserRole.SUPER_ADMIN)
async def revoke_user_role(request: Request, user_id: int, role: str):
    """Revoke a specific role from a user"""
    user_service = request.app.state.user_service
    audit_service = RoleAuditService(user_service.user_repo)
    
    try:
        # Validate role
        try:
            role_to_revoke = UserRole(role)
        except ValueError:
            return JSONResponse(
                {"error": f"Invalid role: {role}"},
                status_code=400
            )
        
        # Get current user
        current_user = await user_service.get_user_by_id(user_id)
        if not current_user:
            return JSONResponse(
                {"error": "User not found"},
                status_code=404
            )
        
        # Check if user has the role
        if role_to_revoke not in current_user.roles:
            return JSONResponse(
                {"error": f"User does not have role: {role}"},
                status_code=400
            )
        
        # Check permissions - can't revoke super admin unless you are one
        if role_to_revoke == UserRole.SUPER_ADMIN:
            current_admin = await user_service.get_user_by_email(
                request.ctx.user.get("email")
            )
            admin_roles = current_admin.roles if current_admin else []
            if UserRole.SUPER_ADMIN not in admin_roles:
                return JSONResponse(
                    {"error": "Only Super Admins can revoke Super Admin role"},
                    status_code=403
                )
        
        # Remove the role
        new_roles = [r for r in current_user.roles if r != role_to_revoke]
        
        # Log the change
        await audit_service.log_role_change(
            user_id=user_id,
            action="revoke",
            previous_roles=current_user.roles,
            new_roles=new_roles,
            changed_by=request.ctx.user.get("id"),
            reason=f"Revoked role: {role}",
            request=request
        )
        
        # Update user roles
        await user_service.update_user_roles(user_id, new_roles)
        
        # Increment role version
        await user_service.increment_role_version(user_id)
        
        logger.info(f"Role {role} revoked from user {user_id}")
        
        return JSONResponse({
            "success": True,
            "message": f"Role {role} revoked successfully",
            "previous_roles": current_user.roles,
            "new_roles": new_roles
        })
        
    except Exception as e:
        logger.error(f"Failed to revoke user role: {e}")
        return JSONResponse(
            {"error": "Internal server error"},
            status_code=500
        )


@router_admin_roles.get("/admin/api/roles")
@requires_role(UserRole.ADMIN, UserRole.SUPER_ADMIN)
async def list_all_roles(request: Request):
    """Get all available roles with hierarchy info"""
    try:
        roles = []
        for role in UserRole:
            roles.append({
                "name": role.value,
                "level": RoleHierarchy.get_hierarchy_level(role),
                "description": _get_role_description(role)
            })
        
        # Sort by hierarchy level
        roles.sort(key=lambda r: r["level"], reverse=True)
        
        return JSONResponse({
            "roles": roles,
            "total": len(roles)
        })
        
    except Exception as e:
        logger.error(f"Failed to list roles: {e}")
        return JSONResponse(
            {"error": "Internal server error"},
            status_code=500
        )


@router_admin_roles.get("/admin/api/users/{user_id}/role-history")
@requires_role(UserRole.ADMIN, UserRole.SUPER_ADMIN)
async def get_user_role_history(
    request: Request,
    user_id: int,
    limit: int = 50,
    offset: int = 0
):
    """Get role change history for a user"""
    user_service = request.app.state.user_service
    audit_service = RoleAuditService(user_service.user_repo)
    
    try:
        history = await audit_service.get_role_history(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        return JSONResponse({
            "history": history,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": len(history)
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get role history: {e}")
        return JSONResponse(
            {"error": "Internal server error"},
            status_code=500
        )


@router_admin_roles.post("/admin/api/users/bulk-role-update")
@requires_role(UserRole.ADMIN, UserRole.SUPER_ADMIN)
async def bulk_role_update(request: Request):
    """Bulk update roles for multiple users (Super Admin only)"""
    user_service = request.app.state.user_service
    audit_service = RoleAuditService(user_service.user_repo)
    
    try:
        data = await request.json()
        user_ids = data.get("user_ids", [])
        roles_to_assign = [UserRole(r) for r in data.get("roles", [])]
        reason = data.get("reason", "Bulk role update")
        
        if not user_ids:
            return JSONResponse(
                {"error": "No user IDs provided"},
                status_code=400
            )
        
        if not roles_to_assign:
            return JSONResponse(
                {"error": "No roles provided"},
                status_code=400
            )
        
        # Validate role assignment
        is_valid, errors = RoleHierarchy.validate_role_assignment([], roles_to_assign)
        
        if not is_valid:
            return JSONResponse(
                {"error": "Invalid role assignment", "details": errors},
                status_code=400
            )
        
        results = []
        errors_list = []
        
        for user_id in user_ids:
            try:
                # Get current user
                current_user = await user_service.get_user_by_id(user_id)
                if not current_user:
                    errors_list.append(f"User {user_id} not found")
                    continue
                
                # Log the change
                await audit_service.log_role_change(
                    user_id=user_id,
                    action="bulk_update",
                    previous_roles=current_user.roles,
                    new_roles=roles_to_assign,
                    changed_by=request.ctx.user.get("id"),
                    reason=reason,
                    request=request
                )
                
                # Update user roles
                await user_service.update_user_roles(user_id, roles_to_assign)
                await user_service.increment_role_version(user_id)
                
                results.append({
                    "user_id": user_id,
                    "success": True,
                    "previous_roles": current_user.roles,
                    "new_roles": roles_to_assign
                })
                
            except Exception as e:
                logger.error(f"Failed to update roles for user {user_id}: {e}")
                errors_list.append(f"Failed to update user {user_id}: {str(e)}")
        
        return JSONResponse({
            "success": True,
            "results": results,
            "errors": errors_list,
            "summary": {
                "total": len(user_ids),
                "successful": len(results),
                "failed": len(errors_list)
            }
        })
        
    except Exception as e:
        logger.error(f"Failed bulk role update: {e}")
        return JSONResponse(
            {"error": "Internal server error"},
            status_code=500
        )


def _get_role_description(role: UserRole) -> str:
    """Get human-readable description for a role"""
    descriptions = {
        UserRole.SUPER_ADMIN: "Full platform access with all privileges",
        UserRole.ADMIN: "Site administrator with management privileges",
        UserRole.INSTRUCTOR: "Course instructor with educational content access",
        UserRole.EDITOR: "Content editor with page and component access",
        UserRole.STUDENT: "Student with course enrollment access",
        UserRole.USER: "Regular authenticated user",
        UserRole.GUEST: "Guest user with minimal access",
        UserRole.BLOG_ADMIN: "Blog domain administrator",
        UserRole.BLOG_AUTHOR: "Blog content author",
        UserRole.LMS_ADMIN: "Learning Management System administrator",
        UserRole.MEMBER: "Paid member with enhanced access",
        UserRole.SITE_OWNER: "Site owner with full site control",
        UserRole.SITE_ADMIN: "Site administrator (legacy)",
        UserRole.SUPPORT_STAFF: "Platform support staff",
    }
    return descriptions.get(role, "Custom role")
