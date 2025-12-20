# Admin Test Credentials

## Quick Access Admin User
- **Email**: `admin@example.org`
- **Password**: `Admin123!`
- **Roles**: `admin`, `site_admin`
- **Permissions**: Full site editing, theme editing, user management

## How to Create This User

1. **Register via Web Interface**:
   - Go to http://localhost:5001/auth?tab=register
   - Email: `admin@example.org`
   - Password: `Admin123!`
   - Confirm Password: `Admin123!`
   - Role: Select "Administrator"
   - Submit

2. **Login via Admin Portal**:
   - Go to http://localhost:5001/admin/login
   - Email: `admin@example.org`
   - Password: `Admin123!`

## Access Points

- **Admin Dashboard**: http://localhost:5001/admin/dashboard
- **Site Editor**: http://localhost:5001/admin/site/main/editor
- **User Management**: http://localhost:5001/admin/users

## Permissions

This user has:
- `site.theme.edit` - Edit themes, colors, typography
- `site.content.edit` - Manage pages, sections, components
- `site.content.view` - View site content
- `site.users.manage` - Manage site users
- Full admin access to platform settings

## Testing

After creating this user:
1. Login and verify admin dashboard access
2. Navigate to site editor
3. Test page creation, theme editing, preview functionality
4. Verify all permissions work correctly

The registration system now automatically assigns both `admin` and `site_admin` roles when registering with "Administrator" role.
