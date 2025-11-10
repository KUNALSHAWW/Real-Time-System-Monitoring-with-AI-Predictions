"""
Advanced Role-Based Access Control (RBAC) System
Provides granular permission management for API endpoints
"""

from fastapi import HTTPException, Depends, Header
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel

# ============================================================================
# ROLE DEFINITIONS
# ============================================================================

class UserRole(str, Enum):
    """User role hierarchy"""
    ADMIN = "admin"          # Full access
    OPERATOR = "operator"    # Can view and modify metrics, incidents
    VIEWER = "viewer"        # Read-only access
    GUEST = "guest"          # Limited read access

class Permission(str, Enum):
    """Available permissions"""
    READ_METRICS = "read:metrics"
    WRITE_METRICS = "write:metrics"
    READ_INCIDENTS = "read:incidents"
    WRITE_INCIDENTS = "write:incidents"
    READ_USERS = "read:users"
    WRITE_USERS = "write:users"
    MANAGE_SETTINGS = "manage:settings"
    DELETE_DATA = "delete:data"
    TRIGGER_ALERTS = "trigger:alerts"

# ============================================================================
# ROLE-PERMISSION MAPPING
# ============================================================================

ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        Permission.READ_METRICS,
        Permission.WRITE_METRICS,
        Permission.READ_INCIDENTS,
        Permission.WRITE_INCIDENTS,
        Permission.READ_USERS,
        Permission.WRITE_USERS,
        Permission.MANAGE_SETTINGS,
        Permission.DELETE_DATA,
        Permission.TRIGGER_ALERTS
    ],
    UserRole.OPERATOR: [
        Permission.READ_METRICS,
        Permission.WRITE_METRICS,
        Permission.READ_INCIDENTS,
        Permission.WRITE_INCIDENTS,
        Permission.TRIGGER_ALERTS
    ],
    UserRole.VIEWER: [
        Permission.READ_METRICS,
        Permission.READ_INCIDENTS
    ],
    UserRole.GUEST: [
        Permission.READ_METRICS
    ]
}

# ============================================================================
# USER MODEL
# ============================================================================

class User(BaseModel):
    """User model with role and permissions"""
    id: int
    username: str
    email: str
    role: UserRole
    permissions: List[Permission] = []
    is_active: bool = True
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission"""
        return permission in ROLE_PERMISSIONS.get(self.role, [])
    
    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions"""
        user_permissions = ROLE_PERMISSIONS.get(self.role, [])
        return any(p in user_permissions for p in permissions)
    
    def has_all_permissions(self, permissions: List[Permission]) -> bool:
        """Check if user has all of the specified permissions"""
        user_permissions = ROLE_PERMISSIONS.get(self.role, [])
        return all(p in user_permissions for p in permissions)

# ============================================================================
# DEPENDENCY FUNCTIONS
# ============================================================================

async def get_current_user(authorization: Optional[str] = Header(None)) -> User:
    """
    Extract and validate user from authorization header
    
    In production, this would:
    1. Decode JWT token
    2. Validate signature
    3. Check expiration
    4. Load user from database
    5. Return User object
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Mock implementation - replace with actual JWT validation
    # For demo, parse role from header
    token = authorization.replace("Bearer ", "")
    
    # In production: decode JWT and get user from database
    # For now, return mock user
    return User(
        id=1,
        username="demo_user",
        email="user@example.com",
        role=UserRole.ADMIN  # Change based on actual token
    )

def require_permission(permission: Permission):
    """
    Dependency to require specific permission
    
    Usage:
        @router.get("/admin", dependencies=[Depends(require_permission(Permission.MANAGE_SETTINGS))])
    """
    async def permission_checker(user: User = Depends(get_current_user)):
        if not user.has_permission(permission):
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: requires {permission.value}"
            )
        return user
    
    return permission_checker

def require_any_permission(permissions: List[Permission]):
    """Dependency to require any of the specified permissions"""
    async def permission_checker(user: User = Depends(get_current_user)):
        if not user.has_any_permission(permissions):
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: requires one of {[p.value for p in permissions]}"
            )
        return user
    
    return permission_checker

def require_all_permissions(permissions: List[Permission]):
    """Dependency to require all of the specified permissions"""
    async def permission_checker(user: User = Depends(get_current_user)):
        if not user.has_all_permissions(permissions):
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: requires all of {[p.value for p in permissions]}"
            )
        return user
    
    return permission_checker

def require_role(role: UserRole):
    """Dependency to require specific role"""
    async def role_checker(user: User = Depends(get_current_user)):
        if user.role != role:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied: requires {role.value} role"
            )
        return user
    
    return role_checker

def require_admin():
    """Shortcut dependency for admin-only endpoints"""
    return require_role(UserRole.ADMIN)

# ============================================================================
# AUDIT LOGGING
# ============================================================================

class AuditLog:
    """Audit log for RBAC actions"""
    
    @staticmethod
    async def log_access(user: User, resource: str, action: str, success: bool):
        """Log access attempt"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user.id,
            "username": user.username,
            "role": user.role.value,
            "resource": resource,
            "action": action,
            "success": success
        }
        
        # In production: write to database or log file
        print(f"AUDIT: {log_entry}")
        
        return log_entry
