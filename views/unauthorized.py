"""
WSMIS Unauthorized Access Page (403)
Displayed when user lacks permission to access a resource
Version: 1.0.0
"""

import streamlit as st
from ui.components.core import UniversalHeader, UniversalFooter, EmptyState


def render_unauthorized_page():
    """Render the unauthorized access (403) page."""
    
    # Header
    UniversalHeader()
    
    # Unauthorized content
    st.markdown("""
    <div style="text-align: center; padding: 80px 20px;">
        <div style="font-size: 120px; font-weight: 700; color: var(--color-danger); margin-bottom: 20px;">
            403
        </div>
        <h1 style="font-size: 32px; font-weight: 600; color: var(--color-text-primary); margin-bottom: 16px;">
            Access Denied
        </h1>
        <p style="font-size: 16px; color: var(--color-text-secondary); margin-bottom: 32px; max-width: 500px; margin-left: auto; margin-right: auto;">
            You don't have permission to access this page. Please contact your administrator if you believe this is an error.
        </p>
        <div style="margin-top: 40px;">
            <a href="/" style="display: inline-block; padding: 12px 24px; background: var(--color-primary); color: white; text-decoration: none; border-radius: 8px; font-weight: 500;">
                Return to Home
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Footer
    UniversalFooter()


def render_not_found_page():
    """Render the not found (404) page."""
    
    # Header
    UniversalHeader()
    
    # Not found content
    st.markdown("""
    <div style="text-align: center; padding: 80px 20px;">
        <div style="font-size: 120px; font-weight: 700; color: var(--color-warning); margin-bottom: 20px;">
            404
        </div>
        <h1 style="font-size: 32px; font-weight: 600; color: var(--color-text-primary); margin-bottom: 16px;">
            Page Not Found
        </h1>
        <p style="font-size: 16px; color: var(--color-text-secondary); margin-bottom: 32px; max-width: 500px; margin-left: auto; margin-right: auto;">
            The page you're looking for doesn't exist or has been moved. Please check the URL and try again.
        </p>
        <div style="margin-top: 40px;">
            <a href="/" style="display: inline-block; padding: 12px 24px; background: var(--color-primary); color: white; text-decoration: none; border-radius: 8px; font-weight: 500;">
                Return to Home
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Footer
    UniversalFooter()


def render_session_expired_page():
    """Render the session expired page."""
    
    # Header
    UniversalHeader()
    
    # Session expired content
    st.markdown("""
    <div style="text-align: center; padding: 80px 20px;">
        <div style="font-size: 80px; margin-bottom: 20px;">
            ⏰
        </div>
        <h1 style="font-size: 32px; font-weight: 600; color: var(--color-text-primary); margin-bottom: 16px;">
            Session Expired
        </h1>
        <p style="font-size: 16px; color: var(--color-text-secondary); margin-bottom: 32px; max-width: 500px; margin-left: auto; margin-right: auto;">
            Your session has expired due to inactivity. Please log in again to continue.
        </p>
        <div style="margin-top: 40px;">
            <a href="/login" style="display: inline-block; padding: 12px 24px; background: var(--color-primary); color: white; text-decoration: none; border-radius: 8px; font-weight: 500;">
                Log In Again
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Footer
    UniversalFooter()
