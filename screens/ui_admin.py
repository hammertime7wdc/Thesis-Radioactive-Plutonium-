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
    page.title = "QualCheck Admin Panel"
    page.scroll = ft.ScrollMode.AUTO
    page.bgcolor = BG_COLOR

    # Only create header if not using admin navigation (navigation handles it)
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

    # Helpers for rendering table cells matching the screenshot
    def create_name_cell(avatar_text, full_name):
        return ft.DataCell(
            ft.Row(
                [
                    ft.Container(
                        content=ft.Text(avatar_text, size=11, weight=ft.FontWeight.BOLD, color=PRIMARY_BLUE),
                        width=24,
                        height=24,
                        border_radius=12,
                        bgcolor="#eff6ff",
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(width=8),
                    ft.Text(full_name, size=13, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

    def create_role_badge(role):
        if role == "Admin":
            return ft.DataCell(
                ft.Container(
                    content=ft.Text("Admin", size=12, color="#7e22ce", weight=ft.FontWeight.W_600),
                    bgcolor="#f3e8ff",
                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                    border_radius=12,
                )
            )
        else:
            return ft.DataCell(
                ft.Container(
                    content=ft.Text("Evaluator", size=12, color=PRIMARY_BLUE, weight=ft.FontWeight.W_600),
                    bgcolor="#eff6ff",
                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                    border_radius=12,
                )
            )

    def create_status_badge(status):
        if status == "Active":
            return ft.DataCell(
                ft.Container(
                    content=ft.Text("Active", size=12, color=SUCCESS, weight=ft.FontWeight.W_600),
                    bgcolor="#ecfdf5",
                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                    border_radius=12,
                )
            )
        else:
            return ft.DataCell(
                ft.Container(
                    content=ft.Text("Inactive", size=12, color=TEXT_SECONDARY, weight=ft.FontWeight.W_600),
                    bgcolor="#f1f5f9",
                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                    border_radius=12,
                )
            )

    # --- Users Table ---
    users_table = ft.DataTable(
        columns=[
            ft.DataColumn(
                ft.Text("NAME", size=12, weight=ft.FontWeight.BOLD, color=TEXT_SECONDARY),
            ),
            ft.DataColumn(
                ft.Text("EMAIL", size=12, weight=ft.FontWeight.BOLD, color=TEXT_SECONDARY),
            ),
            ft.DataColumn(
                ft.Text("ROLE", size=12, weight=ft.FontWeight.BOLD, color=TEXT_SECONDARY),
            ),
            ft.DataColumn(
                ft.Text("SUBJECT", size=12, weight=ft.FontWeight.BOLD, color=TEXT_SECONDARY),
            ),
            ft.DataColumn(
                ft.Text("EVALUATIONS", size=12, weight=ft.FontWeight.BOLD, color=TEXT_SECONDARY),
            ),
            ft.DataColumn(
                ft.Text("JOINED", size=12, weight=ft.FontWeight.BOLD, color=TEXT_SECONDARY),
            ),
            ft.DataColumn(
                ft.Text("STATUS", size=12, weight=ft.FontWeight.BOLD, color=TEXT_SECONDARY),
            ),
        ],
        border=ft.border.all(1, BORDER_COLOR),
        border_radius=8,
        horizontal_lines=ft.border.BorderSide(1, BORDER_COLOR),
        vertical_lines=None,
        column_spacing=54,
        heading_row_color=SECTION_BG_COLOR,
        data_row_min_height=56,
        show_bottom_border=True,
        rows=[
            ft.DataRow(
                cells=[
                    create_name_cell("AA", "Admin Account"),
                    ft.DataCell(ft.Text("admin@qualcheck.edu", size=13, color=TEXT_SECONDARY)),
                    create_role_badge("Admin"),
                    ft.DataCell(ft.Text("System", size=13, color=TEXT_SECONDARY)),
                    ft.DataCell(ft.Text("0", size=13, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY)),
                    ft.DataCell(ft.Text("2025-01-01", size=13, color=TEXT_SECONDARY)),
                    create_status_badge("Active"),
                ],
            ),
            ft.DataRow(
                cells=[
                    create_name_cell("PM", "Prof. Maria Santos"),
                    ft.DataCell(ft.Text("msantos@university.edu", size=13, color=TEXT_SECONDARY)),
                    create_role_badge("Evaluator"),
                    ft.DataCell(ft.Text("Data Structures", size=13, color=TEXT_SECONDARY)),
                    ft.DataCell(ft.Text("34", size=13, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY)),
                    ft.DataCell(ft.Text("2025-05-10", size=13, color=TEXT_SECONDARY)),
                    create_status_badge("Active"),
                ],
            ),
            ft.DataRow(
                cells=[
                    create_name_cell("PJ", "Prof. James Chen"),
                    ft.DataCell(ft.Text("jchen@university.edu", size=13, color=TEXT_SECONDARY)),
                    create_role_badge("Evaluator"),
                    ft.DataCell(ft.Text("Programming", size=13, color=TEXT_SECONDARY)),
                    ft.DataCell(ft.Text("28", size=13, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY)),
                    ft.DataCell(ft.Text("2025-05-12", size=13, color=TEXT_SECONDARY)),
                    create_status_badge("Active"),
                ],
            ),
            ft.DataRow(
                cells=[
                    create_name_cell("PA", "Prof. Anna Lee"),
                    ft.DataCell(ft.Text("alee@university.edu", size=13, color=TEXT_SECONDARY)),
                    create_role_badge("Evaluator"),
                    ft.DataCell(ft.Text("Algorithms", size=13, color=TEXT_SECONDARY)),
                    ft.DataCell(ft.Text("19", size=13, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY)),
                    ft.DataCell(ft.Text("2025-06-01", size=13, color=TEXT_SECONDARY)),
                    create_status_badge("Inactive"),
                ],
            ),
        ],
    )

    # --- Add User Button ---
    def on_add_user(e):
        print("Add user button clicked")

    add_user_btn = ft.ElevatedButton(
        content=ft.Row(
            [ft.Icon(ft.Icons.ADD, size=18, color=TEXT_WHITE), ft.Text("Add User", size=13, weight=ft.FontWeight.W_600, color=TEXT_WHITE)],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=4,
        ),
        width=120,
        height=40,
        style=ft.ButtonStyle(
            bgcolor=PRIMARY_BLUE,
            shape=ft.RoundedRectangleBorder(radius=8),
            elevation=0,
        ),
        on_click=on_add_user,
    )

    # --- Users Section Header ---
    users_header = ft.Row(
        [
            ft.Text("4 accounts", size=13, color=TEXT_SECONDARY),
            ft.Container(expand=True),
            add_user_btn,
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    # --- Users Section ---
    users_section = ft.Container(
        content=ft.Column(
            [
                users_header,
                ft.Container(height=20),
                ft.Container(
                    content=users_table,
                    padding=ft.padding.all(0),
                ),
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
                    ft.Container(
                        content=users_section,
                        padding=ft.padding.symmetric(horizontal=32),
                    ),
                    ft.Container(height=40),
                ],
                spacing=0,
            ),
        )
    else:
        main_content = ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=users_section,
                        padding=ft.padding.symmetric(horizontal=32),
                    ),
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