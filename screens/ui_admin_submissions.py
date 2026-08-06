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
from services.submissions_services import fetch_submissions
from services.csv_service import export_submissions_to_csv


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

    # --- Submissions data ---
    SUBMISSIONS_DATA = fetch_submissions()

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

    def build_row(item):
        return ft.DataRow(
            cells=[
                file_cell(item["file"]),
                ft.DataCell(ft.Text(item["score"], size=13, weight=ft.FontWeight.W_600, color=PRIMARY_BLUE)),
                classification_cell(item["classification"]),
                ft.DataCell(ft.Text(item["type"], size=13, color=TEXT_SECONDARY)),
                ft.DataCell(ft.Text(item["evaluator"], size=13, color=TEXT_SECONDARY)),
                ft.DataCell(ft.Text(item["date"], size=13, color=TEXT_SECONDARY)),
            ],
        )

    def empty_row(msg="No submissions found"):
        return [
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(msg, color=TEXT_SECONDARY)),
            ] + [ft.DataCell(ft.Text("")) for _ in range(5)])
        ]

    # --- Search + Classification Filter state ---
    search_state = {"query": "", "classification": "all"}

    def matches(item, query, classification):
        if classification != "all" and classification not in item["classification"]:
            return False
        if query:
            haystack = f"{item['file']} {item['evaluator']} {item['type']}".lower()
            if query.lower() not in haystack:
                return False
        return True

    def get_filtered_data():
        return [item for item in SUBMISSIONS_DATA if matches(item, search_state["query"], search_state["classification"])]

    def rebuild_rows(e=None):
        style_filter_pills()
        filtered = get_filtered_data()
        submissions_table.rows = [build_row(item) for item in filtered] if filtered else empty_row()
        page.update()

    # --- Search bar ---
    search_bar = ft.TextField(
        hint_text="Search student, evaluator, subject…",
        prefix_icon=ft.Icons.SEARCH,
        border_color=INPUT_BORDER,
        focused_border_color=PRIMARY_BLUE,
        bgcolor=INPUT_BG,
        border_radius=8,
        height=42,
        text_size=13,
        content_padding=ft.padding.symmetric(horizontal=14, vertical=8),
        hint_style=ft.TextStyle(color=INPUT_HINT, size=13),
        expand=True,
        on_change=lambda e: (search_state.update({"query": e.control.value or ""}), rebuild_rows()),
    )

    # --- Classification filter pills ---
    FILTERS = [("all", "All"), ("Fully Relevant", "Fully Relevant"),
               ("Partially Relevant", "Partially Relevant"), ("Irrelevant", "Irrelevant")]

    def make_filter_pill(key, label):
        def on_click(e):
            search_state["classification"] = key
            rebuild_rows()

        return ft.Container(
            content=ft.Text(label, size=13, weight=ft.FontWeight.W_600),
            padding=ft.padding.symmetric(horizontal=14, vertical=6),
            border_radius=14,
            ink=True,
            on_click=on_click,
        )

    pills = {key: make_filter_pill(key, label) for key, label in FILTERS}

    def style_filter_pills():
        for key, pill in pills.items():
            selected = search_state["classification"] == key
            pill.bgcolor = PRIMARY_BLUE if selected else None
            pill.content.color = TEXT_WHITE if selected else TEXT_TERTIARY

    style_filter_pills()

    # --- Filter Container (Hidden by default so it doesn't stay open) ---
    pills_container = ft.Row(
        [
            pills["all"],
            ft.Container(width=4),
            pills["Fully Relevant"],
            ft.Container(width=4),
            pills["Partially Relevant"],
            ft.Container(width=4),
            pills["Irrelevant"],
        ],
        visible=False,  # Hidden by default
        animate_opacity=200,
    )

    def toggle_filter_visibility(e):
        pills_container.visible = not pills_container.visible
        filter_btn.icon_color = PRIMARY_BLUE if pills_container.visible else TEXT_TERTIARY
        page.update()

    filter_btn = ft.IconButton(
        icon=ft.Icons.FILTER_LIST,
        icon_color=TEXT_TERTIARY,
        icon_size=22,
        tooltip="Toggle Filters",
        on_click=toggle_filter_visibility,
    )

    # --- CSV Export Logic ---
    def on_csv_result(e: ft.FilePickerResultEvent):
        if e.path:
            current_data = get_filtered_data()
            success = export_submissions_to_csv(current_data, e.path)
            
            snack_message = "CSV exported successfully!" if success else "Failed to export CSV."
            snack_color = SUCCESS if success else ERROR
            
            page.snack_bar = ft.SnackBar(
                content=ft.Text(snack_message, color=TEXT_WHITE),
                bgcolor=snack_color,
            )
            page.snack_bar.open = True
            page.update()

    file_picker = ft.FilePicker(on_result=on_csv_result)
    page.overlay.append(file_picker)

    def on_export_csv(e):
        file_picker.save_file(
            dialog_title="Export Submissions to CSV",
            file_name="submissions_export.csv",
            allowed_extensions=["csv"],
        )

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
                search_bar,
                ft.Container(width=12),
                filter_btn,
                pills_container,
                ft.Container(width=12),
                export_btn,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.padding.symmetric(horizontal=24, vertical=16),
    )

    # --- Submissions Table ---
    submissions_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("STUDENT FILE", size=11, weight=ft.FontWeight.BOLD, color=TEXT_TERTIARY)),
            ft.DataColumn(ft.Text("SCORE", size=11, weight=ft.FontWeight.BOLD, color=TEXT_TERTIARY)),
            ft.DataColumn(ft.Text("CLASSIFICATION", size=11, weight=ft.FontWeight.BOLD, color=TEXT_TERTIARY)),
            ft.DataColumn(ft.Text("TYPE", size=11, weight=ft.FontWeight.BOLD, color=TEXT_TERTIARY)),
            ft.DataColumn(ft.Text("EVALUATOR", size=11, weight=ft.FontWeight.BOLD, color=TEXT_TERTIARY)),
            ft.DataColumn(ft.Text("DATE", size=11, weight=ft.FontWeight.BOLD, color=TEXT_TERTIARY)),
        ],
        border=ft.border.all(1, BORDER_COLOR),
        border_radius=8,
        horizontal_lines=ft.border.BorderSide(1, BORDER_COLOR),
        vertical_lines=None,
        column_spacing=54,
        heading_row_color=SECTION_BG_COLOR,
        data_row_min_height=56,
        show_bottom_border=True,
        rows=[build_row(item) for item in SUBMISSIONS_DATA] if SUBMISSIONS_DATA else empty_row(),
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