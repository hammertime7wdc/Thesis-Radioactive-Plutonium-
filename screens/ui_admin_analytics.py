import sys
import os
import math
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import flet as ft
import flet.canvas as cv
from utils.utils import (
    BG_COLOR, CARD_BG_COLOR, SECTION_BG_COLOR,
    PRIMARY_BLUE, PRIMARY_BLUE_DARK, PRIMARY_BLUE_LIGHT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_TERTIARY, TEXT_WHITE,
    BORDER_COLOR, BORDER_COLOR_DARK,
    BUTTON_PRIMARY_BG, BUTTON_PRIMARY_TEXT, BUTTON_SECONDARY_BG, BUTTON_SECONDARY_TEXT, BUTTON_SECONDARY_BORDER,
    INPUT_BG, INPUT_BORDER, INPUT_TEXT, INPUT_HINT,
    SUCCESS, WARNING, ERROR
)
from services.analytics_service import fetch_analytics_summary

# ── Chart colors ────────────────────────────────────────────────────
GREEN = "#22c55e"
ORANGE = "#f59e0b"
RED = "#ef4444"
PURPLE = "#8b5cf6"
GRID_COLOR = "#e2e8f0"


# ─────────────────────────────────────────────────────────────────
# Stat card (Total Evaluations / Avg Similarity Score)
# ─────────────────────────────────────────────────────────────────
def build_stat_card(label, value, subtitle, value_color=TEXT_PRIMARY):
    return ft.Container(
        content=ft.Column(
            [
                ft.Text(label, size=13, color=TEXT_SECONDARY),
                ft.Container(height=6),
                ft.Text(str(value), size=28, weight=ft.FontWeight.BOLD, color=value_color),
                ft.Container(height=2),
                ft.Text(subtitle, size=12, color=TEXT_TERTIARY),
            ],
            spacing=0,
        ),
        padding=ft.padding.all(20),
        bgcolor=CARD_BG_COLOR,
        border_radius=12,
        border=ft.border.all(1, BORDER_COLOR),
        expand=True,
    )


