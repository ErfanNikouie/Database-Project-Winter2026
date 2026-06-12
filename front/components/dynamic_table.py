from __future__ import annotations

from io import StringIO

import pandas as pd
import streamlit as st

try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
except Exception:  # pragma: no cover - optional dependency import guard
    AgGrid = None
    GridOptionsBuilder = None
    GridUpdateMode = None
    JsCode = None


def render_toolbar(*, can_insert: bool, can_delete: bool, can_print: bool, count: int) -> dict[str, bool]:
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 2, 2])
    with col1:
        insert_clicked = st.button("Insert", disabled=not can_insert, use_container_width=True)
    with col2:
        refresh_clicked = st.button("Refresh", use_container_width=True)
    with col3:
        delete_clicked = st.button("Delete", disabled=not can_delete, use_container_width=True)
    with col4:
        export_clicked = st.button("Export CSV", disabled=not can_print, use_container_width=True)
    with col5:
        st.markdown(f"**Record count:** {count}")

    return {
        "insert": insert_clicked,
        "refresh": refresh_clicked,
        "delete": delete_clicked,
        "export": export_clicked,
    }


def render_data_grid(df: pd.DataFrame, *, key: str) -> dict:
    if AgGrid is None or df.empty:
        st.dataframe(df, use_container_width=True)
        return {"selected_rows": []}

    grid_df = df.copy()
    if "__open_edit__" not in grid_df.columns:
        grid_df["__open_edit__"] = 0

    options_builder = GridOptionsBuilder.from_dataframe(grid_df)
    options_builder.configure_default_column(resizable=True, sortable=True, filter=True)
    options_builder.configure_selection(selection_mode="single", use_checkbox=True)
    options_builder.configure_column("__open_edit__", hide=True)
    if JsCode is not None:
        options_builder.configure_grid_options(
            domLayout="normal",
            onRowDoubleClicked=JsCode(
                """
                function(event) {
                    event.data.__open_edit__ = Date.now();
                    event.api.applyTransaction({update: [event.data]});
                }
                """
            ),
        )
    else:
        options_builder.configure_grid_options(domLayout="normal")
    options = options_builder.build()

    return AgGrid(
        grid_df,
        gridOptions=options,
        theme="balham-dark",
        height=430,
        fit_columns_on_grid_load=False,
        update_mode=GridUpdateMode.SELECTION_CHANGED | GridUpdateMode.MODEL_CHANGED,
        allow_unsafe_jscode=True,
        key=key,
    )


def render_export_button(df: pd.DataFrame, *, key: str, filename: str) -> None:
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    st.download_button(
        "Download CSV",
        data=csv_buffer.getvalue(),
        file_name=filename,
        mime="text/csv",
        key=key,
        use_container_width=True,
    )

