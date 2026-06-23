"""
WSMIS Route Service
Route Registry, Validation, and Protection
Version: 1.0.0
"""

import streamlit as st
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum


class RouteType(Enum):
    """Route type enumeration."""
    PUBLIC = "public"
    PROTECTED = "protected"
    ADMIN = "admin"


@dataclass
class Route:
    """Route definition."""
    path: str
    type: RouteType
    title: str
    handler: Optional[Callable] = None
    allowed_roles: Optional[List[str]] = None
    allowed_dashboards: Optional[List[str]] = None
    query_params: Optional[Dict[str, Any]] = None


class RouteRegistry:
    """Central registry for all application routes."""
    
    def __init__(self):
        self._routes: Dict[str, Route] = {}
        self._initialize_default_routes()
    
    def _initialize_default_routes(self):
        """Initialize default route definitions."""
        # Public routes
        self.register_route(Route(
            path="/",
            type=RouteType.PUBLIC,
            title="Home"
        ))
        
        self.register_route(Route(
            path="/login",
            type=RouteType.PUBLIC,
            title="Login"
        ))
        
        self.register_route(Route(
            path="/logout",
            type=RouteType.PUBLIC,
            title="Logout"
        ))
        
        # Admin routes
        self.register_route(Route(
            path="/admin",
            type=RouteType.ADMIN,
            title="Admin",
            allowed_roles=["admin"]
        ))
        
        self.register_route(Route(
            path="/admin/users",
            type=RouteType.ADMIN,
            title="User Management",
            allowed_roles=["admin"]
        ))
        
        self.register_route(Route(
            path="/admin/roles",
            type=RouteType.ADMIN,
            title="Role Management",
            allowed_roles=["admin"]
        ))
        
        self.register_route(Route(
            path="/admin/audit",
            type=RouteType.ADMIN,
            title="Audit Log",
            allowed_roles=["admin"]
        ))
        
        # Protected routes (dashboards)
        # Paths MUST match the page-name keys used by resolve_page() / render_page_router()
        dashboard_routes = [
            ("/Cockpit", "Cockpit"),
            ("/Overview", "Overview"),
            ("/Executive", "Executive"),
            ("/Labour", "Labour"),
            ("/Parts Executive", "Parts Executive"),
            ("/Parts Detail", "Parts Detail"),
            ("/Margin", "Margin"),
            ("/Sales Mix", "Sales Mix"),
            ("/Discounts", "Discounts"),
            ("/Leakage Center", "Leakage Center"),
            ("/Advisors", "Advisors"),
            ("/Advisor MoM", "Advisor MoM"),
            ("/Locations", "Locations"),
            ("/Trends", "Trends"),
            ("/Targets", "Targets"),
            ("/Expense Analysis", "Expense Analysis"),
            ("/Profit & Loss", "Profit & Loss"),
            ("/Reports", "Reports"),
            ("/Internal Audit", "Internal Audit"),
            ("/Audit Intelligence", "Audit Intelligence"),
            ("/System Health", "System Health"),
        ]
        
        for path, title in dashboard_routes:
            self.register_route(Route(
                path=path,
                type=RouteType.PROTECTED,
                title=title
            ))
    
    def register_route(self, route: Route):
        """Register a route in the registry."""
        self._routes[route.path] = route
    
    def get_route(self, path: str) -> Optional[Route]:
        """Get route by path."""
        return self._routes.get(path)
    
    def get_all_routes(self) -> Dict[str, Route]:
        """Get all registered routes."""
        return self._routes.copy()
    
    def get_routes_by_type(self, route_type: RouteType) -> List[Route]:
        """Get all routes of a specific type."""
        return [route for route in self._routes.values() if route.type == route_type]
    
    def route_exists(self, path: str) -> bool:
        """Check if a route exists in the registry."""
        return path in self._routes
    
    def is_valid_route(self, path: str) -> bool:
        """Check if a route is valid (exists in registry)."""
        return self.route_exists(path)
    
    def get_route_type(self, path: str) -> Optional[RouteType]:
        """Get the type of a route."""
        route = self.get_route(path)
        return route.type if route else None