# ─────────────────────────────────────────────────────────────────
# Classification Distribution — Pie Chart
# ─────────────────────────────────────────────────────────────────
def build_pie_chart(fully_pct, partial_pct, irrelevant_pct):
    chart = ft.PieChart(
        sections=[
            ft.PieChartSection(
                fully_pct,
                title=f"{fully_pct}%",
                title_style=ft.TextStyle(size=13, color=TEXT_WHITE, weight=ft.FontWeight.BOLD),
                color=GREEN,
                radius=100,
            ),
            ft.PieChartSection(
                partial_pct,
                title=f"{partial_pct}%",
                title_style=ft.TextStyle(size=13, color=TEXT_WHITE, weight=ft.FontWeight.BOLD),
                color=ORANGE,
                radius=100,
            ),
            ft.PieChartSection(
                irrelevant_pct,
                title=f"{irrelevant_pct}%",
                title_style=ft.TextStyle(size=13, color=TEXT_WHITE, weight=ft.FontWeight.BOLD),
                color=RED,
                radius=100,
            ),
        ],
        sections_space=2,
        center_space_radius=0,
        height=240,
    )

    legend = ft.Row(
        [
            _legend_dot("Fully Relevant", GREEN),
            ft.Container(width=20),
            _legend_dot("Partially Relevant", ORANGE),
            ft.Container(width=20),
            _legend_dot("Irrelevant", RED),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
    )

    return ft.Container(
        content=ft.Column(
            [
                ft.Text("Classification Distribution", size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(height=16),
                ft.Container(chart, alignment=ft.alignment.center),
                ft.Container(height=12),
                legend,
            ],
            spacing=0,
        ),
        padding=ft.padding.all(24),
        bgcolor=CARD_BG_COLOR,
        border_radius=12,
        border=ft.border.all(1, BORDER_COLOR),
        expand=True,
    )


def _legend_dot(label, color):
    return ft.Row(
        [
            ft.Container(width=8, height=8, bgcolor=color, border_radius=4),
            ft.Container(width=6),
            ft.Text(label, size=12, color=TEXT_SECONDARY),
        ],
        spacing=0,
    )


def _empty_chart_placeholder(title, message):
    """Shown instead of a chart when there isn't enough real data yet
    (e.g. no evaluations with criterion_scores populated so far)."""
    return ft.Container(
        content=ft.Column(
            [
                ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(height=40),
                ft.Icon(ft.Icons.BAR_CHART_OUTLINED, size=32, color=TEXT_TERTIARY),
                ft.Container(height=8),
                ft.Text(message, size=12, color=TEXT_TERTIARY, text_align=ft.TextAlign.CENTER),
                ft.Container(height=40),
            ],
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.padding.all(24),
        bgcolor=CARD_BG_COLOR,
        border_radius=12,
        border=ft.border.all(1, BORDER_COLOR),
        expand=True,
    )


# ─────────────────────────────────────────────────────────────────
# Average Score by Criterion — Radar / Spider Chart
# ─────────────────────────────────────────────────────────────────
def build_radar_chart(labels, values, max_value=100, size=260):
    center = size / 2
    radius = size * 0.34
    n = len(labels)
    rings = 4  # number of concentric grid rings

    def point(angle_deg, r):
        angle_rad = math.radians(angle_deg)
        x = center + r * math.sin(angle_rad)
        y = center - r * math.cos(angle_rad)
        return x, y

    def axis_angle(i):
        return (360 / n) * i  # 0 = straight up, clockwise

    shapes = []

    # Concentric web rings
    for ring in range(1, rings + 1):
        r = radius * ring / rings
        elements = []
        for i in range(n + 1):
            x, y = point(axis_angle(i % n), r)
            if i == 0:
                elements.append(cv.Path.MoveTo(x, y))
            else:
                elements.append(cv.Path.LineTo(x, y))
        shapes.append(cv.Path(elements, paint=ft.Paint(
            style=ft.PaintingStyle.STROKE, stroke_width=1, color=GRID_COLOR)))

    # Axis spokes
    for i in range(n):
        x, y = point(axis_angle(i), radius)
        shapes.append(cv.Line(center, center, x, y,
                               paint=ft.Paint(stroke_width=1, color=GRID_COLOR)))

    # Data polygon
    data_elements = []
    for i in range(n + 1):
        idx = i % n
        r = radius * (values[idx] / max_value)
        x, y = point(axis_angle(idx), r)
        if i == 0:
            data_elements.append(cv.Path.MoveTo(x, y))
        else:
            data_elements.append(cv.Path.LineTo(x, y))
    shapes.append(cv.Path(data_elements, paint=ft.Paint(
        style=ft.PaintingStyle.FILL, color=ft.Colors.with_opacity(0.25, PRIMARY_BLUE))))
    shapes.append(cv.Path(data_elements, paint=ft.Paint(
        style=ft.PaintingStyle.STROKE, stroke_width=2, color=PRIMARY_BLUE)))

    # Data point dots
    for i in range(n):
        r = radius * (values[i] / max_value)
        x, y = point(axis_angle(i), r)
        shapes.append(cv.Circle(x, y, 3, paint=ft.Paint(
            style=ft.PaintingStyle.FILL, color=PRIMARY_BLUE)))

    canvas = cv.Canvas(shapes, width=size, height=size)

    # Axis labels, positioned around the outside of the web
    label_controls = [ft.Container(canvas)]
    label_radius = radius + 22
    for i, label in enumerate(labels):
        x, y = point(axis_angle(i), label_radius)
        label_controls.append(
            ft.Container(
                content=ft.Text(label, size=12, color=TEXT_SECONDARY),
                left=x - 30,
                top=y - 8,
                width=60,
                alignment=ft.alignment.center,
            )
        )

    stack = ft.Stack(label_controls, width=size, height=size)

    return ft.Container(
        content=ft.Column(
            [
                ft.Text("Average Score by Criterion", size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(height=16),
                ft.Container(stack, alignment=ft.alignment.center),
            ],
            spacing=0,
        ),
        padding=ft.padding.all(24),
        bgcolor=CARD_BG_COLOR,
        border_radius=12,
        border=ft.border.all(1, BORDER_COLOR),
        expand=True,
    )


# ─────────────────────────────────────────────────────────────────
# Per-Criterion Average Scores — Bar Chart
# ─────────────────────────────────────────────────────────────────
def build_bar_chart(categories, values, max_y=100):
    bar_groups = []
    for i, (cat, val) in enumerate(zip(categories, values)):
        bar_groups.append(
            ft.BarChartGroup(
                x=i,
                bar_rods=[
                    ft.BarChartRod(
                        from_y=0,
                        to_y=val,
                        width=24,
                        color=PRIMARY_BLUE,
                        border_radius=ft.border_radius.only(top_left=4, top_right=4),
                        tooltip=f"{cat}: {val}%",
                    )
                ],
            )
        )

    chart = ft.BarChart(
        bar_groups=bar_groups,
        border=ft.border.only(bottom=ft.BorderSide(1, BORDER_COLOR)),
        left_axis=ft.ChartAxis(
            labels_size=40,
            title=None,
            labels=[
                ft.ChartAxisLabel(value=v, label=ft.Text(f"{v}%", size=11, color=TEXT_TERTIARY))
                for v in range(0, max_y + 1, 25)
            ],
        ),
        bottom_axis=ft.ChartAxis(
            labels_size=32,
            labels=[
                ft.ChartAxisLabel(value=i, label=ft.Text(cat, size=11, color=TEXT_TERTIARY))
                for i, cat in enumerate(categories)
            ],
        ),
        horizontal_grid_lines=ft.ChartGridLines(color=GRID_COLOR, width=1),
        max_y=max_y,
        interactive=True,
        height=280,
    )

    return ft.Container(
        content=ft.Column(
            [
                ft.Text("Per-Criterion Average Scores", size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(height=16),
                chart,
            ],
            spacing=0,
        ),
        padding=ft.padding.all(24),
        bgcolor=CARD_BG_COLOR,
        border_radius=12,
        border=ft.border.all(1, BORDER_COLOR),
    )


# ─────────────────────────────────────────────────────────────────
# Main page
# ─────────────────────────────────────────────────────────────────
def main(page: ft.Page, nav=None):
    page.title = "QualCheck - Admin Analytics"
    page.scroll = ft.ScrollMode.AUTO
    page.bgcolor = BG_COLOR
    page.theme_mode = ft.ThemeMode.LIGHT

    # ── Real data, last 30 days ──
    summary = fetch_analytics_summary(days=30)

    total_evaluations = summary["total_evaluations"]
    evaluations_delta = summary["evaluations_delta"]
    avg_similarity_score = summary["avg_similarity_score"]

    fully_pct = summary["fully_pct"]
    partial_pct = summary["partial_pct"]
    irrelevant_pct = summary["irrelevant_pct"]

    criterion_labels = summary["criterion_labels"]
    criterion_values = summary["criterion_values"]
    has_criterion_data = len(criterion_labels) >= 3  # radar needs >=3 axes to mean anything

    # Analytics header
    analytics_header = ft.Row(
        [
            ft.Text("Analytics", size=22, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ft.Container(expand=True),
            ft.Text("Last 30 days", size=13, color=TEXT_SECONDARY),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    # Stats cards row
    stats_row = ft.Row(
        [
            build_stat_card("Total Evaluations", total_evaluations, evaluations_delta, PRIMARY_BLUE),
            ft.Container(width=16),
            build_stat_card("Avg. Similarity Score", f"{avg_similarity_score * 100:.1f}%",
                            "Across all submissions", SUCCESS),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    # Pie chart + radar chart row
    radar_section = (
        build_radar_chart(criterion_labels, criterion_values)
        if has_criterion_data
        else _empty_chart_placeholder(
            "Average Score by Criterion",
            "Not enough evaluations with per-criterion scores yet.",
        )
    )
    charts_row = ft.Row(
        [
            build_pie_chart(fully_pct, partial_pct, irrelevant_pct),
            ft.Container(width=16),
            radar_section,
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    # Bar chart (full width)
    bar_chart_section = (
        build_bar_chart(criterion_labels, criterion_values)
        if has_criterion_data
        else _empty_chart_placeholder(
            "Per-Criterion Average Scores",
            "Not enough evaluations with per-criterion scores yet.",
        )
    )

    # Main content
    main_content = ft.Container(
        content=ft.Column(
            [
                analytics_header,
                ft.Container(height=20),
                stats_row,
                ft.Container(height=24),
                charts_row,
                ft.Container(height=24),
                bar_chart_section,
                ft.Container(height=40),
            ],
            spacing=0,
        ),
        padding=ft.padding.symmetric(horizontal=32),
    )

    if nav:
        nav.main_content = main_content
    else:
        page.add(main_content)


if __name__ == "__main__":
    ft.app(target=main)