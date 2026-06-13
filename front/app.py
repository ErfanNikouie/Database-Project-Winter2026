from __future__ import annotations

from dash import Dash
import dash_mantine_components as dmc

from layouts.main_layout import build_main_layout


app = Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    title="HRMS",
)

app.layout = dmc.MantineProvider(
    forceColorScheme="dark",
    withGlobalClasses=True,
    withCssVariables=True,
    children=build_main_layout(),
)

# Register callback modules after app initialization.
import callbacks.authentication  # noqa: E402,F401
import callbacks.crud  # noqa: E402,F401
import callbacks.filters  # noqa: E402,F401
import callbacks.menus  # noqa: E402,F401
import callbacks.navigation  # noqa: E402,F401
import callbacks.profile  # noqa: E402,F401
import callbacks.reports  # noqa: E402,F401


if __name__ == "__main__":
    app.run(debug=True)

