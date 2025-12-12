"""
Admin User Management Routes - Admin/SuperAdmin endpoints for managing users.

Routes:
- GET /admin/users - List all users
- GET /admin/users/{user_id} - View user details
- POST /admin/users - Create new user
- PUT /admin/users/{user_id} - Update user
- DELETE /admin/users/{user_id} - Delete user
- PUT /admin/users/{user_id}/role - Change user role (SuperAdmin only)
"""

from fasthtml.common import *
from monsterui.all import *
from core.services.auth import require_admin, require_super_admin
from core.utils.logger import get_logger

logger = get_logger(__name__)

router_admin_users = APIRouter()


@router_admin_users.get("/admin/users")
@require_admin()
async def list_users(request: Request):
    """List all users with filtering and search."""
    user_service = request.app.state.user_service
    
    # Get query params
    search = request.query_params.get("search", "")
    role_filter = request.query_params.get("role", "")
    
    # Get users
    result = await user_service.list_users(search=search, role=role_filter)
    
    if not result["success"]:
        return Alert(f"Error: {result.get('error')}", cls="alert-error")
    
    users = result["users"]
    
    return Card(
        Div(
            H2("User Management", cls="text-2xl font-bold mb-6"),
            
            # Search and filters
            Div(
                Form(
                    Input(
                        type="text",
                        name="search",
                        placeholder="Search users...",
                        value=search,
                        cls="input input-bordered w-full md:w-64 mr-2"
                    ),
                    Select(
                        Option("All Roles", value=""),
                        Option("Super Admin", value="super_admin"),
                        Option("Admin", value="admin"),
                        Option("Editor", value="editor"),
                        Option("Member", value="member"),
                        name="role",
                        value=role_filter,
                        cls="select select-bordered mr-2"
                    ),
                    ButtonPrimary("Filter", type="submit"),
                    hx_get="/admin/users",
                    hx_target="#user-list",
                    cls="flex gap-2 mb-4"
                ),
                
                ButtonPrimary(
                    "+ Create User",
                    hx_get="/admin/users/create",
                    hx_target="#user-content",
                    cls="mb-4"
                ),
                
                cls="mb-6"
            ),
            
            # User list
            Div(
                *[
                    Card(
                        Div(
                            Div(
                                H4(u.email, cls="font-bold"),
                                Badge(u.role.replace("_", " ").title(), cls="badge-primary ml-2"),
                                cls="flex items-center mb-2"
                            ),
                            P(f"ID: {u.id}", cls="text-sm text-gray-600 mb-2"),
                            P(
                                f"Created: {u.created_at.strftime('%Y-%m-%d')}" if hasattr(u, 'created_at') else "",
                                cls="text-sm text-gray-600 mb-4"
                            ),
                            
                            # Actions
                            Div(
                                ButtonSecondary(
                                    "View",
                                    hx_get=f"/admin/users/{u.id}",
                                    hx_target="#user-content",
                                    cls="btn-sm mr-2"
                                ),
                                ButtonSecondary(
                                    "Edit",
                                    hx_get=f"/admin/users/{u.id}/edit",
                                    hx_target="#user-content",
                                    cls="btn-sm mr-2"
                                ),
                                ButtonDanger(
                                    "Delete",
                                    hx_delete=f"/api/admin/users/{u.id}",
                                    hx_target="#user-list",
                                    hx_confirm=f"Delete user {u.email}?",
                                    cls="btn-sm"
                                ) if u.role != "super_admin" else None,
                                cls="flex gap-2"
                            ),
                            
                            cls="p-4"
                        ),
                        cls="mb-2"
                    )
                    for u in users
                ],
                id="user-list"
            ) if users else P("No users found", cls="text-gray-600"),
            
            cls="p-6"
        ),
        id="user-content"
    )


@router_admin_users.get("/admin/users/create")
@require_admin()
async def create_user_form(request: Request):
    """Show create user form."""
    return Card(
        Div(
            H2("Create New User", cls="text-2xl font-bold mb-6"),
            
            Form(
                Div(
                    Label("Email", cls="block text-sm font-bold mb-1"),
                    Input(
                        type="email",
                        name="email",
                        required=True,
                        placeholder="user@example.com",
                        cls="input input-bordered w-full mb-4"
                    )
                ),
                
                Div(
                    Label("Password", cls="block text-sm font-bold mb-1"),
                    Input(
                        type="password",
                        name="password",
                        required=True,
                        placeholder="Minimum 8 characters",
                        cls="input input-bordered w-full mb-4"
                    )
                ),
                
                Div(
                    Label("Role", cls="block text-sm font-bold mb-1"),
                    Select(
                        Option("Member", value="member"),
                        Option("Editor", value="editor"),
                        Option("Admin", value="admin"),
                        name="role",
                        cls="select select-bordered w-full mb-4"
                    )
                ),
                
                Div(
                    Label("Display Name (Optional)", cls="block text-sm font-bold mb-1"),
                    Input(
                        type="text",
                        name="display_name",
                        placeholder="John Doe",
                        cls="input input-bordered w-full mb-4"
                    )
                ),
                
                Div(
                    ButtonPrimary("Create User", type="submit", cls="mr-2"),
                    ButtonSecondary(
                        "Cancel",
                        hx_get="/admin/users",
                        hx_target="#user-content"
                    ),
                    cls="flex gap-2"
                ),
                
                hx_post="/api/admin/users",
                hx_target="#user-content"
            ),
            
            cls="p-6"
        )
    )


