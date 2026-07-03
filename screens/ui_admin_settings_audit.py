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


def main(page: ft.Page, nav=None):
    page.title = "QualCheck Admin - Settings & Audit"
    page.scroll = ft.ScrollMode.AUTO
    page.bgcolor = BG_COLOR

    # --- Admin Panel Header (fallback when not using admin navigation) ---
    if not nav:
        shield_icon = ft.Container(
            content=ft.Icon(ft.Icons.SHIELD, size=20, color=TEXT_WHITE),
            width=36,
            height=36,
            bgcolor="#a855f7",
            border_radius=8,
            alignment=ft.alignment.center,
        )

        admin_header = ft.Container(
            content=ft.Row(
                [
                    ft.Row(
                        [
                            shield_icon,
                            ft.Container(width=12),
                            ft.Column(
                                [
                                    ft.Text("Admin Panel", size=22, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                                    ft.Container(height=4),
                                    ft.Text("System administration & analytics", size=13, color=TEXT_SECONDARY),
                                ],
                                spacing=0,
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(expand=True),
                    ft.Container(
                        content=ft.Text("Administrator", size=12, weight=ft.FontWeight.W_600, color="#7e22ce"),
                        padding=ft.padding.symmetric(horizontal=12, vertical=6),
                        bgcolor="#f3e8ff",
                        border_radius=16,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.symmetric(horizontal=32, vertical=20),
        )
    else:
        admin_header = None

    # --- Scoring Thresholds Section ---
    scoring_label = ft.Text("Scoring Thresholds", size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)
    scoring_subtitle = ft.Text("Adjust the similarity score cutoffs used to classify each response", size=13, color=TEXT_TERTIARY)

    # Threshold sliders with full-width layout matching the screenshot
    fully_relevant_value = ft.Text("75%", size=14, weight=ft.FontWeight.W_600, color=SUCCESS)
    fully_relevant_slider = ft.Slider(
        value=75,
        min=0,
        max=100,
        active_color=PRIMARY_BLUE,
        expand=True,
    )

    partially_relevant_value = ft.Text("50%", size=14, weight=ft.FontWeight.W_600, color=WARNING)
    partially_relevant_slider = ft.Slider(
        value=50,
        min=0,
        max=100,
        active_color=PRIMARY_BLUE,
        expand=True,
    )

    threshold_row1 = ft.Column(
        [
            ft.Text("Fully Relevant ≥", size=13, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY),
            ft.Container(height=8),
            ft.Row(
                [fully_relevant_slider, ft.Container(width=12), fully_relevant_value],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        ],
        spacing=0,
    )

    threshold_row2 = ft.Column(
        [
            ft.Text("Partially Relevant ≥", size=13, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY),
            ft.Container(height=8),
            ft.Row(
                [partially_relevant_slider, ft.Container(width=12), partially_relevant_value],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        ],
        spacing=0,
    )

    def on_save_thresholds(e):
        print("Save thresholds clicked")

    save_thresholds_btn = ft.Container(
        content=ft.Text("Save Thresholds", size=13, weight=ft.FontWeight.W_600, color=TEXT_WHITE),
        width=150,
        height=38,
        border_radius=8,
        bgcolor=PRIMARY_BLUE,
        alignment=ft.alignment.center,
        on_click=on_save_thresholds,
        ink=True,
    )

    scoring_section = ft.Container(
        content=ft.Column(
            [
                scoring_label,
                ft.Container(height=4),
                scoring_subtitle,
                ft.Container(height=24),
                threshold_row1,
                ft.Container(height=20),
                threshold_row2,
                ft.Container(height=24),
                ft.Row([save_thresholds_btn], alignment=ft.MainAxisAlignment.START),
            ],
            spacing=0,
        ),
        padding=ft.padding.all(24),
        bgcolor=CARD_BG_COLOR,
        border_radius=12,
        border=ft.border.all(1, BORDER_COLOR),
    )

    # --- Audit Log Section (timeline-style matching the screenshot) ---
    def create_audit_entry(action_text, detail_text, user_email, timestamp):
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.ACCESS_TIME, size=16, color=TEXT_TERTIARY),
                    ft.Container(width=12),
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(action_text, size=13, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                                    ft.Text("  —  ", size=13, color=TEXT_TERTIARY),
                                    ft.Text(detail_text, size=13, color=TEXT_SECONDARY),
                                ],
                                spacing=0,
                                wrap=True,
                            ),
                            ft.Container(height=2),
                            ft.Text(f"{user_email} · {timestamp}", size=12, color=TEXT_TERTIARY),
                        ],
                        spacing=0,
                        expand=True,
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            padding=ft.padding.symmetric(vertical=14),
            border=ft.border.only(bottom=ft.BorderSide(1, BORDER_COLOR)),
        )

    audit_entries = ft.Column(
        [
            create_audit_entry(
                "Override classification",
                "maria_reyes.pdf → Fully Relevant",
                "admin@qualcheck.edu",
                "2025-06-24 09:45",
            ),
            create_audit_entry(
                "Uploaded 8 PDFs",
                "Sorting Algorithm Report batch",
                "jchen@university.edu",
                "2025-06-23 14:00",
            ),
            create_audit_entry(
                "Override classification",
                "marco_santos.pdf → Partially Relevant",
                "admin@qualcheck.edu",
                "2025-06-22 12:10",
            ),
            create_audit_entry(
                "Added user",
                "alee@university.edu (Evaluator)",
                "admin@qualcheck.edu",
                "2025-06-21 10:30",
            ),
        ],
        spacing=0,
    )

    audit_section = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.ACCESS_TIME, size=20, color=TEXT_TERTIARY),
                        ft.Container(width=8),
                        ft.Text("Audit Log", size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(height=16),
                audit_entries,
            ],
            spacing=0,
        ),
        padding=ft.padding.all(24),
        bgcolor=CARD_BG_COLOR,
        border_radius=12,
        border=ft.border.all(1, BORDER_COLOR),
    )

    # --- Main Content ---
    if admin_header:
        main_content = ft.Container(
            content=ft.Column(
                [
                    admin_header,
                    ft.Container(height=8),
                    ft.Container(content=scoring_section, padding=ft.padding.symmetric(horizontal=32)),
                    ft.Container(height=20),
                    ft.Container(content=audit_section, padding=ft.padding.symmetric(horizontal=32)),
                    ft.Container(height=40),
                ],
                spacing=0,
            ),
        )
    else:
        main_content = ft.Container(
            content=ft.Column(
                [
                    ft.Container(content=scoring_section, padding=ft.padding.symmetric(horizontal=32)),
                    ft.Container(height=20),
                    ft.Container(content=audit_section, padding=ft.padding.symmetric(horizontal=32)),
                    ft.Container(height=40),
                ],
                spacing=0,
            ),
        )

    # --- Page Layout ---
    page.add(main_content)
    if nav:
        nav.main_content = main_content


if __name__ == "__main__":
    ft.app(target=main)