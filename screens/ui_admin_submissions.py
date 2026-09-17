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

    def file_cell(name, on_tap=None):
        return ft.DataCell(
            ft.Row(
                [
                    ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, size=18, color=TEXT_TERTIARY),
                    ft.Container(width=6),
                    ft.Text(name, size=13, color=TEXT_PRIMARY),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            on_tap=on_tap,
        )

    def build_submission_item(item):
        score_value = item.get("score", "—")
        classification = item.get("classification", ["Unclassified"])
        classification = classification[0] if isinstance(classification, list) else classification
        classification_colors = {
            "Fully Relevant": SUCCESS,
            "Partially Relevant": WARNING,
            "Irrelevant": ERROR,
        }
        score_color = classification_colors.get(classification, PRIMARY_BLUE)

        criterion_rows = []
        for name, value in (item.get("criterion_scores") or {}).items():
            try:
                score_pct = float(value) * 100 if float(value) <= 1 else float(value)
            except (TypeError, ValueError):
                continue
            criterion_color = SUCCESS if score_pct >= 75 else WARNING if score_pct >= 50 else ERROR
            criterion_rows.append(
                ft.Row(
                    [
                        ft.Text(name, size=12, color=TEXT_SECONDARY, width=160),
                        ft.ProgressBar(
                            value=max(0, min(100, score_pct)) / 100,
                            bgcolor=SECTION_BG_COLOR,
                            color=criterion_color,
                            height=7,
                            border_radius=4,
                            expand=True,
                        ),
                        ft.Text(f"{score_pct:.0f}%", size=12, color=TEXT_SECONDARY, width=42),
                    ],
                    spacing=10,
                )
            )

        rubric_details = item.get("rubric_details") or []
        if isinstance(rubric_details, dict):
            rubric_details = [
                {"name": name, "description": description}
                for name, description in rubric_details.items()
            ]
        rubric_rows = [
            ft.Row(
                [
                    ft.Text(entry.get("name", "Criterion"), size=12, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY, width=160),
                    ft.Text(entry.get("description", "No description"), size=12, color=TEXT_SECONDARY, expand=True),
                ],
                spacing=10,
            )
            for entry in rubric_details
            if isinstance(entry, dict)
        ]
        if not rubric_rows:
            rubric_rows = [ft.Text("Rubric details unavailable for this evaluation.", size=12, color=TEXT_TERTIARY)]

        expanded = {"value": False}
        arrow_icon = ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN, size=18, color=TEXT_SECONDARY)

        detail_panel = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(score_value, size=28, weight=ft.FontWeight.BOLD, color=score_color),
                            classification_badge(classification),
                            ft.Text(item.get("type", "—"), size=12, color=TEXT_TERTIARY),
                        ],
                        spacing=12,
                    ),
                    ft.Divider(height=1, color=BORDER_COLOR),
                    ft.Text("QUESTION", size=11, color=TEXT_TERTIARY, weight=ft.FontWeight.BOLD),
                    ft.Text(item.get("prompt") or "No question saved.", size=13, color=TEXT_PRIMARY),
                    ft.Text("CRITERION SCORES", size=11, color=TEXT_TERTIARY, weight=ft.FontWeight.BOLD),
                    ft.Column(criterion_rows or [ft.Text("No criterion scores saved.", size=12, color=TEXT_TERTIARY)], spacing=9),
                    ft.Text("RUBRIC", size=11, color=TEXT_TERTIARY, weight=ft.FontWeight.BOLD),
                    ft.Column(rubric_rows, spacing=7),
                ],
                spacing=10,
            ),
            bgcolor=SECTION_BG_COLOR,
            border_radius=10,
            padding=16,
            margin=ft.margin.only(top=4, bottom=8),
            visible=False,
        )

        def toggle_details(e):
            expanded["value"] = not expanded["value"]
            detail_panel.visible = expanded["value"]
            arrow_icon.name = (
                ft.Icons.KEYBOARD_ARROW_UP
                if expanded["value"]
                else ft.Icons.KEYBOARD_ARROW_DOWN
            )
            page.update()

        summary_row = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, size=18, color=TEXT_TERTIARY),
                    ft.Text(item["file"], size=13, color=TEXT_PRIMARY, expand=True),
                    ft.Text(item["score"], size=13, weight=ft.FontWeight.W_600, color=PRIMARY_BLUE, width=60),
                    classification_badge(classification),
                    ft.Text(item["type"], size=13, color=TEXT_SECONDARY, width=100),
                    ft.Text(item["evaluator"], size=13, color=TEXT_SECONDARY, width=120),
                    ft.Text(item["date"], size=13, color=TEXT_SECONDARY, width=120),
                    arrow_icon,
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=14),
            on_click=toggle_details,
            ink=True,
            tooltip="View submission details",
        )
        return ft.Column([summary_row, detail_panel], spacing=0)

    def empty_submission_state(msg="No submissions found"):
        return ft.Container(
            content=ft.Text(msg, color=TEXT_SECONDARY),
            padding=ft.padding.all(24),
            alignment=ft.alignment.center,
        )

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
        submissions_list.controls = [build_submission_item(item) for item in filtered] if filtered else [empty_submission_state()]
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

    # --- Expandable submissions list ---
    submissions_header = ft.Container(
        content=ft.Row(
            [
                ft.Text("STUDENT FILE", size=11, weight=ft.FontWeight.BOLD, color=TEXT_TERTIARY, expand=True),
                ft.Text("SCORE", size=11, weight=ft.FontWeight.BOLD, color=TEXT_TERTIARY, width=60),
                ft.Text("CLASSIFICATION", size=11, weight=ft.FontWeight.BOLD, color=TEXT_TERTIARY, width=125),
                ft.Text("TYPE", size=11, weight=ft.FontWeight.BOLD, color=TEXT_TERTIARY, width=100),
                ft.Text("EVALUATOR", size=11, weight=ft.FontWeight.BOLD, color=TEXT_TERTIARY, width=120),
                ft.Text("DATE", size=11, weight=ft.FontWeight.BOLD, color=TEXT_TERTIARY, width=120),
                ft.Container(width=18),
            ],
            spacing=12,
        ),
        bgcolor=SECTION_BG_COLOR,
        padding=ft.padding.symmetric(horizontal=16, vertical=14),
    )

    submissions_list = ft.ListView(
        controls=[build_submission_item(item) for item in SUBMISSIONS_DATA] if SUBMISSIONS_DATA else [empty_submission_state()],
        spacing=0,
        height=420,
        auto_scroll=False,
    )

    table_scroll_view = ft.ListView(
        controls=[submissions_header, submissions_list],
        spacing=0,
        height=480,
        auto_scroll=False,
    )

    # --- Submissions Card container ---
    submissions_section = ft.Container(
        content=ft.Column(
            [
                filter_section,
                ft.Container(
                    content=table_scroll_view,
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