@router_admin_users.get("/admin/users/{user_id}")
@require_admin()
async def view_user(request: Request, user_id: int):
    """View user details."""
    user_service = request.app.state.user_service
    
    user_data = await user_service.get_user_by_id(user_id)
    
    if not user_data:
        return Alert("User not found", cls="alert-error")
    
    return Card(
        Div(
            H2("User Details", cls="text-2xl font-bold mb-6"),
            
            Div(
                Div(
                    Label("Email", cls="block text-sm font-bold mb-1"),
                    P(user_data.email, cls="text-gray-700 mb-4")
                ),
                Div(
                    Label("Role", cls="block text-sm font-bold mb-1"),
                    Badge(user_data.role.replace("_", " ").title(), cls="badge-primary mb-4")
                ),
                Div(
                    Label("User ID", cls="block text-sm font-bold mb-1"),
                    P(str(user_data.id), cls="text-gray-700 mb-4")
                ),
                Div(
                    Label("Display Name", cls="block text-sm font-bold mb-1"),
                    P(getattr(user_data, 'display_name', 'N/A'), cls="text-gray-700 mb-4")
                ),
                Div(
                    Label("Created", cls="block text-sm font-bold mb-1"),
                    P(
                        user_data.created_at.strftime("%B %d, %Y") if hasattr(user_data, 'created_at') else "N/A",
                        cls="text-gray-700 mb-4"
                    )
                ),
                cls="mb-6"
            ),
            
            # Actions
            Div(
                ButtonPrimary(
                    "Edit User",
                    hx_get=f"/admin/users/{user_id}/edit",
                    hx_target="#user-content",
                    cls="mr-2"
                ),
                ButtonSecondary(
                    "Change Role",
                    hx_get=f"/admin/users/{user_id}/role",
                    hx_target="#user-content",
                    cls="mr-2"
                ) if user_data.role != "super_admin" else None,
                ButtonSecondary(
                    "Back to List",
                    hx_get="/admin/users",
                    hx_target="#user-content"
                ),
                cls="flex gap-2"
            ),
            
            cls="p-6"
        )
    )


@router_admin_users.get("/admin/users/{user_id}/edit")
@require_admin()
async def edit_user_form(request: Request, user_id: int):
    """Show edit user form."""
    user_service = request.app.state.user_service
    
    user_data = await user_service.get_user_by_id(user_id)
    
    if not user_data:
        return Alert("User not found", cls="alert-error")
    
    return Card(
        Div(
            H2(f"Edit User: {user_data.email}", cls="text-2xl font-bold mb-6"),
            
            Form(
                Div(
                    Label("Display Name", cls="block text-sm font-bold mb-1"),
                    Input(
                        type="text",
                        name="display_name",
                        value=getattr(user_data, 'display_name', ''),
                        placeholder="John Doe",
                        cls="input input-bordered w-full mb-4"
                    )
                ),
                
                Div(
                    Label("Bio", cls="block text-sm font-bold mb-1"),
                    Textarea(
                        getattr(user_data, 'bio', ''),
                        name="bio",
                        rows=4,
                        placeholder="User bio",
                        cls="textarea textarea-bordered w-full mb-4"
                    )
                ),
                
                Div(
                    ButtonPrimary("Save Changes", type="submit", cls="mr-2"),
                    ButtonSecondary(
                        "Cancel",
                        hx_get=f"/admin/users/{user_id}",
                        hx_target="#user-content"
                    ),
                    cls="flex gap-2"
                ),
                
                hx_put=f"/api/admin/users/{user_id}",
                hx_target="#user-content"
            ),
            
            cls="p-6"
        )
    )


