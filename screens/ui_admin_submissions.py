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
    page.title = "QualCheck Admin - Submissions"
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

    # --- Filter Section ---
    filter_all = ft.Container(
        content=ft.Text("All", size=12, weight=ft.FontWeight.W_600, color=TEXT_WHITE),
        bgcolor=PRIMARY_BLUE,
        padding=ft.padding.symmetric(horizontal=14, vertical=6),
        border_radius=14,
    )

    filter_fully = ft.Text("Fully Relevant", size=13, color=TEXT_TERTIARY)
    filter_partially = ft.Text("Partially Relevant", size=13, color=TEXT_TERTIARY)
    filter_irrelevant = ft.Text("Irrelevant", size=13, color=TEXT_TERTIARY)

    def on_export_csv(e):
        print("Export CSV clicked")

    # Export CSV green button matching submissions spec
    export_btn = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.DOWNLOAD, size=16, color=TEXT_WHITE),
                ft.Text("Export CSV", size=13, weight=ft.FontWeight.W_600, color=TEXT_WHITE),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=4,
        ),
        width=130,
        height=40,
        border_radius=20,
        bgcolor="#22c55e",
        alignment=ft.alignment.center,
        on_click=on_export_csv,
        ink=True,
    )

    filter_section = ft.Container(
        content=ft.Row(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.FILTER_LIST, size=20, color=TEXT_TERTIARY),
                        ft.Container(width=8),
                        filter_all,
                        ft.Container(width=16),
                        filter_fully,
                        ft.Container(width=16),
                        filter_partially,
                        ft.Container(width=16),
                        filter_irrelevant,
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(expand=True),
                export_btn,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.padding.symmetric(horizontal=24, vertical=12),
    )

    # --- Classification Badge Helpers ---
    def classification_badge(label):
        colors = {
            "Fully Relevant": (SUCCESS, "#dcfce7"),
            "Partially Relevant": ("#ca8a04", "#fef9c3"),
            "Irrelevant": (ERROR, "#fee2e2"),
        }
        text_color, bg_color = colors.get(label, (TEXT_SECONDARY, SECTION_BG_COLOR))
        return ft.Container(
            content=ft.Text(label, size=11, color=text_color, weight=ft.FontWeight.W_600),
            bgcolor=bg_color,
            padding=ft.padding.symmetric(horizontal=10, vertical=3),
            border_radius=12,
        )

    def classification_cell(labels):
        if isinstance(labels, str):
            labels = [labels]
        if len(labels) == 1:
            return ft.DataCell(classification_badge(labels[0]))
        return ft.DataCell(ft.Column([classification_badge(l) for l in labels], spacing=2))

    def file_cell(name):
        return ft.DataCell(
            ft.Row(
                [
                    ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, size=18, color=TEXT_TERTIARY),
                    ft.Container(width=6),
                    ft.Text(name, size=13, color=TEXT_PRIMARY),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

    def override_cell():
        return ft.DataCell(
            ft.Row(
                [
                    ft.Icon(ft.Icons.EDIT, size=14, color=PRIMARY_BLUE),
                    ft.Text("Override", size=12, color=PRIMARY_BLUE, weight=ft.FontWeight.W_500),
                ],
                spacing=4,
            )
        )

    # --- Submissions Table ---
    submissions_table = ft.DataTable(
        columns=[
            ft.DataColumn(
                ft.Text("STUDENT FILE", size=11, weight=ft.FontWeight.BOLD, color=TEXT_TERTIARY),
            ),
            ft.DataColumn(
                ft.Text("SCORE", size=11, weight=ft.FontWeight.BOLD, color=TEXT_TERTIARY),
            ),
            ft.DataColumn(
                ft.Text("CLASSIFICATION", size=11, weight=ft.FontWeight.BOLD, color=TEXT_TERTIARY),
            ),
            ft.DataColumn(
                ft.Text("TYPE", size=11, weight=ft.FontWeight.BOLD, color=TEXT_TERTIARY),
            ),
            ft.DataColumn(
                ft.Text("EVALUATOR", size=11, weight=ft.FontWeight.BOLD, color=TEXT_TERTIARY),
            ),
            ft.DataColumn(
                ft.Text("DATE", size=11, weight=ft.FontWeight.BOLD, color=TEXT_TERTIARY),
            ),
            ft.DataColumn(
                ft.Text("ACTIONS", size=11, weight=ft.FontWeight.BOLD, color=TEXT_TERTIARY),
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
                    file_cell("juan_dela_cruz.pdf"),
                    ft.DataCell(ft.Text("88%", size=13, weight=ft.FontWeight.W_600, color=PRIMARY_BLUE)),
                    classification_cell("Fully Relevant"),
                    ft.DataCell(ft.Text("Essay", size=13, color=TEXT_SECONDARY)),
                    ft.DataCell(ft.Text("Prof. Santos", size=13, color=TEXT_SECONDARY)),
                    ft.DataCell(ft.Text("2025-06-24 09:12", size=13, color=TEXT_SECONDARY)),
                    override_cell(),
                ],
            ),
            ft.DataRow(
                cells=[
                    file_cell("maria_reyes.pdf"),
                    ft.DataCell(ft.Text("63%", size=13, weight=ft.FontWeight.W_600, color=PRIMARY_BLUE)),
                    classification_cell(["Fully Relevant", "Partially Relevant"]),
                    ft.DataCell(ft.Text("Essay", size=13, color=TEXT_SECONDARY)),
                    ft.DataCell(ft.Text("Prof. Santos", size=13, color=TEXT_SECONDARY)),
                    ft.DataCell(ft.Text("2025-06-24 09:13", size=13, color=TEXT_SECONDARY)),
                    override_cell(),
                ],
            ),
            ft.DataRow(
                cells=[
                    file_cell("pedro_garcia.pdf"),
                    ft.DataCell(ft.Text("41%", size=13, weight=ft.FontWeight.W_600, color=PRIMARY_BLUE)),
                    classification_cell("Irrelevant"),
                    ft.DataCell(ft.Text("Essay", size=13, color=TEXT_SECONDARY)),
                    ft.DataCell(ft.Text("Prof. Santos", size=13, color=TEXT_SECONDARY)),
                    ft.DataCell(ft.Text("2025-06-24 09:14", size=13, color=TEXT_SECONDARY)),
                    override_cell(),
                ],
            ),
            ft.DataRow(
                cells=[
                    file_cell("ana_torres.pdf"),
                    ft.DataCell(ft.Text("79%", size=13, weight=ft.FontWeight.W_600, color=PRIMARY_BLUE)),
                    classification_cell("Fully Relevant"),
                    ft.DataCell(ft.Text("Code Report", size=13, color=TEXT_SECONDARY)),
                    ft.DataCell(ft.Text("Prof. Chen", size=13, color=TEXT_SECONDARY)),
                    ft.DataCell(ft.Text("2025-06-23 14:05", size=13, color=TEXT_SECONDARY)),
                    override_cell(),
                ],
            ),
            ft.DataRow(
                cells=[
                    file_cell("carlos_mendoza.pdf"),
                    ft.DataCell(ft.Text("55%", size=13, weight=ft.FontWeight.W_600, color=PRIMARY_BLUE)),
                    classification_cell("Partially Relevant"),
                    ft.DataCell(ft.Text("Code Report", size=13, color=TEXT_SECONDARY)),
                    ft.DataCell(ft.Text("Prof. Chen", size=13, color=TEXT_SECONDARY)),
                    ft.DataCell(ft.Text("2025-06-23 14:06", size=13, color=TEXT_SECONDARY)),
                    override_cell(),
                ],
            ),
            ft.DataRow(
                cells=[
                    file_cell("sofia_lim.pdf"),
                    ft.DataCell(ft.Text("91%", size=13, weight=ft.FontWeight.W_600, color=PRIMARY_BLUE)),
                    classification_cell("Fully Relevant"),
                    ft.DataCell(ft.Text("Short Answer", size=13, color=TEXT_SECONDARY)),
                    ft.DataCell(ft.Text("Prof. Lee", size=13, color=TEXT_SECONDARY)),
                    ft.DataCell(ft.Text("2025-06-22 11:30", size=13, color=TEXT_SECONDARY)),
                    override_cell(),
                ],
            ),
            ft.DataRow(
                cells=[
                    file_cell("marco_santos.pdf"),
                    ft.DataCell(ft.Text("48%", size=13, weight=ft.FontWeight.W_600, color=PRIMARY_BLUE)),
                    classification_cell(["Partially Relevant", "Irrelevant"]),
                    ft.DataCell(ft.Text("Short Answer", size=13, color=TEXT_SECONDARY)),
                    ft.DataCell(ft.Text("Prof. Lee", size=13, color=TEXT_SECONDARY)),
                    ft.DataCell(ft.Text("2025-06-22 11:31", size=13, color=TEXT_SECONDARY)),
                    override_cell(),
                ],
            ),
            ft.DataRow(
                cells=[
                    file_cell("nina_cruz.pdf"),
                    ft.DataCell(ft.Text("82%", size=13, weight=ft.FontWeight.W_600, color=PRIMARY_BLUE)),
                    classification_cell("Fully Relevant"),
                    ft.DataCell(ft.Text("Code Report", size=13, color=TEXT_SECONDARY)),
                    ft.DataCell(ft.Text("Prof. Chen", size=13, color=TEXT_SECONDARY)),
                    ft.DataCell(ft.Text("2025-06-21 16:20", size=13, color=TEXT_SECONDARY)),
                    override_cell(),
                ],
            ),
        ],
    )

    # --- Submissions Card container ---
    submissions_section = ft.Container(
        content=ft.Column(
            [
                filter_section,
                ft.Container(
                    content=submissions_table,
                    padding=ft.padding.symmetric(horizontal=24, vertical=0),
                ),
            ],
            spacing=0,
        ),
        padding=ft.padding.symmetric(horizontal=0, vertical=24),
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
                        content=submissions_section,
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
                        content=submissions_section,
                        padding=ft.padding.symmetric(horizontal=32),
                    ),
                    ft.Container(height=40),
                ],
                spacing=0,
            ),
        )

    # --- Page Layout ---
    if nav:
        nav.main_content = main_content
    else:
        page.add(main_content)


if __name__ == "__main__":
    ft.app(target=main)