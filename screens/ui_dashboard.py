import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, timezone

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
from services.supabase_client import get_supabase_client
from services.session_manager import get_current_user

OUTPUT_TYPE_LABELS = {
    "short_answer": "Short Answer",
    "essay": "Essay",
    "code_report": "Code Report",
}
OUTPUT_TYPE_KEYS = {label: key for key, label in OUTPUT_TYPE_LABELS.items()}


def _fetch_user_evaluations(user_id: str) -> list:
    """Pull this user's own evaluation rows, most recent first."""
    if not user_id:
        return []
    supabase = get_supabase_client()
    try:
        resp = (
            supabase.table("evaluations")
            .select(
                "id, prompt, rubric_details, criterion_scores, "
                "file_name, file_path, similarity_score, classification, "
                "output_type, created_at"
            )
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return resp.data or []
    except Exception as fetch_error:
        print(f"Failed to fetch evaluations for dashboard: {fetch_error}")
        return []


def _compute_stats(evaluations: list) -> dict:
    total = len(evaluations)
    fully = sum(1 for e in evaluations if e.get("classification") == "Fully Relevant")
    partial = sum(1 for e in evaluations if e.get("classification") == "Partially Relevant")
    irrelevant = sum(1 for e in evaluations if e.get("classification") == "Irrelevant")

    sims = [e.get("similarity_score") for e in evaluations if e.get("similarity_score") is not None]
    avg_sim_pct = (sum(sims) / len(sims) * 100) if sims else 0.0
    avg_sim_pct = max(0.0, min(100.0, avg_sim_pct))

    return {
        "total_evaluations": total,
        "fully_relevant": fully,
        "partially_relevant": partial,
        "irrelevant": irrelevant,
        "avg_similarity_score": avg_sim_pct,
    }


def _compute_output_type_breakdown(evaluations: list) -> list:
    total = len(evaluations)
    counts = {key: 0 for key in OUTPUT_TYPE_LABELS}
    for e in evaluations:
        ot = e.get("output_type")
        if ot in counts:
            counts[ot] += 1

    breakdown = []
    for key, label in OUTPUT_TYPE_LABELS.items():
        count = counts[key]
        progress = (count / total) if total else 0.0
        breakdown.append((label, count, progress))
    return breakdown


def _normalize_similarity_score(value):
    if value is None:
        return None
    try:
        similarity = float(value)
    except (TypeError, ValueError):
        return None
    if similarity > 1.0:
        return similarity / 100.0
    return similarity


def _classify_score(score_pct: float) -> str:
    if score_pct >= 75:
        return "Fully Relevant"
    if score_pct >= 50:
        return "Partially Relevant"
    return "Irrelevant"


def _saved_evaluation_to_result(evaluation: dict) -> tuple[dict, list[tuple[str, str]]]:
    """Convert a stored evaluation row to the detailed-results screen shape."""
    similarity_score = _normalize_similarity_score(evaluation.get("similarity_score")) or 0.0
    criterion_scores = evaluation.get("criterion_scores") or {}
    criteria = []
    for name, value in criterion_scores.items():
        normalized = _normalize_similarity_score(value) or 0.0
        criteria.append((name, round(max(0.0, min(100.0, normalized * 100)))))

    rubric_details = evaluation.get("rubric_details") or []
    if isinstance(rubric_details, dict):
        rubric_details = [
            {"name": name, "description": description}
            for name, description in rubric_details.items()
        ]
    rubric = [
        (item.get("name", "Criterion"), item.get("description", ""))
        for item in rubric_details
        if isinstance(item, dict)
    ]

    result = {
        "name": evaluation.get("file_name") or "Untitled",
        "file": evaluation.get("file_name") or "Untitled",
        "file_path": evaluation.get("file_path") or "",
        "score": similarity_score * 100,
        "similarity_score": similarity_score,
        "classification": evaluation.get("classification") or _classify_score(similarity_score * 100),
        "criteria": criteria,
    }
    return result, rubric


def _build_live_evaluations(nav) -> list:
    if not nav:
        return []

    live_results = getattr(nav, "evaluation_results", None) or []
    if not live_results:
        return []

    prompt = getattr(nav, "evaluation_prompt", "") or ""
    rubric = getattr(nav, "evaluation_rubric", None) or []
    output_type_label = getattr(nav, "evaluation_output_type_label", "Short Answer") or "Short Answer"
    output_type_key = OUTPUT_TYPE_KEYS.get(output_type_label, "short_answer")

    live_evaluations = []
    for result in live_results:
        score_pct = float(result.get("score", 0.0) or 0.0)
        similarity_score = _normalize_similarity_score(result.get("similarity_score"))
        if similarity_score is None:
            similarity_score = score_pct / 100.0 if score_pct > 1.0 else score_pct

        live_evaluations.append(
            {
                "name": result.get("name") or result.get("file") or "Untitled",
                "file_name": result.get("file") or result.get("file_name") or result.get("name") or "Untitled",
                "prompt": prompt,
                "rubric_id": None,
                "output_type": output_type_key,
                "output_type_label": output_type_label,
                "similarity_score": similarity_score,
                "classification": result.get("classification") or _classify_score(score_pct),
                "created_at": "just now",
                "source": "live",
                "criterion_scores": {
                    name: value / 100
                    for name, value in result.get("criteria", [])
                },
                "rubric_details": [
                    {"name": name, "description": description}
                    for name, description in rubric
                ],
            }
        )

    return live_evaluations


def _merge_evaluations(live_evaluations: list, saved_evaluations: list) -> list:
    merged = []
    seen = set()

    def add_rows(rows: list):
        for evaluation in rows:
            key = (
                evaluation.get("output_type") or evaluation.get("output_type_label") or "",
                evaluation.get("file_name") or evaluation.get("name") or "",
                evaluation.get("prompt") or "",
            )
            if key in seen:
                continue
            seen.add(key)
            merged.append(evaluation)

    add_rows(live_evaluations)
    add_rows(saved_evaluations)
    return merged


def _format_relative_time(created_at: str) -> str:
    if not created_at:
        return ""
    try:
        ts = created_at.replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - dt
        seconds = delta.total_seconds()
        if seconds < 60:
            return "just now"
        if seconds < 3600:
            return f"{int(seconds // 60)}m ago"
        if seconds < 86400:
            return f"{int(seconds // 3600)}h ago"
        return dt.strftime("%b %d, %Y")
    except Exception:
        return created_at


def main(page: ft.Page, nav=None, role="evaluator"):
    page.title = "QualCheck - Dashboard"
    page.scroll = ft.ScrollMode.AUTO
    page.bgcolor = BG_COLOR
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0

    current_user = get_current_user()
    if not current_user:
        if nav and hasattr(nav, "navigate_to_login"):
            nav.navigate_to_login()
        return

    user_identity = getattr(current_user, "user", current_user)
    user_id = getattr(user_identity, "id", None)

    evaluations = _fetch_user_evaluations(user_id)
    live_evaluations = _build_live_evaluations(nav)
    dashboard_evaluations = _merge_evaluations(live_evaluations, evaluations)
    stats = _compute_stats(dashboard_evaluations)
    output_types = _compute_output_type_breakdown(dashboard_evaluations)

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------
    dashboard_header = ft.Container(
        content=ft.Column(
            [
                ft.Text("Evaluation Dashboard", size=26, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(height=6),
                ft.Text("Overview of your evaluations processed by QualCheck", size=13, color=TEXT_SECONDARY),
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

    total = stats["total_evaluations"]

    def pct_of_total(n):
        if not total:
            return "0% of total"
        return f"{round((n / total) * 100)}% of total"

    stats_row = ft.ResponsiveRow(
        controls=[
            ft.Container(stat_card(PRIMARY_BLUE, "Total Evaluations", stats["total_evaluations"]), col={"sm": 6, "md": 3}),
            ft.Container(stat_card(SUCCESS, "Fully Relevant", stats["fully_relevant"],
                      subtitle=pct_of_total(stats["fully_relevant"]), value_color=SUCCESS), col={"sm": 6, "md": 3}),
            ft.Container(stat_card(WARNING, "Partially Relevant", stats["partially_relevant"],
                      subtitle=pct_of_total(stats["partially_relevant"]), value_color=WARNING), col={"sm": 6, "md": 3}),
            ft.Container(stat_card(ERROR, "Irrelevant", stats["irrelevant"],
                      subtitle=pct_of_total(stats["irrelevant"]), value_color=ERROR), col={"sm": 6, "md": 3}),
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
                    f"{stats['avg_similarity_score']:.1f}%",
                    size=42, weight=ft.FontWeight.BOLD, color=PRIMARY_BLUE,
                ),
                ft.Container(height=12),
                ft.ProgressBar(
                    value=stats["avg_similarity_score"] / 100,
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
                *[output_type_row(label, count, progress) for label, count, progress in output_types],
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
    # Recent Evaluations section (scrollable + searchable)
    # ------------------------------------------------------------------
    def empty_state(msg="No evaluations yet. Create your first evaluation to see results here."):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Image(src="https://img.icons8.com/fluency/48/000000/bar-chart.png", width=48, height=48),
                    ft.Container(height=12),
                    ft.Text(msg, size=13, color=TEXT_SECONDARY, text_align=ft.TextAlign.CENTER),
                ],
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(vertical=80),
            alignment=ft.alignment.center,
        )

    def classification_badge(classification: str):
        color_map = {
            "Fully Relevant": (SUCCESS, "#dcfce7"),
            "Partially Relevant": (WARNING, "#fef3c7"),
            "Irrelevant": (ERROR, "#fee2e2"),
        }
        color, bg = color_map.get(classification, (TEXT_SECONDARY, SECTION_BG_COLOR))
        return ft.Container(
            content=ft.Text(classification or "—", size=11, color=color, weight=ft.FontWeight.W_600),
            bgcolor=bg,
            border_radius=20,
            padding=ft.padding.symmetric(horizontal=10, vertical=4),
        )

    def recent_evaluation_row(evaluation: dict):
        sim = evaluation.get("similarity_score")
        sim_pct = max(0.0, min(100.0, sim * 100)) if sim is not None else None
        output_type_label = OUTPUT_TYPE_LABELS.get(evaluation.get("output_type"), evaluation.get("output_type") or "—")
        title = evaluation.get("file_name") or (evaluation.get("prompt") or "")[:60] or "Untitled"
        result, rubric = _saved_evaluation_to_result(evaluation)
        expanded = {"value": False}
        arrow_icon = ft.Icon(ft.Icons.KEYBOARD_ARROW_DOWN, size=18, color=TEXT_SECONDARY)

        criterion_rows = []
        for criterion_name, criterion_pct in result["criteria"]:
            criterion_color = (
                SUCCESS if criterion_pct >= 75
                else WARNING if criterion_pct >= 50
                else ERROR
            )
            criterion_rows.append(
                ft.Row(
                    [
                        ft.Text(criterion_name, size=12, color=TEXT_SECONDARY, width=170),
                        ft.ProgressBar(
                            value=criterion_pct / 100,
                            bgcolor=SECTION_BG_COLOR,
                            color=criterion_color,
                            height=7,
                            border_radius=4,
                            expand=True,
                        ),
                        ft.Text(
                            f"{criterion_pct}%",
                            size=12,
                            color=TEXT_SECONDARY,
                            width=42,
                            text_align=ft.TextAlign.RIGHT,
                        ),
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )

        rubric_rows = [
            ft.Row(
                [
                    ft.Text(name, size=12, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY, width=170),
                    ft.Text(description or "No description", size=12, color=TEXT_SECONDARY, expand=True),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.START,
            )
            for name, description in rubric
        ]
        if not rubric_rows:
            rubric_rows = [ft.Text("Rubric details are unavailable for this older evaluation.", size=12, color=TEXT_TERTIARY)]

        detail_panel = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text(
                                            f"{result['score']:.1f}%",
                                            size=28,
                                            weight=ft.FontWeight.BOLD,
                                            color=classification_badge(evaluation.get("classification")).content.color,
                                        ),
                                        ft.Text(
                                            evaluation.get("classification") or "—",
                                            size=12,
                                            weight=ft.FontWeight.W_600,
                                            color=classification_badge(evaluation.get("classification")).content.color,
                                        ),
                                        ft.Text("Similarity Score", size=11, color=TEXT_SECONDARY),
                                    ],
                                    spacing=2,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                ),
                                bgcolor=SECTION_BG_COLOR,
                                border_radius=10,
                                padding=16,
                                width=150,
                                alignment=ft.alignment.center,
                            ),
                            ft.Column(
                                [
                                    ft.Text("CRITERION SCORES", size=11, color=TEXT_TERTIARY, weight=ft.FontWeight.BOLD),
                                    ft.Container(height=8),
                                    ft.Column(criterion_rows or [ft.Text("No criterion scores saved.", size=12, color=TEXT_TERTIARY)], spacing=9),
                                ],
                                spacing=0,
                                expand=True,
                            ),
                        ],
                        spacing=20,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                    ft.Divider(height=1, color=BORDER_COLOR),
                    ft.Column(
                        [
                            ft.Text("QUESTION", size=11, color=TEXT_TERTIARY, weight=ft.FontWeight.BOLD),
                            ft.Text(evaluation.get("prompt") or "No question saved.", size=12, color=TEXT_PRIMARY),
                        ],
                        spacing=6,
                    ),
                    ft.Column(
                        [
                            ft.Text("RUBRIC", size=11, color=TEXT_TERTIARY, weight=ft.FontWeight.BOLD),
                            ft.Column(rubric_rows, spacing=7),
                        ],
                        spacing=6,
                    ),
                ],
                spacing=14,
            ),
            bgcolor="#f1f5f9",
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
                    ft.Container(
                        content=ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, size=16, color=TEXT_SECONDARY),
                        width=32, height=32, border_radius=16, bgcolor=SECTION_BG_COLOR,
                        alignment=ft.alignment.center,
                    ),
                    ft.Column(
                        [
                            ft.Text(title, size=13, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                            ft.Text(
                                f"{output_type_label} · {_format_relative_time(evaluation.get('created_at'))}",
                                size=11, color=TEXT_TERTIARY,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.Text(
                        f"{sim_pct:.1f}%" if sim_pct is not None else "—",
                        size=13, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY, width=60,
                        text_align=ft.TextAlign.RIGHT,
                    ),
                    classification_badge(evaluation.get("classification")),
                    arrow_icon,
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(vertical=10),
            on_click=toggle_details,
            ink=True,
            tooltip="View evaluation details",
        )

        return ft.Column([summary_row, detail_panel], spacing=0)

    # --- Search + filter state (same pattern as ui_admin_submissions.py) ---
    history_state = {"query": "", "classification": "all"}

    def matches_history(evaluation, query, classification):
        if classification != "all" and evaluation.get("classification") != classification:
            return False
        if query:
            title = evaluation.get("file_name") or evaluation.get("name") or ""
            prompt = evaluation.get("prompt") or ""
            output_label = OUTPUT_TYPE_LABELS.get(evaluation.get("output_type"), "")
            haystack = f"{title} {prompt} {output_label}".lower()
            if query.lower() not in haystack:
                return False
        return True

    def get_filtered_history():
        return [
            ev for ev in dashboard_evaluations
            if matches_history(ev, history_state["query"], history_state["classification"])
        ]

    history_list = ft.ListView(spacing=0, height=380, auto_scroll=False)

    def rebuild_history(e=None):
        style_history_pills()
        filtered = get_filtered_history()
        if filtered:
            rows = []
            for i, ev in enumerate(filtered):
                rows.append(recent_evaluation_row(ev))
                if i < len(filtered) - 1:
                    rows.append(ft.Divider(height=1, color=BORDER_COLOR))
            history_list.controls = rows
        else:
            no_match_msg = (
                "No evaluations match your search."
                if (history_state["query"] or history_state["classification"] != "all")
                else "No evaluations yet. Create your first evaluation to see results here."
            )
            history_list.controls = [empty_state(no_match_msg)]
        page.update()

    history_search_bar = ft.TextField(
        hint_text="Search by file name, prompt, or type…",
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
        on_change=lambda e: (history_state.update({"query": e.control.value or ""}), rebuild_history()),
    )

    HISTORY_FILTERS = [
        ("all", "All"),
        ("Fully Relevant", "Fully Relevant"),
        ("Partially Relevant", "Partially Relevant"),
        ("Irrelevant", "Irrelevant"),
    ]

    def make_history_pill(key, label):
        def on_click(e):
            history_state["classification"] = key
            rebuild_history()

        return ft.Container(
            content=ft.Text(label, size=12, weight=ft.FontWeight.W_600),
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            border_radius=14,
            ink=True,
            on_click=on_click,
        )

    history_pills = {key: make_history_pill(key, label) for key, label in HISTORY_FILTERS}

    def style_history_pills():
        for key, pill in history_pills.items():
            selected = history_state["classification"] == key
            pill.bgcolor = PRIMARY_BLUE if selected else None
            pill.content.color = TEXT_WHITE if selected else TEXT_TERTIARY

    style_history_pills()

    history_filter_row = ft.Row(
        [history_pills[key] for key, _ in HISTORY_FILTERS],
        spacing=4,
    )

    recent_evaluations_section = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Recent Evaluations", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ft.Text(f"{len(dashboard_evaluations)} total", size=12, color=TEXT_TERTIARY),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(height=16),
                history_search_bar,
                ft.Container(height=10),
                history_filter_row,
                ft.Container(height=16),
                history_list,
            ],
            spacing=0,
        ),
        padding=ft.padding.all(24),
        bgcolor=CARD_BG_COLOR,
        border_radius=12,
        border=ft.border.all(1, BORDER_COLOR),
    )

    rebuild_history()

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