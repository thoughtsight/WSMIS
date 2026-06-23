"""
StateManager - Central Session State Management

Implements namespace-driven session state architecture as approved in
Claude Opus 4.8 Architecture Review.

Responsibilities:
- Register state with namespaces
- Get/set state with validation
- Initialize defaults
- Reset current page (namespace-driven)
- Reset all (protect-list driven)
- Protect permanent keys
- Validate namespaces
"""

import streamlit as st
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field


@dataclass
class NamespaceConfig:
    """Configuration for a dashboard namespace."""
    prefix: str
    defaults: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


class StateManager:
    """
    Central session state manager with namespace-driven reset.
    
    Architecture:
    - Namespace-based state (lab_*, parts_*, cockpit_*, etc.)
    - Shared global filters (flt_*)
    - Protected keys (auth, cache, expensive outputs)
    - Reset Page: clears active namespace + shared filters
    - Reset All: clears everything except protected keys
    """
    
    # Reserved namespace for shared global filters
    GLOBAL_NAMESPACE = "flt_"
    
    # Legacy global filter keys (for backward compatibility during migration)
    # These are treated as global filters even without the flt_ prefix
    # NOTE: Period-related keys (month_preset, selected_months_custom, comparison_mode_radio, last_preset)
    # and global location/BU filters (filter_location, filter_mp_pb) are NOT included here
    # because they are now true global filters and should NOT be reset by reset_page()
    LEGACY_GLOBAL_KEYS: Set[str] = {
        "filter_svc_type_single",
        "filter_svc_type_labour",
        "filter_adv_single",
        "filter_svc_type",
        "filter_advisor",
    }
    
    # Protected keys that survive Reset All
    PROTECTED_KEYS: Set[str] = {
        # Authentication
        "authenticated",
        "user_email",
        "user_role",
        
        # Data cache
        "cached_data",
        "data_synced_at",
        "last_refresh",
        
        # Expensive computations
        "ai_response_cache",
        "ml_model_cache",
        
        # System state
        "initialized",
        "env_validated",
        "startup_time",
        "current_page",
        "preset_applied",
        
        # Internal audit state
        "dealer_audit_period",
    }
    
    # Registered namespaces
    _namespaces: Dict[str, NamespaceConfig] = {}
    
    @classmethod
    def register_namespace(cls, config: NamespaceConfig) -> None:
        """Register a dashboard namespace with its defaults."""
        cls._namespaces[config.prefix] = config
    
    @classmethod
    def initialize_namespace(cls, prefix: str) -> None:
        """Initialize all defaults for a namespace if not already set."""
        if prefix not in cls._namespaces:
            return
        
        config = cls._namespaces[prefix]
        for key, default_value in config.defaults.items():
            full_key = f"{prefix}{key}"
            if full_key not in st.session_state:
                st.session_state[full_key] = default_value
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Get a session state value."""
        return st.session_state.get(key, default)
    
    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """Set a session state value."""
        st.session_state[key] = value
    
    @classmethod
    def is_protected(cls, key: str) -> bool:
        """Check if a key is protected."""
        return key in cls.PROTECTED_KEYS
    
    @classmethod
    def get_namespace_for_key(cls, key: str) -> Optional[str]:
        """Extract namespace prefix from a key."""
        # Check against registered namespaces
        for prefix in cls._namespaces:
            if key.startswith(prefix):
                return prefix
        # Check global namespace
        if key.startswith(cls.GLOBAL_NAMESPACE):
            return cls.GLOBAL_NAMESPACE
        return None
    
    @classmethod
    def reset_page(cls, active_namespace: str) -> int:
        """
        Reset current page state.
        
        Clears:
        - All keys in active_namespace
        - All keys in GLOBAL_NAMESPACE (shared filters)
        - Legacy global filter keys (for backward compatibility)
        
        Preserves:
        - Protected keys
        - Other dashboard namespaces
        
        Returns number of keys cleared.
        """
        keys_to_delete = []
        
        for key in list(st.session_state.keys()):
            # Never delete protected keys
            if cls.is_protected(key):
                continue
            
            # Delete keys in active namespace
            if key.startswith(active_namespace):
                keys_to_delete.append(key)
                continue
            
            # Delete keys in global namespace (shared filters)
            if key.startswith(cls.GLOBAL_NAMESPACE):
                keys_to_delete.append(key)
                continue
            
            # Delete legacy global filter keys (backward compatibility)
            if key in cls.LEGACY_GLOBAL_KEYS:
                keys_to_delete.append(key)
                continue
        
        # Delete keys (must not be iterating while modifying)
        for key in keys_to_delete:
            del st.session_state[key]
        
        # Clear page-specific ui_* widget keys to prevent stale state
        page_ui_keys_to_clear = [
            "ui_filter_svc_type_single",
            "ui_filter_adv_single",
            "lab_biz_ui",
            "filter_svc_type_labour",  # Labour-specific widget key
        ]
        for ui_key in page_ui_keys_to_clear:
            if ui_key in st.session_state:
                del st.session_state[ui_key]
        
        return len(keys_to_delete)
    
    @classmethod
    def reset_all(cls) -> int:
        """
        Reset all session state except protected keys.
        
        Clears everything except PROTECTED_KEYS.
        Also resets global period to application default (3M).
        Clears both persistent keys and their corresponding ui_* widget keys.
        
        Returns number of keys cleared.
        """
        keys_to_delete = []
        
        for key in list(st.session_state.keys()):
            if not cls.is_protected(key):
                keys_to_delete.append(key)
        
        # Delete keys
        for key in keys_to_delete:
            del st.session_state[key]
        
        # Reset global period to application default
        st.session_state.month_preset = "3M"
        st.session_state.last_preset = "3M"
        st.session_state.selected_months_custom = []
        st.session_state.comparison_mode_radio = "YoY"
        st.session_state.user_has_selected_period = False
        
        # Clear ui_* widget keys for global filters
        ui_keys_to_clear = [
            "ui_month_preset",
            "ui_comparison_mode_radio",
            "ui_selected_months_custom",
            "ui_filter_location",
            "ui_filter_mp_pb",
            "ui_filter_svc_type_single",
            "ui_filter_adv_single",
        ]
        for ui_key in ui_keys_to_clear:
            if ui_key in st.session_state:
                del st.session_state[ui_key]
        
        return len(keys_to_delete)
    
    @classmethod
    def validate_namespaces(cls) -> Dict[str, List[str]]:
        """
        Validate all session state keys against registered namespaces.
        
        Returns dict of invalid keys by namespace (or "unregistered").
        """
        invalid = {"unregistered": []}
        
        for key in st.session_state.keys():
            if cls.is_protected(key):
                continue
            
            namespace = cls.get_namespace_for_key(key)
            if namespace is None:
                invalid["unregistered"].append(key)
        
        return invalid
    
    @classmethod
    def get_registered_namespaces(cls) -> List[str]:
        """Get list of registered namespace prefixes."""
        return list(cls._namespaces.keys())
    
    @classmethod
    def get_state_summary(cls) -> Dict[str, int]:
        """Get summary of current session state distribution."""
        summary = {
            "protected": 0,
            "global": 0,
            "namespaces": {},
            "unregistered": 0,
        }
        
        for key in st.session_state.keys():
            if cls.is_protected(key):
                summary["protected"] += 1
            elif key.startswith(cls.GLOBAL_NAMESPACE):
                summary["global"] += 1
            else:
                namespace = cls.get_namespace_for_key(key)
                if namespace:
                    if namespace not in summary["namespaces"]:
                        summary["namespaces"][namespace] = 0
                    summary["namespaces"][namespace] += 1
                else:
                    summary["unregistered"] += 1
        
        return summary
