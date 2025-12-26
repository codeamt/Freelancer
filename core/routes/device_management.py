"""
Device Management Routes
"""

from fasthtml.common import *
from monsterui.all import *

router = Router()

# Import auth helpers
from core.routes.auth import get_current_user


@router.get("/profile/devices")
async def devices_page(request: Request):
    """Device management page for users"""
    current_user = await get_current_user(request)
    
    if not current_user:
        return RedirectResponse("/auth?tab=login&redirect=/profile/devices", status_code=303)
    
    auth_service = request.app.state.auth_service
    devices = await auth_service.get_user_devices(current_user.id)
    
    # Build device list
    device_items = []
    for device in devices:
        trust_badge = Badge("Trusted", color="success") if device.get("is_trusted") else Badge("Not Trusted", color="secondary")
        
        device_item = Li(
            Div(
                Div(
                    H4(device.get("device_name", "Unknown Device"), cls="text-lg font-semibold"),
                    P(f"Type: {device.get('device_type', 'Unknown').title()}", cls="text-sm text-gray-600"),
                    P(f"Platform: {device.get('platform', 'Unknown')}", cls="text-sm text-gray-600"),
                    P(f"Browser: {device.get('browser', 'Unknown')}", cls="text-sm text-gray-600"),
                    P(f"IP: {device.get('ip_address', 'Unknown')}", cls="text-sm text-gray-600"),
                    P(f"Last seen: {device.get('last_seen_at', 'Unknown')}", cls="text-sm text-gray-600"),
                    P(f"Active sessions: {device.get('active_sessions', 0)}", cls="text-sm text-gray-600"),
                    cls="flex-1"
                ),
                Div(
                    trust_badge,
                    Div(
                        Button(
                            "Revoke",
                            cls="btn btn-sm btn-error mt-2",
                            onclick=f"revokeDevice('{device.get('device_id')}')"
                        ),
                        cls="flex flex-col gap-2"
                    ),
                    cls="flex items-center gap-4"
                ),
                cls="flex justify-between items-center p-4 border rounded-lg"
            )
        )
        device_items.append(device_item)
    
    # Build page content
    content = Container(
        H2("Device Management", cls="text-2xl font-bold mb-6"),
        P("Manage your trusted devices and active sessions.", cls="mb-6"),
        
        H3("Active Devices", cls="text-xl font-semibold mb-4"),
        Ul(*device_items, cls="space-y-4 mb-8") if device_items else P("No devices found.", cls="text-gray-500"),
        
        Hr(cls="my-8"),
        
        H3("Security Tips", cls="text-xl font-semibold mb-4"),
        Ul(
            Li("Only trust devices you regularly use and control", cls="mb-2"),
            Li("Revoke access to devices you no longer use", cls="mb-2"),
            Li("Check your active sessions regularly", cls="mb-2"),
            Li("Enable two-factor authentication when available", cls="mb-2"),
            cls="list-disc list-inside text-gray-700"
        )
    )
    
    # Add JavaScript for device management
    script = Script("""
        async function revokeDevice(deviceId) {
            if (!confirm('Are you sure you want to revoke access to this device?')) {
                return;
            }
            
            try {
                const response = await fetch('/auth/device/revoke', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ device_id: deviceId })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert('Device revoked successfully');
                    window.location.reload();
                } else {
                    alert('Error: ' + result.error);
                }
            } catch (error) {
                alert('Error revoking device: ' + error.message);
            }
        }
    """)
    
    # Return within layout
    return Layout(
        Div(content, script, cls="container mx-auto px-4 py-8"),
        title="Device Management | FastApp",
        user=current_user,
        show_auth=True
    )


@router.get("/profile/devices/data")
async def devices_data(request: Request):
    """API endpoint to get device data as JSON"""
    current_user = await get_current_user(request)
    
    if not current_user:
        return Response(
            json.dumps({"error": "Authentication required"}),
            status_code=401,
            media_type="application/json"
        )
    
    auth_service = request.app.state.auth_service
    devices = await auth_service.get_user_devices(current_user.id)
    
    return Response(
        json.dumps({"devices": devices}),
        media_type="application/json"
    )
