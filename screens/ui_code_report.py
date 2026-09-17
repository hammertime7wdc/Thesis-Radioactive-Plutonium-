import os
import time
import threading
import flet as ft
from utils.utils import (
    BG_COLOR, CARD_BG_COLOR, SECTION_BG_COLOR,
    PRIMARY_BLUE, PRIMARY_BLUE_DARK, PRIMARY_BLUE_LIGHT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_TERTIARY, TEXT_WHITE,
    BORDER_COLOR, BORDER_COLOR_DARK,
    BUTTON_PRIMARY_BG, BUTTON_PRIMARY_TEXT, BUTTON_SECONDARY_BG, BUTTON_SECONDARY_TEXT, BUTTON_SECONDARY_BORDER,
    INPUT_BG, INPUT_BORDER, INPUT_TEXT, INPUT_HINT,
    UPLOAD_BG, UPLOAD_BORDER, UPLOAD_TEXT,
    ERROR,
)
from widgets.loading_components import EvaluationProgressDialog
from core.pdf_processor import PDFProcessor
from core.embeddings import EmbeddingGenerator
from core.evaluation import Evaluator
from services.supabase_client import get_supabase_client
from services.session_manager import get_current_user

# ── Model paths — CODE REPORT track specifically ───────────────────────────
# theta1/theta2 in qualcheck_final_meta.json were calibrated (Eq. 3.3 grid
# search) against the SIAMESE model's own cosine-similarity output
# (model.similarity(), notebook cell 26) — NOT the cross-encoder. The
# cross-encoder scored higher (WF1 0.898 vs 0.836) and is recorded as
# "primary_eval" in that same JSON, but it classifies via argmax on its own
# softmax head and has no cosine-similarity output these thresholds mean
# anything against. Evaluator only implements the theta-threshold path, so
# the checkpoint loaded here MUST be the Siamese one (best_model.safetensors),
# never best_model_crossencoder.safetensors — loading the cross-encoder's
# weights into EmbeddingGenerator would run without error but produce a
# meaningless similarity score, since that checkpoint was never trained to
# make its CLS embedding meaningful for cosine comparison on its own.
# ── Adjust these two paths to wherever your code-report artifacts actually
#    live before shipping — placeholders below follow the same layout pattern
#    as the short-answer checkpoint referenced in EmbeddingGenerator's docstring.
# codereport_bert/ sits at project root, same level as essay_qualcheck/ and qualcheck_short_answers/
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.abspath(os.path.join(_THIS_DIR, ".."))
CODE_REPORT_MODEL_DIR = os.path.join(_ROOT_DIR, "codereport_bert", "best_model.safetensors")
CODE_REPORT_META_PATH = os.path.join(_ROOT_DIR, "codereport_bert", "qualcheck_final_meta.json")

# Lazy singletons — BERT + tokenizer load is expensive, load once per process
# and reuse across evaluations rather than reconstructing per click.
_embedding_generator = None
_evaluator = None
_pdf_processor = PDFProcessor()


def _get_evaluator():
    global _embedding_generator, _evaluator
    if _evaluator is None:
        _embedding_generator = EmbeddingGenerator(
            model_dir=CODE_REPORT_MODEL_DIR,
            bert_model="bert-base-uncased",
            max_len_pr=256,  # matches max_len_pr in qualcheck_final_meta.json
            max_len_r=512,   # matches max_len_r  in qualcheck_final_meta.json —
                              # code report responses are long, must NOT share
                              # the P-side's shorter 256-token budget.
        )
        _evaluator = Evaluator(_embedding_generator, meta_path=CODE_REPORT_META_PATH)
    return _evaluator


