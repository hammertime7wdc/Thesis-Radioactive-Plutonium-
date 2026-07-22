import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import flet as ft
from utils.utils import (
    BG_COLOR, CARD_BG_COLOR, SECTION_BG_COLOR,
    PRIMARY_BLUE, PRIMARY_BLUE_DARK, PRIMARY_BLUE_LIGHT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_TERTIARY, TEXT_WHITE,
    BORDER_COLOR, BORDER_COLOR_DARK,
    BUTTON_PRIMARY_BG, BUTTON_PRIMARY_TEXT, BUTTON_SECONDARY_BG, BUTTON_SECONDARY_TEXT, BUTTON_SECONDARY_BORDER,
    INPUT_BG, INPUT_BORDER, INPUT_TEXT, INPUT_HINT,
    SUCCESS, WARNING, ERROR
)

# ============================================================
# PLACEHOLDER DATA
# ============================================================

PLACEHOLDER_STATS = {
    "total_evaluations": 0,
    "fully_relevant": 0,
    "partially_relevant": 0,
    "irrelevant": 0,
    "avg_similarity_score": 0.0,
}

PLACEHOLDER_OUTPUT_TYPES = [
    ("Short Answer", 0, 0.0),
    ("Essay", 0, 0.0),
    ("Code Report", 0, 0.0),
]

PLACEHOLDER_RECENT_EVALUATIONS = []

