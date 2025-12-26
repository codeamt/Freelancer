/**
 * JWT Token Refresh Manager
 * Handles automatic token refresh and expiration warnings
 */

class TokenRefreshManager {
    constructor(options = {}) {
        this.refreshEndpoint = options.refreshEndpoint || '/auth/refresh';
        this.expiryCheckInterval = options.expiryCheckInterval || 60000; // Check every minute
        this.warningThreshold = options.warningThreshold || 300; // 5 minutes warning
        this.refreshThreshold = options.refreshThreshold || 60; // Refresh when 1 minute left
        this.onRefreshSuccess = options.onRefreshSuccess || null;
        this.onRefreshError = options.onRefreshError || null;
        this.onExpiringSoon = options.onExpiringSoon || null;
        this.onExpired = options.onExpired || null;
        
        this.checkInterval = null;
        this.isRefreshing = false;
    }
    
    start() {
        // Start periodic checks
        this.checkInterval = setInterval(() => {
            this.checkTokenExpiry();
        }, this.expiryCheckInterval);
        
        // Initial check
        this.checkTokenExpiry();
    }
    
    stop() {
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
            this.checkInterval = null;
        }
    }
    
    getToken() {
        // Get token from cookie
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'auth_token') {
                return value;
            }
        }
        return null;
    }
    
    getRefreshToken() {
        // Get refresh token from cookie
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'refresh_token') {
                return value;
            }
        }
        return null;
    }
    
    parseJWT(token) {
        try {
            const base64Url = token.split('.')[1];
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            const jsonPayload = decodeURIComponent(
                atob(base64)
                    .split('')
                    .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
                    .join('')
            );
            return JSON.parse(jsonPayload);
        } catch (e) {
            return null;
        }
    }
    
    async checkTokenExpiry() {
        const token = this.getToken();
        
        if (!token) {
            return;
        }
        
        const payload = this.parseJWT(token);
        
        if (!payload || !payload.exp) {
            return;
        }
        
        const now = Math.floor(Date.now() / 1000);
        const timeUntilExpiry = payload.exp - now;
        
        // Check if token is expired
        if (timeUntilExpiry <= 0) {
            if (this.onExpired) {
                this.onExpired();
            } else {
                // Default behavior: redirect to login
                window.location.href = '/auth?tab=login&error=Session+expired';
            }
            return;
        }
        
        // Check if token is expiring soon
        if (timeUntilExpiry <= this.warningThreshold) {
            if (this.onExpiringSoon) {
                this.onExpiringSoon(timeUntilExpiry);
            } else {
                // Show warning toast
                this.showToast('Session expiring soon', 'warning');
            }
        }
        
        // Check if token should be refreshed
        if (timeUntilExpiry <= this.refreshThreshold && !this.isRefreshing) {
            await this.refreshToken();
        }
    }
    
    async refreshToken() {
        this.isRefreshing = true;
        
        try {
            const refreshToken = this.getRefreshToken();
            
            if (!refreshToken) {
                throw new Error('No refresh token available');
            }
            
            const response = await fetch(this.refreshEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    refresh_token: refreshToken
                })
            });
            
            const data = await response.json();
            
            if (response.ok && data.access_token) {
                // Update the auth token cookie
                document.cookie = `auth_token=${data.access_token}; path=/; max-age=86400; samesite=lax${window.location.protocol === 'https:' ? '; secure' : ''}`;
                
                if (this.onRefreshSuccess) {
                    this.onRefreshSuccess(data);
                } else {
                    // Show success message
                    this.showToast('Session refreshed', 'success');
                }
            } else {
                throw new Error(data.error || 'Refresh failed');
            }
        } catch (error) {
            console.error('Token refresh failed:', error);
            
            if (this.onRefreshError) {
                this.onRefreshError(error);
            } else {
                // Show error and redirect to login
                this.showToast('Failed to refresh session', 'error');
                setTimeout(() => {
                    window.location.href = '/auth?tab=login&error=Session+expired';
                }, 2000);
            }
        } finally {
            this.isRefreshing = false;
        }
    }
    
    showToast(message, type = 'info') {
        // Simple toast implementation
        // In production, use your preferred toast library
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 12px 24px;
            background: ${type === 'error' ? '#ef4444' : type === 'warning' ? '#f59e0b' : type === 'success' ? '#10b981' : '#3b82f6'};
            color: white;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            z-index: 9999;
            animation: slideIn 0.3s ease-out;
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, 3000);
    }
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Initialize and export
window.TokenRefreshManager = TokenRefreshManager;

// Auto-initialize if auth token exists
document.addEventListener('DOMContentLoaded', () => {
    const tokenManager = new TokenRefreshManager();
    
    // Custom handlers
    tokenManager.onExpiringSoon = (secondsLeft) => {
        console.log('Token expiring in', secondsLeft, 'seconds');
    };
    
    tokenManager.onExpired = () => {
        console.log('Token expired');
        window.location.href = '/auth?tab=login&error=Session+expired';
    };
    
    // Start monitoring
    if (tokenManager.getToken()) {
        tokenManager.start();
    }
    
    // Make available globally
    window.tokenManager = tokenManager;
});