def main(page: ft.Page, nav=None):
    page.title = "QualCheck Evaluation - Code Report"
    page.scroll = ft.ScrollMode.AUTO

    current_user = get_current_user()
    if not current_user:
        if nav and hasattr(nav, "navigate_to_login"):
            nav.navigate_to_login()
        return

    user_identity = getattr(current_user, "user", current_user)
    user_id = getattr(user_identity, "id", None)

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
                        ft.IconButton(ft.Icons.LOGOUT, tooltip="Logout", icon_color=TEXT_PRIMARY, on_click=lambda e: nav.logout() if nav and hasattr(nav, "logout") else (nav.navigate_to_login() if nav else None)),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(width=12),
            ],
        )

        page.appbar = app_bar

    # --- Placeholder Content ---
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

    def output_type_button(label: str, selected: bool, on_click):
        return ft.ElevatedButton(
            content=ft.Text(
                label,
                color=PRIMARY_BLUE if selected else TEXT_PRIMARY,
                weight=ft.FontWeight.BOLD if selected else ft.FontWeight.W_500,
            ),
            height=40,
            style=ft.ButtonStyle(
                bgcolor="#eff6ff" if selected else "#ffffff",
                shape=ft.RoundedRectangleBorder(radius=8),
                side=ft.BorderSide(1, PRIMARY_BLUE if selected else BORDER_COLOR),
                elevation=0,
            ),
            on_click=on_click,
        )

    output_type_buttons = ft.Row(
        [
            output_type_button("Short Answer", False, on_short_answer),
            output_type_button("Essay", False, on_essay),
            output_type_button("Code Report", True, on_code_report),
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

    def criterion_badge(number: str, text: str):
        return ft.Row(
            [
                ft.Container(
                    content=ft.Text(number, size=11, weight=ft.FontWeight.BOLD, color=TEXT_WHITE),
                    width=20,
                    height=20,
                    border_radius=10,
                    bgcolor=PRIMARY_BLUE,
                    alignment=ft.alignment.center,
                ),
                ft.Container(width=8),
                ft.Text(text, size=13, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY),
            ],
            spacing=0,
        )

    criterion1_label = criterion_badge("1", "Technical Terminology")
    criterion1_field = ft.TextField(
        hint_text="Define technical terminology expectations...",
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

    criterion2_label = criterion_badge("2", "Clarity and Cohesion")
    criterion2_field = ft.TextField(
        hint_text="Define clarity and cohesion expectations...",
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

    criterion3_label = criterion_badge("3", "Constraint Adherence")
    criterion3_field = ft.TextField(
        hint_text="Define constraint adherence expectations...",
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

    criterion4_label = criterion_badge("4", "Algorithmic Logic")
    criterion4_field = ft.TextField(
        hint_text="Define algorithmic logic expectations...",
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
                ft.Container(height=12),
                criterion4_label,
                ft.Container(height=6),
                criterion4_field,
            ],
            spacing=0,
        ),
        padding=ft.padding.all(20),
        bgcolor=CARD_BG_COLOR,
        border_radius=12,
        border=ft.border.all(1, BORDER_COLOR),
    )

    # --- Student Responses Section ---
    responses_label = ft.Row(
        [
            ft.Text("Student Responses", size=14, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
            ft.Container(width=8),
            ft.Icon(ft.Icons.GROUP_OUTLINED, size=14, color=TEXT_TERTIARY),
            ft.Container(width=4),
            ft.Text("PDF per student", size=12, color=TEXT_TERTIARY),
        ],
        spacing=0,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )
    responses_subtitle = ft.Text(
        "Upload one PDF per student — all will be evaluated against the same rubric",
        size=12,
        color=TEXT_SECONDARY,
    )

    # --- File picker state -------------------------------------------------
    # selected_files: list of dicts {"name": display_name, "path": local_path}
    selected_files: list = []

    selected_files_list = ft.Column(spacing=4)

    def render_selected_files():
        selected_files_list.controls.clear()
        for f in selected_files:
            def make_remove_handler(target=f):
                def remove_file(e):
                    if target in selected_files:
                        selected_files.remove(target)
                    render_selected_files()
                    update_evaluate_button_state()
                    selected_files_list.update()
                    page.update()
                return remove_file

            selected_files_list.controls.append(
                ft.Row(
                    [
                        ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, size=14, color=TEXT_SECONDARY),
                        ft.Text(f["name"], size=12, color=TEXT_PRIMARY, expand=True),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            icon_size=14,
                            icon_color=TEXT_SECONDARY,
                            tooltip="Remove file",
                            on_click=make_remove_handler(),
                        ),
                    ],
                    spacing=6,
                )
            )

    def on_files_picked(e: ft.FilePickerResultEvent):
        if e.files:
            for f in e.files:
                if f.path and not any(sf["path"] == f.path for sf in selected_files):
                    selected_files.append({"name": f.name, "path": f.path})
            render_selected_files()
            update_evaluate_button_state()
            selected_files_list.update()
            page.update()

    file_picker = ft.FilePicker(on_result=on_files_picked)
    page.overlay.append(file_picker)

    def open_file_picker(e):
        file_picker.pick_files(
            dialog_title="Select student PDF submissions",
            allow_multiple=True,
            allowed_extensions=["pdf"],
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
        on_click=open_file_picker,
        ink=True,
    )

    responses_section = ft.Container(
        content=ft.Column(
            [
                responses_label,
                ft.Container(height=4),
                responses_subtitle,
                ft.Container(height=12),
                upload_area,
                ft.Container(height=10),
                selected_files_list,
            ],
            spacing=0,
        ),
        padding=ft.padding.all(20),
        bgcolor=CARD_BG_COLOR,
        border_radius=12,
        border=ft.border.all(1, BORDER_COLOR),
    )

    # --- Evaluate Button ---
    def on_evaluate(e):
        if not selected_files:
            return

        # Build rubric from form fields — order matters, this is the exact
        # order Evaluator.evaluate_response() will label each criterion with,
        # and the order studenta_result.py renders criterion_row()s in.
        rubric_pairs = [
            ("Technical Terminology", criterion1_field.value),
            ("Clarity and Cohesion", criterion2_field.value),
            ("Constraint Adherence", criterion3_field.value),
            ("Algorithmic Logic", criterion4_field.value),
        ]
        rubric_dict = {name: desc for name, desc in rubric_pairs}
        question = prompt_field.value or ""

        evaluate_btn.disabled = True
        evaluate_btn.content = ft.Row(
            [ft.ProgressRing(width=16, height=16, stroke_width=2, color=BUTTON_PRIMARY_TEXT),
             ft.Text("Evaluating...", size=15, weight=ft.FontWeight.BOLD)],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
        )
        evaluate_btn.update()

        progress_dialog = EvaluationProgressDialog(
            title="Evaluating Code Reports",
            subtitle="BERT Semantic Evaluation in progress...",
        )
        progress_dialog.open(page)

        def refresh_evaluate_button():
            evaluate_btn.disabled = False
            evaluate_btn.content = ft.Row(
                [ft.Text("> Evaluate Response", size=15, weight=ft.FontWeight.BOLD)],
                alignment=ft.MainAxisAlignment.CENTER,
            )
            try:
                evaluate_btn.update()
            except Exception:
                pass

        def run_evaluation_task():
            try:
                progress_dialog.update_progress(
                    status="Initializing evaluation model...",
                    detail="Loading neural network weights...",
                    progress_pct=None,
                )
                evaluator = _get_evaluator()  # loads BERT + weights on first call only
                supabase = get_supabase_client()

                results = []
                failed_files = []
                total_files = len(selected_files)

                for idx, f in enumerate(selected_files):
                    file_name = f.get("name", "Document")
                    pct = idx / total_files
                    progress_dialog.update_progress(
                        status=f"Evaluating report {idx + 1} of {total_files}",
                        detail=file_name,
                        progress_pct=pct,
                    )

                    if not f["path"]:
                        # Web build with no local path — desktop-only for now.
                        failed_files.append(f["name"])
                        continue
                    try:
                        response_text = _pdf_processor.extract_text(f["path"])
                    except Exception:
                        failed_files.append(f["name"])
                        continue

                    if not response_text.strip():
                        failed_files.append(f["name"])
                        continue

                    criterion_scores = evaluator.evaluate_response(question, response_text, rubric_dict)
                    overall_similarity = evaluator.calculate_overall_score(criterion_scores, method="min")
                    overall_pct = max(0.0, min(100.0, overall_similarity * 100))
                    overall_label = evaluator.classify(overall_similarity)

                    result_record = {
                        "name": os.path.splitext(f["name"])[0],
                        "file": f["name"],
                        "file_path": f["path"],
                        "score": overall_pct,
                        "similarity_score": overall_similarity,
                        "classification": overall_label,
                        "criteria": [
                            (name, round(max(0.0, min(100.0, criterion_scores[name]["similarity"] * 100))))
                            for name, _ in rubric_pairs
                        ],
                    }
                    results.append(result_record)

                    if user_id:
                        try:
                            supabase.table("evaluations").insert(
                                {
                                    "user_id": user_id,
                                    "prompt": question,
                                    "rubric_id": None,
                                    "output_type": "code_report",
                                    "similarity_score": overall_similarity,
                                    "classification": overall_label,
                                    "file_name": f["name"],
                                    "file_path": f["path"],
                                    "criterion_scores": {
                                        name: round(v["similarity"], 4)
                                        for name, v in criterion_scores.items()
                                    },
                                    "rubric_details": [
                                        {"name": name, "description": description}
                                        for name, description in rubric_pairs
                                    ],
                                }
                            ).execute()
                        except Exception as db_error:
                            print(f"Failed to save code report evaluation for {f['name']}: {db_error}")

                progress_dialog.update_progress(
                    status="Finalizing results...",
                    detail="Preparing evaluation summary...",
                    progress_pct=1.0,
                )
                time.sleep(0.3)
                progress_dialog.close()

                if failed_files:
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text(
                            f"Could not read {len(failed_files)} file(s): "
                            f"{', '.join(failed_files)}. They were skipped."
                        ),
                        bgcolor=ERROR,
                    )
                    page.snack_bar.open = True
                    page.update()

                if results and nav and hasattr(nav, 'navigate_to_student_result'):
                    nav.navigate_to_student_result(
                        results,
                        question,
                        rubric_pairs,
                        output_type_label="Code Report",
                        theta1=evaluator.theta1,
                        theta2=evaluator.theta2,
                    )

            except Exception as ex:
                print(f"Evaluation error: {ex}")
                progress_dialog.close()
                refresh_evaluate_button()
                page.snack_bar = ft.SnackBar(content=ft.Text(f"Evaluation failed: {ex}"), bgcolor=ERROR)
                page.snack_bar.open = True
                page.update()
            finally:
                refresh_evaluate_button()

        threading.Thread(target=run_evaluation_task, daemon=True).start()

    DISABLED_BG = "#cbd5e1"
    DISABLED_TEXT = "#f8fafc"

    evaluate_btn = ft.ElevatedButton(
        content=ft.Row(
            [ft.Text("> Evaluate Response", size=15, weight=ft.FontWeight.BOLD)],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        width=200,
        height=48,
        disabled=True,
        style=ft.ButtonStyle(
            bgcolor=DISABLED_BG,
            color=DISABLED_TEXT,
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
        on_click=on_evaluate,
    )

    def update_evaluate_button_state(e=None):
        is_valid = bool(
            (prompt_field.value or "").strip()
            and (criterion1_field.value or "").strip()
            and (criterion2_field.value or "").strip()
            and (criterion3_field.value or "").strip()
            and (criterion4_field.value or "").strip()
            and selected_files
        )
        evaluate_btn.disabled = not is_valid
        evaluate_btn.style = ft.ButtonStyle(
            bgcolor=BUTTON_PRIMARY_BG if is_valid else DISABLED_BG,
            color=BUTTON_PRIMARY_TEXT if is_valid else DISABLED_TEXT,
            shape=ft.RoundedRectangleBorder(radius=8),
        )
        if getattr(evaluate_btn, "page", None) is not None:
            evaluate_btn.update()

    prompt_field.on_change = update_evaluate_button_state
    criterion1_field.on_change = update_evaluate_button_state
    criterion2_field.on_change = update_evaluate_button_state
    criterion3_field.on_change = update_evaluate_button_state
    criterion4_field.on_change = update_evaluate_button_state

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
            ft.Text("• Each student receives an independent classification — results are saved to your dashboard", size=12, color=TEXT_SECONDARY),
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
    if nav:
        nav.main_content = main_content
    else:
        page.add(main_content)


if __name__ == "__main__":
    ft.app(target=main)