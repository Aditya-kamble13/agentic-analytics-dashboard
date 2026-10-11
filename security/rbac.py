import streamlit as st

def get_user_role() -> str:
    """Reads role parameter from URL query parameters. Defaults to 'editor'."""
    query_params = st.query_params
    role = query_params.get("role", "editor")
    return str(role).lower()

def is_editor() -> bool:
    """Returns True if current user has Editor privileges."""
    return get_user_role() == "editor"