@router_admin_users.get("/admin/users/{user_id}/role")
@require_super_admin()
async def change_role_form(request: Request, user_id: int):
    """Show change role form (SuperAdmin only)."""
    user_service = request.app.state.user_service
    
    user_data = await user_service.get_user_by_id(user_id)
    
    if not user_data:
        return Alert("User not found", cls="alert-error")
    
    return Card(
        Div(
            H2(f"Change Role: {user_data.email}", cls="text-2xl font-bold mb-6"),
            
            Alert(
                "⚠️ Changing user roles affects their permissions across the entire platform.",
                cls="alert-warning mb-4"
            ),
            
            Form(
                Div(
                    Label("Current Role", cls="block text-sm font-bold mb-1"),
                    Badge(user_data.role.replace("_", " ").title(), cls="badge-primary mb-4")
                ),
                
                Div(
                    Label("New Role", cls="block text-sm font-bold mb-1"),
                    Select(
                        Option("Member", value="member", selected=user_data.role == "member"),
                        Option("Editor", value="editor", selected=user_data.role == "editor"),
                        Option("Admin", value="admin", selected=user_data.role == "admin"),
                        Option("Super Admin", value="super_admin", selected=user_data.role == "super_admin"),
                        name="role",
                        cls="select select-bordered w-full mb-4"
                    )
                ),
                
                Div(
                    ButtonPrimary("Change Role", type="submit", cls="mr-2"),
                    ButtonSecondary(
                        "Cancel",
                        hx_get=f"/admin/users/{user_id}",
                        hx_target="#user-content"
                    ),
                    cls="flex gap-2"
                ),
                
                hx_put=f"/api/admin/users/{user_id}/role",
                hx_target="#user-content",
                hx_confirm="Are you sure you want to change this user's role?"
            ),
            
            cls="p-6"
        )
    )


# ============================================================================
# API Endpoints
# ============================================================================

@router_admin_users.post("/api/admin/users")
@require_admin()
async def create_user(request: Request):
    """Create new user."""
    user_service = request.app.state.user_service
    
    form = await request.form()
    user_data = {
        "email": form.get("email"),
        "password": form.get("password"),
        "role": form.get("role", "member"),
        "display_name": form.get("display_name")
    }
    
    try:
        result = await user_service.create_user(**user_data)
        
        if result["success"]:
            return Div(
                Alert(f"✓ User {user_data['email']} created successfully!", cls="alert-success mb-4"),
                ButtonPrimary(
                    "Back to User List",
                    hx_get="/admin/users",
                    hx_target="#user-content"
                )
            )
        else:
            return Alert(f"Error: {result.get('error')}", cls="alert-error")
            
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return Alert("Failed to create user", cls="alert-error")


@router_admin_users.put("/api/admin/users/{user_id}")
@require_admin()
async def update_user(request: Request, user_id: int):
    """Update user details."""
    user_service = request.app.state.user_service
    
    form = await request.form()
    updates = {
        "display_name": form.get("display_name"),
        "bio": form.get("bio")
    }
    
    try:
        result = await user_service.update_user(user_id, updates)
        
        if result["success"]:
            return Div(
                Alert("✓ User updated successfully!", cls="alert-success mb-4"),
                ButtonPrimary(
                    "Back to User Details",
                    hx_get=f"/admin/users/{user_id}",
                    hx_target="#user-content"
                )
            )
        else:
            return Alert(f"Error: {result.get('error')}", cls="alert-error")
            
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        return Alert("Failed to update user", cls="alert-error")


@router_admin_users.put("/api/admin/users/{user_id}/role")
@require_super_admin()
async def change_user_role(request: Request, user_id: int):
    """Change user role (SuperAdmin only)."""
    user_service = request.app.state.user_service
    current_user = request.state.user
    
    # Prevent changing own role
    if current_user.id == user_id:
        return Alert("Cannot change your own role", cls="alert-error")
    
    form = await request.form()
    new_role = form.get("role")
    
    try:
        result = await user_service.update_user(user_id, {"role": new_role})
        
        if result["success"]:
            return Div(
                Alert(f"✓ User role changed to {new_role.replace('_', ' ').title()}!", cls="alert-success mb-4"),
                ButtonPrimary(
                    "Back to User Details",
                    hx_get=f"/admin/users/{user_id}",
                    hx_target="#user-content"
                )
            )
        else:
            return Alert(f"Error: {result.get('error')}", cls="alert-error")
            
    except Exception as e:
        logger.error(f"Error changing user role: {e}")
        return Alert("Failed to change user role", cls="alert-error")


@router_admin_users.delete("/api/admin/users/{user_id}")
@require_admin()
async def delete_user(request: Request, user_id: int):
    """Delete user."""
    user_service = request.app.state.user_service
    current_user = request.state.user
    
    # Prevent self-deletion
    if current_user.id == user_id:
        return Alert("Cannot delete your own account", cls="alert-error")
    
    # Prevent deleting super admins (unless you're also super admin)
    user_to_delete = await user_service.get_user_by_id(user_id)
    if user_to_delete.role == "super_admin" and current_user.role != "super_admin":
        return Alert("Cannot delete super admin users", cls="alert-error")
    
    try:
        result = await user_service.delete_user(user_id)
        
        if result["success"]:
            # Return updated user list
            return await list_users(request)
        else:
            return Alert(f"Error: {result.get('error')}", cls="alert-error")
            
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        return Alert("Failed to delete user", cls="alert-error")