class RouteValidator:
    """Validates route access and parameters."""
    
    def __init__(self, registry: RouteRegistry):
        self.registry = registry
    
    def validate_route(self, path: str) -> tuple[bool, Optional[str]]:
        """
        Validate a route.
        Returns (is_valid, error_message)
        """
        if not path:
            return False, "Route path cannot be empty"
        
        if not self.registry.is_valid_route(path):
            return False, f"Route '{path}' not found"
        
        return True, None
    
    def validate_query_params(self, path: str, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate query parameters for a route.
        Returns (is_valid, error_message)
        """
        route = self.registry.get_route(path)
        if not route:
            return False, f"Route '{path}' not found"
        
        # If route has defined query params, validate them
        if route.query_params:
            for param_name, param_config in route.query_params.items():
                if param_name in params:
                    value = params[param_name]
                    # Add validation logic based on param_config
                    # For now, just check if required params are present
                    if param_config.get("required", False) and not value:
                        return False, f"Required parameter '{param_name}' is missing"
        
        return True, None
    
    def validate_deep_link(self, path: str, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate a deep link (route + parameters).
        Returns (is_valid, error_message)
        """
        # Validate route
        is_valid, error = self.validate_route(path)
        if not is_valid:
            return False, error
        
        # Validate parameters
        is_valid, error = self.validate_query_params(path, params)
        if not is_valid:
            return False, error
        
        return True, None
    
    def check_route_access(self, path: str, role: str) -> tuple[bool, Optional[str]]:
        """
        Check if a role has access to a route.
        Returns (has_access, error_message)
        """
        route = self.registry.get_route(path)
        if not route:
            return False, f"Route '{path}' not found"
        
        # Public routes are accessible to all
        if route.type == RouteType.PUBLIC:
            return True, None
        
        # Admin routes require admin role
        if route.type == RouteType.ADMIN:
            if route.allowed_roles and role not in route.allowed_roles:
                return False, "Admin access required"
            return True, None
        
        # Protected routes require authentication
        if route.type == RouteType.PROTECTED:
            if not role:
                return False, "Authentication required"
            return True, None
        
        return True, None


class RouteService:
    """Main service for route management and validation."""
    
    def __init__(self):
        self.registry = RouteRegistry()
        self.validator = RouteValidator(self.registry)
    
    def get_registry(self) -> RouteRegistry:
        """Get the route registry."""
        return self.registry
    
    def get_validator(self) -> RouteValidator:
        """Get the route validator."""
        return self.validator
    
    def navigate_to(self, path: str, params: Optional[Dict[str, Any]] = None):
        """
        Navigate to a route with optional parameters.
        Updates session state and validates the route.
        """
        params = params or {}
        
        # Validate route
        is_valid, error = self.validator.validate_deep_link(path, params)
        if not is_valid:
            st.error(f"Invalid route: {error}")
            return False
        
        # Update session state
        st.session_state["current_route"] = path
        st.session_state["route_params"] = params
        
        return True
    
    def get_current_route(self) -> Optional[str]:
        """Get the current route from session state."""
        return st.session_state.get("current_route")
    
    def get_route_params(self) -> Dict[str, Any]:
        """Get the current route parameters from session state."""
        return st.session_state.get("route_params", {})
    
    def sync_url_to_session(self):
        """Synchronize URL query parameters to session state."""
        query_params = st.query_params
        
        if query_params:
            params_dict = dict(query_params)
            st.session_state["route_params"] = params_dict
    
    def sync_session_to_url(self):
        """Synchronize session state to URL query parameters."""
        params = self.get_route_params()
        if params:
            st.query_params.update(params)


# Global route service instance
_route_service = None

def get_route_service() -> RouteService:
    """Get or create the global route service instance."""
    global _route_service
    if _route_service is None:
        _route_service = RouteService()
    return _route_service
