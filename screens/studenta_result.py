import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import flet as ft
from datetime import datetime
from utils.utils import (
    BG_COLOR, CARD_BG_COLOR, SECTION_BG_COLOR,
    PRIMARY_BLUE, PRIMARY_BLUE_DARK, PRIMARY_BLUE_LIGHT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_TERTIARY, TEXT_WHITE,
    BORDER_COLOR, BORDER_COLOR_DARK,
    BUTTON_PRIMARY_BG, BUTTON_PRIMARY_TEXT, BUTTON_SECONDARY_BG, BUTTON_SECONDARY_TEXT,
    BUTTON_SECONDARY_BORDER,
    SUCCESS, WARNING, ERROR, INFO,
)
from services.report_service import (
    export_evaluation_to_pdf,
    export_evaluations_to_pdf,
    export_evaluations_to_csv,
    safe_export_name,
)

# Extra accent used only on this screen (Top Score stat card)
PURPLE = "#8b5cf6"
PURPLE_BG = "#f5f3ff"

CLASSIFICATION_STYLES = {
    "Fully Relevant": (SUCCESS, "#dcfce7"),
    "Partially Relevant": (WARNING, "#fef3c7"),
    "Irrelevant": (ERROR, "#fee2e2"),
}


def classify(score: float):
    """Fallback only — used if a student dict somehow arrives without a
    precomputed classification. Real evaluation results carry their own
    `classification` (computed with the model's actual theta1/theta2),
    which resolve_label() prefers over this."""
    if score >= 75:
        return "Fully Relevant", SUCCESS, "#dcfce7"
    elif score >= 50:
        return "Partially Relevant", WARNING, "#fef3c7"
    else:
        return "Irrelevant", ERROR, "#fee2e2"


def resolve_label(student: dict):
    """Prefer the classification already computed by the evaluator (correct
    per-model theta1/theta2) over recomputing from a fixed 75/50 split."""
    label = student.get("classification")
    if label and label in CLASSIFICATION_STYLES:
        color, bg = CLASSIFICATION_STYLES[label]
        return label, color, bg
    return classify(student["score"])


