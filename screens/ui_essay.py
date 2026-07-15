import flet as ft
from utils.utils import (
    BG_COLOR, CARD_BG_COLOR, SECTION_BG_COLOR,
    PRIMARY_BLUE, PRIMARY_BLUE_DARK, PRIMARY_BLUE_LIGHT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_TERTIARY, TEXT_WHITE,
    BORDER_COLOR, BORDER_COLOR_DARK,
    BUTTON_PRIMARY_BG, BUTTON_PRIMARY_TEXT, BUTTON_SECONDARY_BG, BUTTON_SECONDARY_TEXT, BUTTON_SECONDARY_BORDER,
    INPUT_BG, INPUT_BORDER, INPUT_TEXT, INPUT_HINT,
    UPLOAD_BG, UPLOAD_BORDER, UPLOAD_TEXT
)


def main(page: ft.Page, nav=None):
    page.title = "QualCheck Evaluation - Essay"
    page.scroll = ft.ScrollMode.AUTO

    # Only create app bar if not in evaluation mode (navigation handles it)
    if not nav or not nav.is_evaluation_mode:
        # --- App Bar ---
        logo = ft.Container(
            content=ft.Text("Q", size=20, weight=ft.FontWeight.BOLD, color=TEXT_WHITE),
            bgcolor=PRIMARY_BLUE,
            width=36,
            height=36,
            border_radius=8,
            alignment=ft.alignment.center,
        )

        brand = ft.Column(
            [
                ft.Text("QualCheck", size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Text("Rubric-Guided Semantic Evaluation System", size=10, color=TEXT_SECONDARY),
            ],
            spacing=2,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        app_bar = ft.AppBar(
            leading=ft.Row([ft.Container(width=12), logo, ft.Container(width=12), brand], alignment=ft.MainAxisAlignment.CENTER),
            leading_width=320,
            bgcolor=CARD_BG_COLOR,
            toolbar_height=70,
            center_title=False,
            title=ft.Row(
                [
                    ft.Container(width=20),
                    ft.ElevatedButton("New Evaluation", icon=ft.Icons.ADD, bgcolor=BUTTON_PRIMARY_BG, color=BUTTON_PRIMARY_TEXT),
                    ft.Container(width=10),
                    ft.ElevatedButton("Dashboard", icon=ft.Icons.DASHBOARD),
                ]
            ),
            actions=[
                ft.Row(
                    [
                        ft.IconButton(ft.Icons.LOGOUT, tooltip="Logout", icon_color=TEXT_PRIMARY, on_click=lambda e: nav.navigate_to_login() if nav else None),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(width=12),
            ],
        )

        page.appbar = app_bar

    # --- Output Type Section ---
    output_type_label = ft.Text("Output Type", size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)

    def on_short_answer(e):
        if nav:
            nav.navigate_to_short_answer()
    
    def on_essay(e):
        if nav:
            nav.navigate_to_essay()
    
    def on_code_report(e):
        if nav:
            nav.navigate_to_code_report()

    output_type_buttons = ft.Row(
        [
            ft.ElevatedButton(
                content=ft.Text("Short Answer", color=BUTTON_SECONDARY_TEXT),
                bgcolor=BUTTON_SECONDARY_BG,
                color=BUTTON_SECONDARY_TEXT,
                height=40,
                on_click=on_short_answer,
            ),
            ft.ElevatedButton(
                content=ft.Text("Essay", color=BUTTON_PRIMARY_TEXT),
                bgcolor=BUTTON_PRIMARY_BG,
                color=BUTTON_PRIMARY_TEXT,
                height=40,
                on_click=on_essay,
            ),
            ft.ElevatedButton(
                content=ft.Text("Code Report", color=BUTTON_SECONDARY_TEXT),
                bgcolor=BUTTON_SECONDARY_BG,
                color=BUTTON_SECONDARY_TEXT,
                height=40,
                on_click=on_code_report,
            ),
        ],
        spacing=10,
    )

    output_type_section = ft.Container(
        content=ft.Column(
            [output_type_label, ft.Container(height=10), output_type_buttons],
            spacing=0,
        ),
        padding=ft.padding.all(20),
        bgcolor=CARD_BG_COLOR,
        border_radius=12,
        border=ft.border.all(1, BORDER_COLOR),
    )

    # --- Academic Prompt Section ---
    prompt_label = ft.Text("Academic Prompt / Question", size=14, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY)
    prompt_field = ft.TextField(
        hint_text="Enter the academic prompt or question here...",
        multiline=True,
        min_lines=3,
        max_lines=6,
        bgcolor=INPUT_BG,
        border_color=INPUT_BORDER,
        text_size=13,
        color=INPUT_TEXT,
        hint_style=ft.TextStyle(color=INPUT_HINT),
        content_padding=ft.padding.all(12),
    )

    prompt_section = ft.Container(
        content=ft.Column([prompt_label, ft.Container(height=8), prompt_field], spacing=0),
        padding=ft.padding.all(20),
        bgcolor=CARD_BG_COLOR,
        border_radius=12,
        border=ft.border.all(1, BORDER_COLOR),
    )

    # --- Rubric Descriptor Section ---
    rubric_label = ft.Text("Rubric Descriptor", size=14, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY)
    rubric_subtitle = ft.Text(
        "Define expectations for each criterion — applied to every submitted response",
        size=12,
        color=TEXT_SECONDARY,
    )

    criterion1_label = ft.Text("1 Content", size=13, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY)
    criterion1_field = ft.TextField(
        hint_text="Define content expectations...",
        multiline=True,
        min_lines=2,
        max_lines=4,
        bgcolor=INPUT_BG,
        border_color=INPUT_BORDER,
        text_size=13,
        color=INPUT_TEXT,
        hint_style=ft.TextStyle(color=INPUT_HINT),
        content_padding=ft.padding.all(10),
    )

    criterion2_label = ft.Text("2 Organization", size=13, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY)
    criterion2_field = ft.TextField(
        hint_text="Define organization expectations...",
        multiline=True,
        min_lines=2,
        max_lines=4,
        bgcolor=INPUT_BG,
        border_color=INPUT_BORDER,
        text_size=13,
        color=INPUT_TEXT,
        hint_style=ft.TextStyle(color=INPUT_HINT),
        content_padding=ft.padding.all(10),
    )

    criterion3_label = ft.Text("3 Language", size=13, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY)
    criterion3_field = ft.TextField(
        hint_text="Define language expectations...",
        multiline=True,
        min_lines=2,
        max_lines=4,
        bgcolor=INPUT_BG,
        border_color=INPUT_BORDER,
        text_size=13,
        color=INPUT_TEXT,
        hint_style=ft.TextStyle(color=INPUT_HINT),
        content_padding=ft.padding.all(10),
    )

    rubric_section = ft.Container(
        content=ft.Column(
            [
                rubric_label,
                ft.Container(height=4),
                rubric_subtitle,
                ft.Container(height=12),
                criterion1_label,
                ft.Container(height=6),
                criterion1_field,
                ft.Container(height=12),
                criterion2_label,
                ft.Container(height=6),
                criterion2_field,
                ft.Container(height=12),
                criterion3_label,
                ft.Container(height=6),
                criterion3_field,
            ],
            spacing=0,
        ),
        padding=ft.padding.all(20),
        bgcolor=CARD_BG_COLOR,
        border_radius=12,
        border=ft.border.all(1, BORDER_COLOR),
    )

    # --- Student Responses Section ---
    responses_label = ft.Text("Student Responses", size=14, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY)
    responses_subtitle = ft.Text(
        "Upload one PDF per student — all will be evaluated against the same rubric",
        size=12,
        color=TEXT_SECONDARY,
    )

    upload_area = ft.Container(
        content=ft.Column(
            [
                ft.Icon(ft.Icons.CLOUD_UPLOAD, size=48, color=UPLOAD_TEXT),
                ft.Container(height=12),
                ft.Text("Drag & drop PDFs, or browse", size=14, color=UPLOAD_TEXT),
                ft.Container(height=4),
                ft.Text("Multiple files supported — one per student", size=12, color=UPLOAD_TEXT),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=UPLOAD_BG,
        border=ft.border.all(2, UPLOAD_BORDER),
        border_radius=12,
        padding=ft.padding.symmetric(vertical=40, horizontal=20),
        alignment=ft.alignment.center,
    )

    responses_section = ft.Container(
        content=ft.Column(
            [responses_label, ft.Container(height=4), responses_subtitle, ft.Container(height=12), upload_area],
            spacing=0,
        ),
        padding=ft.padding.all(20),
        bgcolor=CARD_BG_COLOR,
        border_radius=12,
        border=ft.border.all(1, BORDER_COLOR),
    )

    # --- Evaluate Button ---
    def on_evaluate(e):
        # TODO: Integrate with core evaluation module
        # For now, create mock results to demonstrate the studenta_result screen
        import random
        
        # Mock student results
        mock_results = [
            {
                "name": "Student 1",
                "file": "student_1.pdf",
                "score": random.uniform(60, 95),
                "criteria": [
                    ("Content", random.randint(50, 100)),
                    ("Organization", random.randint(50, 100)),
                    ("Language", random.randint(50, 100)),
                ],
            },
            {
                "name": "Student 2",
                "file": "student_2.pdf",
                "score": random.uniform(60, 95),
                "criteria": [
                    ("Content", random.randint(50, 100)),
                    ("Organization", random.randint(50, 100)),
                    ("Language", random.randint(50, 100)),
                ],
            },
            {
                "name": "Student 3",
                "file": "student_3.pdf",
                "score": random.uniform(60, 95),
                "criteria": [
                    ("Content", random.randint(50, 100)),
                    ("Organization", random.randint(50, 100)),
                    ("Language", random.randint(50, 100)),
                ],
            },
        ]
        
        # Build rubric from form fields
        rubric = [
            ("Content", criterion1_field.value),
            ("Organization", criterion2_field.value),
            ("Language", criterion3_field.value),
        ]
        
        # Navigate to results screen
        if nav and hasattr(nav, 'navigate_to_student_result'):
            nav.navigate_to_student_result(mock_results, prompt_field.value, rubric)

    evaluate_btn = ft.ElevatedButton(
        content=ft.Row(
            [ft.Text("> Evaluate Response", size=15, weight=ft.FontWeight.BOLD)],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        width=200,
        height=48,
        style=ft.ButtonStyle(
            bgcolor=BUTTON_PRIMARY_BG,
            color=BUTTON_PRIMARY_TEXT,
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
        on_click=on_evaluate,
    )

    evaluate_instruction = ft.Text(
        "Complete all rubric criteria, upload at least one PDF, and enter a prompt to continue.",
        size=12,
        color=TEXT_SECONDARY,
    )

    # --- How It Works Section ---
    how_it_works_label = ft.Text("How it works:", size=14, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)
    how_it_works_content = ft.Column(
        [
            ft.Text("• Each student PDF is extracted and encoded into BERT semantic vectors", size=12, color=TEXT_SECONDARY),
            ft.Text("• Cosine similarity is calculated per rubric criterion for every response", size=12, color=TEXT_SECONDARY),
            ft.Text("• Each student receives an indicator classification, results saved to dashboard", size=12, color=TEXT_SECONDARY),
        ],
        spacing=4,
    )

    how_it_works_section = ft.Container(
        content=ft.Column([how_it_works_label, ft.Container(height=8), how_it_works_content], spacing=0),
        padding=ft.padding.all(16),
        bgcolor=SECTION_BG_COLOR,
        border_radius=8,
        border=ft.border.all(1, BORDER_COLOR),
    )

    evaluate_section = ft.Column(
        [evaluate_btn, ft.Container(height=8), evaluate_instruction, ft.Container(height=16), how_it_works_section],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # --- Main Content ---
    main_title = ft.Text("Evaluate Academic Response", size=24, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)

    main_content = ft.Container(
        content=ft.Column(
            [
                main_title,
                ft.Container(height=24),
                output_type_section,
                ft.Container(height=20),
                prompt_section,
                ft.Container(height=20),
                rubric_section,
                ft.Container(height=20),
                responses_section,
                ft.Container(height=24),
                evaluate_section,
                ft.Container(height=40),
            ],
            spacing=0,
        ),
        padding=ft.padding.symmetric(horizontal=32, vertical=24),
    )

    # --- Page Layout ---
    page.add(main_content)
    if nav:
        nav.main_content = main_content


if __name__ == "__main__":
    ft.app(target=main)
