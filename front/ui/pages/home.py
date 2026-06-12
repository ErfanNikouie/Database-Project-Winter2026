from __future__ import annotations

import streamlit as st


def render_home() -> None:
    st.title("Dynamic HR Meta-App (Prototype)")
    st.write(
        "This is a metadata-driven HR prototype. Use the sidebar to navigate. "
        "Use **Initialize** to seed default HR forms/menus."
    )

    st.subheader("What you can do")
    st.markdown(
        "- Create **Forms** (which map to physical SQLite tables)\n"
        "- Define **Form Fields** (columns)\n"
        "- Create hierarchical **Menus** pointing to forms\n"
        "- Use generated forms for CRUD operations"
    )