def main(page: ft.Page, nav=None, results=None, academic_prompt=None, rubric=None,
         output_type_label="Short Answer", theta1=None, theta2=None):
    """
    results: list of student dicts, shape:
        {
            "name": str,                       # student / file display name
            "file": str,                       # original filename
            "score": float,                    # 0-100 overall similarity score
            "classification": str,             # "Fully Relevant" / "Partially Relevant" / "Irrelevant"
            "criteria": [(str, int), ...],     # (criterion_name, 0-100 score) pairs
        }
    academic_prompt: str, the prompt used for this evaluation.
    rubric: list of (name, description) tuples, the rubric used for this evaluation.
    output_type_label: display label for the header ("Short Answer" / "Essay" / "Code Report").
    """
    page.title = "QualCheck Evaluation - Results"
    page.scroll = ft.ScrollMode.AUTO
    page.bgcolor = BG_COLOR
    page.theme_mode = ft.ThemeMode.LIGHT

    if not results:
        # Nothing to show — bail back to the dashboard rather than rendering
        # against fake data.
        if nav and hasattr(nav, "navigate_to_dashboard"):
            nav.navigate_to_dashboard()
        return

    students = results
    prompt_text = academic_prompt or ""
    rubric_items_data = rubric or []
    sort_mode = {"value": "score"}  # "score" or "name"

    total_students = len(students)
    avg_score = sum(s["score"] for s in students) / total_students
    top_score = max(s["score"] for s in students)
    fully = sum(1 for s in students if resolve_label(s)[0] == "Fully Relevant")
    partial = sum(1 for s in students if resolve_label(s)[0] == "Partially Relevant")
    irrelevant = sum(1 for s in students if resolve_label(s)[0] == "Irrelevant")

    export_state = {"mode": None, "student": None, "sort": "score"}

    def report_record(student):
        return {
            "file_name": student.get("file") or student.get("name") or "Untitled",
            "output_type": output_type_label,
            "classification": resolve_label(student)[0],
            "similarity_score": float(student.get("score", 0.0)) / 100,
            "criterion_scores": {
                name: float(value) / 100
                for name, value in student.get("criteria", [])
            },
            "prompt": prompt_text,
            "rubric_details": [
                {"name": name, "description": description}
                for name, description in rubric_items_data
            ],
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }

    def on_export_result(e: ft.FilePickerResultEvent):
        if not e.path:
            return
        ordered_students = sorted(
            students,
            key=(
                (lambda student: student.get("name", "").lower())
                if export_state["sort"] == "name"
                else (lambda student: -float(student.get("score", 0.0)))
            ),
        )
        mode = export_state["mode"]
        if mode == "csv":
            output_path = e.path if e.path.lower().endswith(".csv") else f"{e.path}.csv"
            success = export_evaluations_to_csv(
                [report_record(student) for student in ordered_students],
                output_path,
            )
            message = "CSV exported successfully." if success else "CSV export failed."
        elif mode == "pdf_all":
            output_path = e.path if e.path.lower().endswith(".pdf") else f"{e.path}.pdf"
            success = export_evaluations_to_pdf(
                [report_record(student) for student in ordered_students],
                output_path,
            )
            message = "PDF exported successfully." if success else "PDF export failed."
        else:
            output_path = e.path if e.path.lower().endswith(".pdf") else f"{e.path}.pdf"
            success = export_evaluation_to_pdf(
                report_record(export_state["student"]),
                output_path,
            )
            message = "PDF exported successfully." if success else "PDF export failed."
        page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color=TEXT_WHITE),
            bgcolor=SUCCESS if success else ERROR,
        )
        page.snack_bar.open = True
        page.update()

    export_picker = ft.FilePicker(on_result=on_export_result)
    page.overlay.append(export_picker)

    def export_student_pdf(student):
        export_state["mode"] = "pdf"
        export_state["student"] = student
        export_picker.save_file(
            dialog_title="Download evaluation report",
            file_name=safe_export_name(student.get("name"), ".pdf"),
            allowed_extensions=["pdf"],
        )

    def export_results_csv(e):
        export_state["mode"] = "csv"
        export_state["student"] = None
        show_export_order_dialog()

    def export_results_pdf(e):
        export_state["mode"] = "pdf_all"
        export_state["student"] = None
        show_export_order_dialog()

    def show_export_order_dialog():
        export_format = "CSV" if export_state["mode"] == "csv" else "PDF"

        def choose_order(order):
            def handler(e):
                export_state["sort"] = order
                page.close(export_order_dialog)
                if export_state["mode"] == "csv":
                    export_picker.save_file(
                        dialog_title="Download evaluation results",
                        file_name="qualcheck_evaluation_results.csv",
                        allowed_extensions=["csv"],
                    )
                else:
                    export_picker.save_file(
                        dialog_title="Download all evaluation results",
                        file_name="qualcheck_evaluation_results.pdf",
                        allowed_extensions=["pdf"],
                    )
            return handler

        export_order_dialog = ft.AlertDialog(
            modal=True,
            shape=ft.RoundedRectangleBorder(radius=18),
            bgcolor=CARD_BG_COLOR,
            content_padding=ft.padding.all(20),
            content=ft.Container(
                width=320,
                height=112,
                content=ft.Column(
                    [
                        ft.Text(
                            f"Export {export_format}",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=TEXT_PRIMARY,
                        ),
                        ft.Text(
                            "Choose the result order.",
                            size=12,
                            color=TEXT_SECONDARY,
                        ),
                        ft.Container(height=14),
                        ft.Row(
                            [
                                ft.ElevatedButton(
                                    "Name",
                                    icon=ft.Icons.SORT_BY_ALPHA,
                                    on_click=choose_order("name"),
                                    style=ft.ButtonStyle(
                                        bgcolor=BUTTON_SECONDARY_BG,
                                        color=TEXT_PRIMARY,
                                        side=ft.BorderSide(1, BORDER_COLOR),
                                        shape=ft.RoundedRectangleBorder(radius=8),
                                    ),
                                    expand=True,
                                ),
                                ft.ElevatedButton(
                                    "Score",
                                    icon=ft.Icons.SORT,
                                    on_click=choose_order("score"),
                                    style=ft.ButtonStyle(
                                        bgcolor=PRIMARY_BLUE,
                                        color=TEXT_WHITE,
                                        shape=ft.RoundedRectangleBorder(radius=8),
                                    ),
                                    expand=True,
                                ),
                            ],
                            spacing=8,
                        ),
                        ft.Container(expand=True),
                        ft.Row(
                            [
                                ft.Container(expand=True),
                                ft.TextButton(
                                    "Cancel",
                                    on_click=lambda e: page.close(export_order_dialog),
                                ),
                            ],
                        ),
                    ],
                    spacing=0,
                ),
            ),
        )
        page.open(export_order_dialog)

    # -----------------------------------------------------------------
    # Header
    # -----------------------------------------------------------------
    def go_back(e):
        if nav:
            if getattr(nav, "evaluation_return_view", "new_evaluation") == "dashboard" and hasattr(nav, "navigate_to_dashboard"):
                nav.evaluation_return_view = "new_evaluation"
                nav.navigate_to_dashboard()
            elif hasattr(nav, "navigate_to_new_evaluation"):
                nav.navigate_to_new_evaluation()
            else:
                nav.navigate_to_short_answer()

    header_buttons = ft.Row(
        [
            ft.Container(
                content=                ft.Row(
                    [
                    ft.Icon(ft.Icons.DOWNLOAD, size=16, color=TEXT_WHITE),
                    ft.Text("Export CSV", size=13, weight=ft.FontWeight.W_600, color=TEXT_WHITE),
                ],
                spacing=8,
                ),
                bgcolor="#22c55e",
                border_radius=8,
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                on_click=export_results_csv,
                ink=True,
            ),
            ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.PICTURE_AS_PDF, size=16, color=TEXT_WHITE),
                        ft.Text("Export PDF", size=13, weight=ft.FontWeight.W_600, color=TEXT_WHITE),
                    ],
                    spacing=8,
                ),
                bgcolor=PRIMARY_BLUE,
                border_radius=8,
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                on_click=export_results_pdf,
                ink=True,
            ),
        ],
        spacing=12,
    )

    header = ft.Container(
        content=ft.Row(
            [
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.IconButton(
                                    icon=ft.Icons.ARROW_BACK,
                                    icon_color=TEXT_PRIMARY,
                                    on_click=go_back,
                                    tooltip="Back to Evaluation Selection",
                                ),
                                ft.Text("Evaluation Results", size=24, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                            ],
                            spacing=4,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Container(height=2),
                        ft.Text(
                            f"{output_type_label} · {total_students} students · {datetime.now().strftime('%#m/%#d/%Y')}",
                            size=13,
                            color=TEXT_SECONDARY,
                        ),
                    ],
                    spacing=0,
                ),
                header_buttons,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.START,
        ),
        padding=ft.padding.only(left=24, right=24, top=24, bottom=16),
    )

    # -----------------------------------------------------------------
    # Stat cards
    # -----------------------------------------------------------------
    def stat_card(label, value, icon, icon_color, value_color=TEXT_PRIMARY):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(label, size=12, color=TEXT_SECONDARY),
                            ft.Icon(icon, size=16, color=icon_color),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(height=6),
                    ft.Text(value, size=22, weight=ft.FontWeight.BOLD, color=value_color),
                ],
                spacing=0,
            ),
            bgcolor=CARD_BG_COLOR,
            border=ft.border.all(1, BORDER_COLOR),
            border_radius=10,
            padding=16,
            expand=True,
        )

    stat_cards_row = ft.Row(
        [
            stat_card("Total Students", str(total_students), ft.Icons.GROUP_OUTLINED, PRIMARY_BLUE),
            stat_card("Avg. Similarity", f"{avg_score:.1f}%", ft.Icons.WORKSPACE_PREMIUM_OUTLINED, SUCCESS, SUCCESS),
            stat_card("Top Score", f"{top_score:.1f}%", ft.Icons.TRENDING_UP, PURPLE, PURPLE),
            stat_card("Needs Attention", str(irrelevant), ft.Icons.WARNING_AMBER_ROUNDED, ERROR,
                      ERROR if irrelevant else TEXT_PRIMARY),
        ],
        spacing=16,
    )

    # -----------------------------------------------------------------
    # Classification breakdown (segmented bar + legend)
    # -----------------------------------------------------------------
    def legend_row(color, label, count):
        pct = round((count / total_students) * 100) if total_students else 0
        return ft.Row(
            [
                ft.Row(
                    [
                        ft.Container(width=8, height=8, border_radius=4, bgcolor=color),
                        ft.Text(label, size=13, color=TEXT_PRIMARY),
                    ],
                    spacing=8,
                ),
                ft.Text(f"{count}  ({pct}%)", size=13, color=TEXT_SECONDARY),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

    segments = []
    for count, color in [(fully, SUCCESS), (partial, WARNING), (irrelevant, ERROR)]:
        if count > 0:
            segments.append(
                ft.Container(
                    bgcolor=color,
                    expand=count,
                    height=10,
                )
            )
    if not segments:
        segments = [ft.Container(bgcolor=BORDER_COLOR, expand=1, height=10)]

    classification_card = ft.Container(
        content=ft.Column(
            [
                ft.Text("Classification Breakdown", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(height=14),
                ft.Container(
                    content=ft.Row(segments, spacing=0),
                    border_radius=6,
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                ),
                ft.Container(height=16),
                legend_row(SUCCESS, "Fully Relevant", fully),
                ft.Container(height=8),
                legend_row(WARNING, "Partially Relevant", partial),
                ft.Container(height=8),
                legend_row(ERROR, "Irrelevant", irrelevant),
            ],
            spacing=0,
        ),
        bgcolor=CARD_BG_COLOR,
        border=ft.border.all(1, BORDER_COLOR),
        border_radius=10,
        padding=20,
        expand=1,
    )

    # -----------------------------------------------------------------
    # Distribution chart (simple bar chart, no external chart lib needed)
    # -----------------------------------------------------------------
    def chart_bar(label, count, color):
        max_count = max(fully, partial, irrelevant, 1)
        bar_height = 90 * (count / max_count) if max_count else 0
        return ft.Column(
            [
                ft.Container(height=90 - bar_height),
                ft.Container(
                    width=48,
                    height=max(bar_height, 4) if count > 0 else 4,
                    bgcolor=color if count > 0 else BORDER_COLOR,
                    border_radius=ft.border_radius.only(top_left=4, top_right=4),
                ),
                ft.Container(height=8),
                ft.Text(label, size=11, color=TEXT_SECONDARY, text_align=ft.TextAlign.CENTER),
            ],
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    distribution_card = ft.Container(
        content=ft.Column(
            [
                ft.Text("Distribution Chart", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(height=14),
                ft.Row(
                    [
                        chart_bar("Fully Relevant", fully, SUCCESS),
                        chart_bar("Partially Relevant", partial, WARNING),
                        chart_bar("Irrelevant", irrelevant, ERROR),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                    vertical_alignment=ft.CrossAxisAlignment.END,
                ),
            ],
            spacing=0,
        ),
        bgcolor=CARD_BG_COLOR,
        border=ft.border.all(1, BORDER_COLOR),
        border_radius=10,
        padding=20,
        expand=1,
    )

    breakdown_row = ft.Row([classification_card, distribution_card], spacing=16)

    # -----------------------------------------------------------------
    # Academic prompt + rubric context panel
    # -----------------------------------------------------------------
    rubric_items = [
        ft.Row(
            [
                ft.Container(
                    content=ft.Text(str(i + 1), size=11, color=TEXT_WHITE, weight=ft.FontWeight.BOLD),
                    width=18, height=18, border_radius=9, bgcolor=PRIMARY_BLUE,
                    alignment=ft.alignment.center,
                ),
                ft.Text(f"{name}: {desc}", size=13, color=TEXT_PRIMARY),
            ],
            spacing=8,
        )
        for i, (name, desc) in enumerate(rubric_items_data)
    ]

    context_panel = ft.Container(
        content=ft.Row(
            [
                ft.Column(
                    [
                        ft.Text("ACADEMIC PROMPT", size=11, color=TEXT_TERTIARY, weight=ft.FontWeight.BOLD),
                        ft.Container(height=8),
                        ft.Text(prompt_text, size=13, color=TEXT_PRIMARY),
                    ],
                    spacing=0,
                    expand=1,
                ),
                ft.Column(
                    [
                        ft.Text("RUBRIC APPLIED", size=11, color=TEXT_TERTIARY, weight=ft.FontWeight.BOLD),
                        ft.Container(height=8),
                        ft.Column(rubric_items, spacing=8),
                    ],
                    spacing=0,
                    expand=1,
                ),
            ],
            spacing=32,
            vertical_alignment=ft.CrossAxisAlignment.START,
        ),
        bgcolor=CARD_BG_COLOR,
        border=ft.border.all(1, BORDER_COLOR),
        border_radius=10,
        padding=20,
    )

    # -----------------------------------------------------------------
    # Student results list (sortable, expandable rows)
    # -----------------------------------------------------------------
    student_list_column = ft.Column(spacing=0)

    def criterion_row(label, pct):
        # Use the model's REAL calibrated theta1/theta2 (per-criterion similarity
        # is a raw 0-1 cosine score, same scale the classifier itself uses) instead
        # of a hardcoded 75/50 split. Falls back to 75/50 only if theta1/theta2
        # weren't passed in (e.g. an older caller), so this never hard-crashes.
        t1 = theta1 * 100 if theta1 is not None else 75
        t2 = theta2 * 100 if theta2 is not None else 50
        color = SUCCESS if pct >= t1 else (WARNING if pct >= t2 else ERROR)
        return ft.Row(
            [
                ft.Text(label, size=13, color=TEXT_SECONDARY, width=150),
                ft.Container(
                    content=ft.ProgressBar(
                        value=pct / 100,
                        bgcolor=SECTION_BG_COLOR,
                        color=color,
                        bar_height=8,
                        border_radius=4,
                    ),
                    expand=True,
                ),
                ft.Text(f"{pct}%", size=13, color=TEXT_SECONDARY, width=40, text_align=ft.TextAlign.RIGHT),
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def build_row(student, rank):
        label, color, bg = resolve_label(student)
        expanded = {"value": rank == 1}  # first row expanded to match reference design

        detail_panel = ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(f"{student['score']:.1f}%", size=32, weight=ft.FontWeight.BOLD, color=color),
                                ft.Text(label, size=13, color=color, weight=ft.FontWeight.W_600),
                                ft.Text("Similarity Score", size=11, color=TEXT_SECONDARY),
                            ],
                            spacing=2,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        bgcolor=bg,
                        border_radius=10,
                        padding=20,
                        width=180,
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(width=24),
                    ft.Column(
                        [
                            ft.Text("CRITERION SCORES", size=11, color=TEXT_TERTIARY, weight=ft.FontWeight.BOLD),
                            ft.Container(height=10),
                            ft.Column(
                                [criterion_row(name, pct) for name, pct in student["criteria"]],
                                spacing=10,
                            ),
                        ],
                        spacing=0,
                        expand=True,
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            bgcolor=SECTION_BG_COLOR,
            border_radius=10,
            padding=20,
            margin=ft.margin.only(left=24, right=24, bottom=8),
            visible=expanded["value"],
        )

        arrow_icon = ft.Icon(
            ft.Icons.KEYBOARD_ARROW_UP if expanded["value"] else ft.Icons.KEYBOARD_ARROW_DOWN,
            size=18,
            color=TEXT_SECONDARY,
        )

        def toggle(e):
            expanded["value"] = not expanded["value"]
            detail_panel.visible = expanded["value"]
            arrow_icon.name = ft.Icons.KEYBOARD_ARROW_UP if expanded["value"] else ft.Icons.KEYBOARD_ARROW_DOWN
            page.update()

        summary_row = ft.Container(
            content=ft.Row(
                [
                    ft.Text(str(rank), size=13, color=TEXT_TERTIARY, width=20),
                    ft.Container(
                        content=ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, size=18, color=TEXT_SECONDARY),
                        width=36, height=36, border_radius=18, bgcolor=SECTION_BG_COLOR,
                        alignment=ft.alignment.center,
                    ),
                    ft.Column(
                        [
                            ft.Text(student["name"], size=14, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                            ft.Text(student["file"], size=12, color=TEXT_TERTIARY),
                        ],
                        spacing=0,
                        expand=True,
                    ),
                    ft.Column(
                        [
                            ft.Text(f"{student['score']:.1f}%", size=13, weight=ft.FontWeight.BOLD, color=color),
                            ft.Container(
                                content=ft.Container(
                                    bgcolor=color,
                                    border_radius=3,
                                    height=6,
                                    width=100 * (student["score"] / 100),
                                ),
                                bgcolor=SECTION_BG_COLOR,
                                border_radius=3,
                                height=6,
                                width=100,
                            ),
                        ],
                        spacing=4,
                        horizontal_alignment=ft.CrossAxisAlignment.END,
                    ),
                    ft.Container(
                        content=ft.Text(label, size=12, color=color, weight=ft.FontWeight.W_600),
                        bgcolor=bg,
                        border_radius=20,
                        padding=ft.padding.symmetric(horizontal=12, vertical=6),
                    ),
                    arrow_icon,
                ],
                spacing=16,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=24, vertical=14),
            on_click=toggle,
            ink=True,
        )

        return ft.Column([summary_row, detail_panel], spacing=0)

    def render_students():
        student_list_column.controls.clear()
        ordered = sorted(
            students,
            key=lambda s: (-s["score"]) if sort_mode["value"] == "score" else s["name"].lower(),
        )
        for i, s in enumerate(ordered):
            student_list_column.controls.append(build_row(s, i + 1))
            if i < len(ordered) - 1:
                student_list_column.controls.append(ft.Divider(height=1, color=BORDER_COLOR))

    render_students()

    def set_sort(mode):
        def handler(e):
            sort_mode["value"] = mode
            score_btn.bgcolor = PRIMARY_BLUE if mode == "score" else BUTTON_SECONDARY_BG
            score_btn.content.color = TEXT_WHITE if mode == "score" else BUTTON_SECONDARY_TEXT
            name_btn.bgcolor = PRIMARY_BLUE if mode == "name" else BUTTON_SECONDARY_BG
            name_btn.content.color = TEXT_WHITE if mode == "name" else BUTTON_SECONDARY_TEXT
            render_students()
            page.update()
        return handler

    score_btn = ft.Container(
        content=ft.Text("Score", size=12, color=TEXT_WHITE, weight=ft.FontWeight.W_600),
        bgcolor=PRIMARY_BLUE,
        border_radius=6,
        padding=ft.padding.symmetric(horizontal=14, vertical=6),
        on_click=set_sort("score"),
        ink=True,
    )
    name_btn = ft.Container(
        content=ft.Text("Name", size=12, color=BUTTON_SECONDARY_TEXT, weight=ft.FontWeight.W_600),
        bgcolor=BUTTON_SECONDARY_BG,
        border=ft.border.all(1, BORDER_COLOR),
        border_radius=6,
        padding=ft.padding.symmetric(horizontal=14, vertical=6),
        on_click=set_sort("name"),
        ink=True,
    )

    student_list_header = ft.Container(
        content=ft.Row(
            [
                ft.Text("Student Results", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Row(
                    [
                        ft.Text("Sort by:", size=12, color=TEXT_SECONDARY),
                        score_btn,
                        name_btn,
                    ],
                    spacing=8,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.padding.only(left=24, right=24, top=20, bottom=16),
    )

    student_list_card = ft.Container(
        content=ft.Column(
            [student_list_header, ft.Divider(height=1, color=BORDER_COLOR), student_list_column],
            spacing=0,
        ),
        bgcolor=CARD_BG_COLOR,
        border=ft.border.all(1, BORDER_COLOR),
        border_radius=10,
    )

    # -----------------------------------------------------------------
    # Methodology footer
    # -----------------------------------------------------------------
    def method_step(number, title, subtitle):
        return ft.Row(
            [
                ft.Container(
                    content=ft.Text(str(number), size=13, color=TEXT_WHITE, weight=ft.FontWeight.BOLD),
                    width=28, height=28, border_radius=14, bgcolor=PRIMARY_BLUE,
                    alignment=ft.alignment.center,
                ),
                ft.Column(
                    [
                        ft.Text(title, size=13, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                        ft.Text(subtitle, size=11, color=TEXT_SECONDARY),
                    ],
                    spacing=0,
                ),
            ],
            spacing=10,
        )

    methodology_footer = ft.Container(
        content=ft.Row(
            [
                method_step(1, "BERT Encoding", "Text converted to embeddings"),
                ft.Icon(ft.Icons.ARROW_FORWARD, size=16, color=TEXT_TERTIARY),
                method_step(2, "Cosine Similarity", "Compared against rubric"),
                ft.Icon(ft.Icons.ARROW_FORWARD, size=16, color=TEXT_TERTIARY),
                method_step(3, "Rubric Classification", "Scored against thresholds"),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20,
        ),
        padding=20,
    )

    # -----------------------------------------------------------------
    # Assemble page
    # -----------------------------------------------------------------
    layout = ft.Container(
        content=ft.Column(
            [
                header,
                ft.Container(
                    content=ft.Column(
                        [
                            stat_cards_row,
                            ft.Container(height=16),
                            breakdown_row,
                            ft.Container(height=16),
                            context_panel,
                            ft.Container(height=16),
                            student_list_card,
                            methodology_footer,
                        ],
                        spacing=0,
                    ),
                    padding=ft.padding.symmetric(horizontal=24),
                ),
                ft.Container(height=24),
            ],
            spacing=0,
        ),
        bgcolor=BG_COLOR,
        expand=True,
    )

    if nav and getattr(nav, "is_evaluation_mode", False):
        nav.main_content = layout
    else:
        page.add(layout)

    page.update()


if __name__ == "__main__":
    ft.app(target=main)