"""
WSMIS Authentication & Authorization Service
Role-Based Access Control (RBAC) Foundation
Version: 1.0.0
"""

import yaml
import streamlit as st
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import time


class AuthService:
    """Handles user authentication, role-based access control, and session management."""
    
    def __init__(self):
        self._users_config = None
        self._config_path = Path(__file__).parent.parent / "config" / "users.yaml"
        self._load_config()
    
    def _load_config(self):
        """Load user configuration from YAML file."""
        try:
            with open(self._config_path, 'r') as f:
                self._users_config = yaml.safe_load(f)
        except FileNotFoundError:
            # Default configuration if file not found
            self._users_config = self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Return default configuration if YAML file is missing."""
        return {
            "users": {
                "admin": {
                    "name": "Administrator",
                    "email": "admin@wsmis.com",
                    "role": "admin",
                    "locations": ["all"],
                    "active": True
                }
            },
            "roles": {
                "admin": {
                    "dashboards": ["all"],
                    "admin_access": True,
                    "export_access": True,
                    "location_access": "all"
                }
            },
            "dashboard_permissions": {},
            "location_permissions": {},
            "session": {
                "timeout_minutes": 30,
                "warning_minutes": 5,
                "auto_logout": True
            },
            "routes": {
                "public": ["/", "/login", "/logout"],
                "admin": ["/admin", "/admin/users", "/admin/roles", "/admin/audit"],
                "protected": []
            }
        }
    
    def get_user(self, username: str) -> Optional[Dict]:
        """Get user configuration by username."""
        if not self._users_config:
            return None
        return self._users_config.get("users", {}).get(username)
    
    def get_role(self, role_name: str) -> Optional[Dict]:
        """Get role configuration by role name."""
        if not self._users_config:
            return None
        return self._users_config.get("roles", {}).get(role_name)
    
    def get_dashboard_permissions(self) -> Dict:
        """Get dashboard permission matrix."""
        if not self._users_config:
            return {}
        return self._users_config.get("dashboard_permissions", {})
    
    def get_location_permissions(self) -> Dict:
        """Get location permission matrix."""
        if not self._users_config:
            return {}
        return self._users_config.get("location_permissions", {})
    
    def get_session_config(self) -> Dict:
        """Get session configuration."""
        if not self._users_config:
            return {"timeout_minutes": 30, "warning_minutes": 5, "auto_logout": True}
        return self._users_config.get("session", {"timeout_minutes": 30, "warning_minutes": 5, "auto_logout": True})
    
    def get_routes_config(self) -> Dict:
        """Get route configuration."""
        if not self._users_config:
            return {"public": [], "admin": [], "protected": []}
        return self._users_config.get("routes", {"public": [], "admin": [], "protected": []})
    
    def check_dashboard_access(self, role: str, dashboard: str) -> str:
        """
        Check if a role has access to a dashboard.
        Returns: 'full', 'read', or 'none'
        """
        permissions = self.get_dashboard_permissions()
        dashboard_perms = permissions.get(dashboard, {})
        return dashboard_perms.get(role, "none")
    
    def check_location_access(self, role: str, location: str, user_locations: List[str]) -> bool:
        """
        Check if a role has access to a location.
        """
        role_config = self.get_role(role)
        if not role_config:
            return False
        
        location_access = role_config.get("location_access", "assigned")
        
        if location_access == "all":
            return True
        
        if location_access == "assigned":
            return location in user_locations or "all" in user_locations
        
        return False
    
    def check_admin_access(self, role: str) -> bool:
        """Check if a role has admin access."""
        role_config = self.get_role(role)
        if not role_config:
            return False
        return role_config.get("admin_access", False)
    
    def check_export_access(self, role: str) -> bool:
        """Check if a role has export access."""
        role_config = self.get_role(role)
        if not role_config:
            return False
        return role_config.get("export_access", False)
    
    def is_public_route(self, route: str) -> bool:
        """Check if a route is public (no authentication required)."""
        routes_config = self.get_routes_config()
        public_routes = routes_config.get("public", [])
        return route in public_routes
    
    def is_admin_route(self, route: str) -> bool:
        """Check if a route is admin-only."""
        routes_config = self.get_routes_config()
        admin_routes = routes_config.get("admin", [])
        return route in admin_routes
    
    def is_protected_route(self, route: str) -> bool:
        """Check if a route is protected (authentication required)."""
        routes_config = self.get_routes_config()
        protected_routes = routes_config.get("protected", [])
        return route in protected_routes
    
    def get_allowed_dashboards(self, role: str) -> List[str]:
        """Get list of dashboards accessible to a role."""
        role_config = self.get_role(role)
        if not role_config:
            return []
        
        dashboards = role_config.get("dashboards", [])
        if "all" in dashboards:
            # Return all dashboards from permission matrix
            permissions = self.get_dashboard_permissions()
            return list(permissions.keys())
        
        return dashboards
    
    def get_allowed_locations(self, role: str, user_locations: List[str]) -> List[str]:
        """Get list of locations accessible to a role."""
        role_config = self.get_role(role)
        if not role_config:
            return []
        
        location_access = role_config.get("location_access", "assigned")
        
        if location_access == "all":
            return ["all"]
        
        if location_access == "assigned":
            return user_locations
        
        return []
    
    def validate_session(self) -> bool:
        """
        Validate current session.
        Returns True if session is valid, False otherwise.
        """
        session_config = self.get_session_config()
        timeout_minutes = session_config.get("timeout_minutes", 30)
        
        # Check if session exists
        if "user" not in st.session_state:
            return False
        
        # Check if session has expired
        if "session_start" in st.session_state:
            session_start = st.session_state["session_start"]
            if isinstance(session_start, datetime):
                elapsed = datetime.now() - session_start
                if elapsed.total_seconds() > timeout_minutes * 60:
                    return False
        
        return True
    
    def create_session(self, username: str):
        """Create a new session for the user."""
        st.session_state["user"] = username
        st.session_state["session_start"] = datetime.now()
        st.session_state["last_activity"] = datetime.now()
    
    def update_session_activity(self):
        """Update last activity timestamp."""
        if "user" in st.session_state:
            st.session_state["last_activity"] = datetime.now()
    
    def destroy_session(self):
        """Destroy current session."""
        keys_to_remove = ["user", "session_start", "last_activity", "current_route"]
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]
    
    def get_session_remaining_time(self) -> int:
        """Get remaining session time in minutes."""
        session_config = self.get_session_config()
        timeout_minutes = session_config.get("timeout_minutes", 30)
        
        if "session_start" not in st.session_state:
            return 0
        
        session_start = st.session_state["session_start"]
        if isinstance(session_start, datetime):
            elapsed = datetime.now() - session_start
            remaining = timeout_minutes * 60 - elapsed.total_seconds()
            return max(0, int(remaining / 60))
        
        return 0
    
    def is_session_warning_time(self) -> bool:
        """Check if session is in warning period."""
        session_config = self.get_session_config()
        warning_minutes = session_config.get("warning_minutes", 5)
        remaining = self.get_session_remaining_time()
        return 0 < remaining <= warning_minutes


# Global auth service instance
_auth_service = None

def get_auth_service() -> AuthService:
    """Get or create the global auth service instance."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
