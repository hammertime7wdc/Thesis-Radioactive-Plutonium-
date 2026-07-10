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
    page.title = "QualCheck - Admin Analytics"
    page.scroll = ft.ScrollMode.AUTO
    page.bgcolor = BG_COLOR
    page.theme_mode = ft.ThemeMode.LIGHT

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
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row([ft.Icon(ft.Icons.ASSIGNMENT_OUTLINED, size=20, color=PRIMARY_BLUE), ft.Container(width=8), ft.Text("Total Evaluations", size=13, color=TEXT_SECONDARY)], spacing=0),
                        ft.Container(height=8),
                        ft.Text("0", size=24, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ],
                    spacing=0,
                ),
                padding=ft.padding.all(20),
                bgcolor=CARD_BG_COLOR,
                border_radius=12,
                border=ft.border.all(1, BORDER_COLOR),
                expand=True,
            ),
            ft.Container(width=16),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row([ft.Icon(ft.Icons.PEOPLE_OUTLINED, size=20, color="#8b5cf6"), ft.Container(width=8), ft.Text("Active Users", size=13, color=TEXT_SECONDARY)], spacing=0),
                        ft.Container(height=8),
                        ft.Text("0", size=24, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ],
                    spacing=0,
                ),
                padding=ft.padding.all(20),
                bgcolor=CARD_BG_COLOR,
                border_radius=12,
                border=ft.border.all(1, BORDER_COLOR),
                expand=True,
            ),
            ft.Container(width=16),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row([ft.Icon(ft.Icons.TRENDING_UP_OUTLINED, size=20, color="#10b981"), ft.Container(width=8), ft.Text("Avg Score", size=13, color=TEXT_SECONDARY)], spacing=0),
                        ft.Container(height=8),
                        ft.Text("N/A", size=24, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ],
                    spacing=0,
                ),
                padding=ft.padding.all(20),
                bgcolor=CARD_BG_COLOR,
                border_radius=12,
                border=ft.border.all(1, BORDER_COLOR),
                expand=True,
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    # Recent activity section
    recent_activity_section = ft.Container(
        content=ft.Column(
            [
                ft.Row([ft.Text("Recent Activity", size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)], spacing=0),
                ft.Container(height=16),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Container(
                                content=ft.Row([ft.Icon(ft.Icons.HISTORY_OUTLINED, size=16, color=TEXT_TERTIARY), ft.Container(width=12), ft.Text("No recent activity", size=13, color=TEXT_SECONDARY)], spacing=0),
                                padding=ft.padding.symmetric(vertical=12),
                            ),
                        ],
                        spacing=0,
                    ),
                    bgcolor=SECTION_BG_COLOR,
                    border_radius=8,
                    padding=ft.padding.all(16),
                ),
            ],
            spacing=0,
        ),
        padding=ft.padding.all(24),
        bgcolor=CARD_BG_COLOR,
        border_radius=12,
        border=ft.border.all(1, BORDER_COLOR),
    )

    # Main content
    main_content = ft.Container(
        content=ft.Column(
            [
                analytics_header,
                ft.Container(height=20),
                stats_row,
                ft.Container(height=24),
                recent_activity_section,
                ft.Container(height=40),
            ],
            spacing=0,
        ),
        padding=ft.padding.symmetric(horizontal=32),
    )

    page.add(main_content)
    if nav:
        nav.main_content = main_content


if __name__ == "__main__":
    ft.app(target=main)
