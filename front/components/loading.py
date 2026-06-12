from __future__ import annotations

import dash_mantine_components as dmc
from dash import html


def build_loading_overlay(child) -> dmc.LoadingOverlay:
    return dmc.LoadingOverlay(visible=False, overlayProps={"radius": "sm", "blur": 2}, children=child)


def build_skeleton_block(height: int = 220) -> html.Div:
    return html.Div(dmc.Skeleton(height=height, radius="md", visible=True), className="skeleton-block")