def main(page: ft.Page, nav=None, role="evaluator"):
    page.title = "QualCheck - Dashboard"
    page.scroll = ft.ScrollMode.AUTO
    page.bgcolor = BG_COLOR
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------
    dashboard_header = ft.Container(
        content=ft.Column(
            [
                ft.Text("Evaluation Dashboard", size=26, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(height=6),
                ft.Text("Overview of all evaluations processed by QualCheck", size=13, color=TEXT_SECONDARY),
            ],
            spacing=0,
        ),
        padding=ft.padding.only(left=32, right=32, top=32, bottom=16),
    )

    # ------------------------------------------------------------------
    # Top Stat Cards
    # ------------------------------------------------------------------
    def stat_card(accent_color, label, value, subtitle=None, value_color=None):
        content_items = [
            ft.Text(label, size=13, color=TEXT_SECONDARY),
            ft.Container(height=10),
            ft.Text(str(value), size=26, weight=ft.FontWeight.BOLD, color=value_color or TEXT_PRIMARY),
        ]
        if subtitle:
            content_items.append(ft.Container(height=4))
            content_items.append(ft.Text(subtitle, size=11, color=TEXT_TERTIARY))
        else:
            # Add spacer to keep card heights uniform when there is no subtitle
            content_items.append(ft.Container(height=19)) 

        return ft.Container(
            content=ft.Column(content_items, spacing=0),
            padding=ft.padding.all(20),
            bgcolor=CARD_BG_COLOR,
            border_radius=10,
            border=ft.border.only(
                top=ft.border.BorderSide(3, accent_color),
                left=ft.border.BorderSide(1, BORDER_COLOR),
                right=ft.border.BorderSide(1, BORDER_COLOR),
                bottom=ft.border.BorderSide(1, BORDER_COLOR),
            ),
        )

    total = PLACEHOLDER_STATS["total_evaluations"]

    def pct_of_total(n):
        if not total:
            return "0% of total"
        return f"{round((n / total) * 100)}% of total"

    # Using ResponsiveRow to ensure they fit side-by-side flawlessly
    stats_row = ft.ResponsiveRow(
        controls=[
            ft.Container(stat_card(PRIMARY_BLUE, "Total Evaluations", PLACEHOLDER_STATS["total_evaluations"]), col={"sm": 6, "md": 3}),
            ft.Container(stat_card(SUCCESS, "Fully Relevant", PLACEHOLDER_STATS["fully_relevant"],
                      subtitle=pct_of_total(PLACEHOLDER_STATS["fully_relevant"]), value_color=SUCCESS), col={"sm": 6, "md": 3}),
            ft.Container(stat_card(WARNING, "Partially Relevant", PLACEHOLDER_STATS["partially_relevant"],
                      subtitle=pct_of_total(PLACEHOLDER_STATS["partially_relevant"]), value_color=WARNING), col={"sm": 6, "md": 3}),
            ft.Container(stat_card(ERROR, "Irrelevant", PLACEHOLDER_STATS["irrelevant"],
                      subtitle=pct_of_total(PLACEHOLDER_STATS["irrelevant"]), value_color=ERROR), col={"sm": 6, "md": 3}),
        ],
        spacing=16,
        run_spacing=16,
    )

    # ------------------------------------------------------------------
    # Middle Row: Similarity & Output Type
    # ------------------------------------------------------------------
    similarity_score_card = ft.Container(
        content=ft.Column(
            [
                ft.Text("Average Similarity Score", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(height=24),
                ft.Text(
                    f"{PLACEHOLDER_STATS['avg_similarity_score']:.1f}%",
                    size=42, weight=ft.FontWeight.BOLD, color=PRIMARY_BLUE,
                ),
                ft.Container(height=12),
                ft.ProgressBar(
                    value=PLACEHOLDER_STATS["avg_similarity_score"] / 100,
                    bgcolor=SECTION_BG_COLOR,
                    color=PRIMARY_BLUE,
                    height=8,
                    border_radius=4,
                ),
            ],
            spacing=0,
        ),
        padding=ft.padding.all(24),
        bgcolor=CARD_BG_COLOR,
        border_radius=12,
        border=ft.border.all(1, BORDER_COLOR),
    )

    def output_type_row(label, count, progress):
        return ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(label, size=13, color=TEXT_PRIMARY),
                        ft.Text(str(count), size=13, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(height=8),
                ft.ProgressBar(
                    value=progress,
                    bgcolor=SECTION_BG_COLOR,
                    color=PRIMARY_BLUE,
                    height=6,
                    border_radius=3,
                ),
                ft.Container(height=16),
            ],
            spacing=0,
        )

    output_type_card = ft.Container(
        content=ft.Column(
            [
                ft.Text("By Output Type", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(height=20),
                *[output_type_row(label, count, progress) for label, count, progress in PLACEHOLDER_OUTPUT_TYPES],
            ],
            spacing=0,
        ),
        padding=ft.padding.all(24),
        bgcolor=CARD_BG_COLOR,
        border_radius=12,
        border=ft.border.all(1, BORDER_COLOR),
    )

    middle_row = ft.ResponsiveRow(
        controls=[
            ft.Container(similarity_score_card, col={"sm": 12, "md": 6}),
            ft.Container(output_type_card, col={"sm": 12, "md": 6}),
        ],
        spacing=24,
        run_spacing=24,
    )

    # ------------------------------------------------------------------
    # Recent Evaluations section
    # ------------------------------------------------------------------
    def empty_state():
        return ft.Container(
            content=ft.Column(
                [
                    ft.Image(src="https://img.icons8.com/fluency/48/000000/bar-chart.png", width=48, height=48), # Placeholder icon
                    ft.Container(height=12),
                    ft.Text("No evaluations yet. Create your first evaluation to see results here.",
                            size=13, color=TEXT_SECONDARY, text_align=ft.TextAlign.CENTER),
                ],
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(vertical=80),
            alignment=ft.alignment.center,
        )

    if PLACEHOLDER_RECENT_EVALUATIONS:
        # Build out populated rows here later
        recent_content = ft.Column([]) 
    else:
        recent_content = empty_state()

    recent_evaluations_section = ft.Container(
        content=ft.Column(
            [
                ft.Text("Recent Evaluations", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(height=16),
                recent_content,
            ],
            spacing=0,
        ),
        padding=ft.padding.all(24),
        bgcolor=CARD_BG_COLOR,
        border_radius=12,
        border=ft.border.all(1, BORDER_COLOR),
    )

    # ------------------------------------------------------------------
    # Assemble page
    # ------------------------------------------------------------------
    main_content = ft.Container(
        content=ft.Column(
            [
                dashboard_header,
                ft.Container(content=stats_row, padding=ft.padding.symmetric(horizontal=32)),
                ft.Container(height=24),
                ft.Container(content=middle_row, padding=ft.padding.symmetric(horizontal=32)),
                ft.Container(height=24),
                ft.Container(content=recent_evaluations_section, padding=ft.padding.symmetric(horizontal=32)),
                ft.Container(height=40),
            ],
            spacing=0,
        ),
    )

    if nav:
        nav.main_content = main_content
    else:
        page.add(main_content)

if __name__ == "__main__":
    ft.app(target=main)