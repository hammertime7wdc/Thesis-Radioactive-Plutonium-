import flet as ft
from utils.utils import (
    BG_COLOR,
    CARD_BG_COLOR,
    SECTION_BG_COLOR,
    PRIMARY_BLUE,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    BORDER_COLOR,
)


# ─── Skeleton building blocks ───────────────────────────────────────
_BONE = "#e8eef5"       # primary placeholder bar colour
_BONE_DARK = "#dce4ee"  # slightly darker for accent bars


def _skeleton_block(width=None, height=14, radius=6, color=_BONE):
    """A single rounded placeholder rectangle."""
    return ft.Container(
        width=width,
        height=height,
        bgcolor=color,
        border_radius=radius,
    )


def _skeleton_circle(size=36, color=_BONE):
    return ft.Container(
        width=size,
        height=size,
        bgcolor=color,
        border_radius=size // 2,
    )


def _skeleton_card(content, padding=20, expand=False):
    """Wraps children in a card container matching the real CARD_BG style."""
    kwargs = {}
    if expand:
        kwargs["expand"] = True
    return ft.Container(
        content=ft.Column(content, spacing=10),
        padding=ft.padding.all(padding),
        bgcolor=CARD_BG_COLOR,
        border=ft.border.all(1, "#e2e8f0"),
        border_radius=12,
        **kwargs,
    )


def _skeleton_stat_card(accent_color=_BONE_DARK):
    """Matches the dashboard / results stat_card shape:
       label (small text) → spacer → big value → optional subtitle."""
    return ft.Container(
        content=ft.Column(
            [
                _skeleton_block(width=110, height=12),         # label
                ft.Container(height=8),
                _skeleton_block(width=60, height=26, radius=4), # big value
                ft.Container(height=6),
                _skeleton_block(width=80, height=10),          # subtitle
            ],
            spacing=0,
        ),
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


# ─── Per-screen skeletons ───────────────────────────────────────────

def _dashboard_skeleton():
    """Mirrors ui_dashboard.py:
       - Header: title 26px + subtitle 13px
       - 4 stat cards in ResponsiveRow
       - Middle row: similarity card + output-type card  (2-col)
       - Recent evaluations card with search bar + filter pills + list rows
    """
    # Header
    header = ft.Container(
        content=ft.Column(
            [
                _skeleton_block(width=250, height=26),   # "Evaluation Dashboard"
                ft.Container(height=6),
                _skeleton_block(width=380, height=13),   # subtitle
            ],
            spacing=0,
        ),
        padding=ft.padding.only(left=32, right=32, top=32, bottom=16),
    )

    # 4 stat cards
    stats_row = ft.ResponsiveRow(
        controls=[
            ft.Container(_skeleton_stat_card(_BONE_DARK), col={"sm": 6, "md": 3}),
            ft.Container(_skeleton_stat_card(_BONE_DARK), col={"sm": 6, "md": 3}),
            ft.Container(_skeleton_stat_card(_BONE_DARK), col={"sm": 6, "md": 3}),
            ft.Container(_skeleton_stat_card(_BONE_DARK), col={"sm": 6, "md": 3}),
        ],
        spacing=16,
        run_spacing=16,
    )

    # Similarity score card
    sim_card = ft.Container(
        content=ft.Column(
            [
                _skeleton_block(width=200, height=15),     # "Average Similarity Score"
                ft.Container(height=24),
                _skeleton_block(width=120, height=42),     # big % value
                ft.Container(height=12),
                _skeleton_block(height=8, radius=4),       # progress bar
            ],
            spacing=0,
        ),
        padding=ft.padding.all(24),
        bgcolor=CARD_BG_COLOR,
        border_radius=12,
        border=ft.border.all(1, BORDER_COLOR),
    )

    # Output type card – 3 rows each: label-row + progress-bar + spacer
    def _output_row():
        return ft.Column(
            [
                ft.Row(
                    [_skeleton_block(width=100, height=13), _skeleton_block(width=20, height=13)],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(height=8),
                _skeleton_block(height=6, radius=3),
                ft.Container(height=16),
            ],
            spacing=0,
        )

    output_card = ft.Container(
        content=ft.Column(
            [
                _skeleton_block(width=140, height=15),  # "By Output Type"
                ft.Container(height=20),
                _output_row(),
                _output_row(),
                _output_row(),
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
            ft.Container(sim_card, col={"sm": 12, "md": 6}),
            ft.Container(output_card, col={"sm": 12, "md": 6}),
        ],
        spacing=24,
        run_spacing=24,
    )

    # Recent evaluations card
    def _eval_row():
        return ft.Container(
            content=ft.Row(
                [
                    _skeleton_circle(32),
                    ft.Column(
                        [
                            _skeleton_block(width=200, height=13),
                            ft.Container(height=4),
                            _skeleton_block(width=140, height=11),
                        ],
                        spacing=0,
                        expand=True,
                    ),
                    _skeleton_block(width=50, height=13),
                    _skeleton_block(width=90, height=24, radius=12),   # badge
                    _skeleton_block(width=18, height=18, radius=3),    # arrow
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(vertical=10),
        )

    # Search bar placeholder
    search_placeholder = ft.Container(
        content=ft.Row(
            [
                _skeleton_block(width=18, height=18, radius=3),
                _skeleton_block(width=250, height=13),
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        height=42,
        border_radius=8,
        border=ft.border.all(1, BORDER_COLOR),
        padding=ft.padding.symmetric(horizontal=14, vertical=8),
        bgcolor=CARD_BG_COLOR,
    )

    # Filter pills
    pills_row = ft.Row(
        [_skeleton_block(width=40, height=28, radius=14),
         _skeleton_block(width=90, height=28, radius=14),
         _skeleton_block(width=110, height=28, radius=14),
         _skeleton_block(width=70, height=28, radius=14)],
        spacing=4,
    )

    recent_card = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [_skeleton_block(width=160, height=15), _skeleton_block(width=60, height=12)],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(height=16),
                search_placeholder,
                ft.Container(height=10),
                pills_row,
                ft.Container(height=16),
                _eval_row(),
                ft.Divider(height=1, color=BORDER_COLOR),
                _eval_row(),
                ft.Divider(height=1, color=BORDER_COLOR),
                _eval_row(),
                ft.Divider(height=1, color=BORDER_COLOR),
                _eval_row(),
            ],
            spacing=0,
        ),
        padding=ft.padding.all(24),
        bgcolor=CARD_BG_COLOR,
        border_radius=12,
        border=ft.border.all(1, BORDER_COLOR),
    )

    return ft.Container(
        expand=True,
        bgcolor=BG_COLOR,
        content=ft.Column(
            [
                header,
                ft.Container(content=stats_row, padding=ft.padding.symmetric(horizontal=32)),
                ft.Container(height=24),
                ft.Container(content=middle_row, padding=ft.padding.symmetric(horizontal=32)),
                ft.Container(height=24),
                ft.Container(content=recent_card, padding=ft.padding.symmetric(horizontal=32)),
                ft.Container(height=40),
            ],
            spacing=0,
        ),
    )


def _results_skeleton():
    """Mirrors studenta_result.py:
       - Header: back arrow + title "Evaluation Results" + subtitle
       - 4 stat cards in a row
       - 2-col row: classification breakdown + distribution chart
       - Context panel: academic prompt + rubric
       - Student list header + expandable rows
    """
    header = ft.Container(
        content=ft.Row(
            [
                ft.Column(
                    [
                        ft.Row(
                            [
                                _skeleton_block(width=32, height=32, radius=16),   # back btn
                                _skeleton_block(width=220, height=24),             # title
                            ],
                            spacing=4,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Container(height=2),
                        _skeleton_block(width=280, height=13),                     # subtitle
                    ],
                    spacing=0,
                ),
            ],
        ),
        padding=ft.padding.only(left=24, right=24, top=24, bottom=16),
    )

    # 4 stat cards
    def _result_stat():
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [_skeleton_block(width=90, height=12), _skeleton_block(width=16, height=16, radius=3)],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(height=6),
                    _skeleton_block(width=70, height=22),
                ],
                spacing=0,
            ),
            bgcolor=CARD_BG_COLOR,
            border=ft.border.all(1, BORDER_COLOR),
            border_radius=10,
            padding=16,
            expand=True,
        )

    stat_row = ft.Row([_result_stat(), _result_stat(), _result_stat(), _result_stat()], spacing=16)

    # Classification + Distribution
    classification = ft.Container(
        content=ft.Column(
            [
                _skeleton_block(width=200, height=15),
                ft.Container(height=14),
                _skeleton_block(height=10, radius=6),      # segmented bar
                ft.Container(height=16),
                *[ft.Row(
                    [
                        ft.Row([_skeleton_block(width=8, height=8, radius=4), _skeleton_block(width=110, height=13)], spacing=8),
                        _skeleton_block(width=60, height=13),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ) for _ in range(3)],
            ],
            spacing=8,
        ),
        bgcolor=CARD_BG_COLOR,
        border=ft.border.all(1, BORDER_COLOR),
        border_radius=10,
        padding=20,
        expand=1,
    )

    distribution = ft.Container(
        content=ft.Column(
            [
                _skeleton_block(width=170, height=15),
                ft.Container(height=14),
                ft.Row(
                    [
                        ft.Column([ft.Container(height=50), _skeleton_block(width=48, height=40, radius=4), ft.Container(height=8), _skeleton_block(width=60, height=11)], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Column([ft.Container(height=60), _skeleton_block(width=48, height=30, radius=4), ft.Container(height=8), _skeleton_block(width=60, height=11)], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Column([ft.Container(height=70), _skeleton_block(width=48, height=20, radius=4), ft.Container(height=8), _skeleton_block(width=60, height=11)], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_EVENLY,
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

    breakdown_row = ft.Row([classification, distribution], spacing=16)

    # Context panel
    context_panel = ft.Container(
        content=ft.Row(
            [
                ft.Column(
                    [
                        _skeleton_block(width=130, height=11),
                        ft.Container(height=8),
                        _skeleton_block(width=300, height=13),
                        _skeleton_block(height=13),
                    ],
                    spacing=4,
                    expand=1,
                ),
                ft.Column(
                    [
                        _skeleton_block(width=110, height=11),
                        ft.Container(height=8),
                        *[ft.Row([_skeleton_circle(18), _skeleton_block(width=260, height=13)], spacing=8)
                          for _ in range(3)],
                    ],
                    spacing=6,
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

    # Student rows
    def _student_row():
        return ft.Container(
            content=ft.Row(
                [
                    _skeleton_block(width=20, height=13),
                    _skeleton_circle(36),
                    ft.Column(
                        [_skeleton_block(width=160, height=14), _skeleton_block(width=120, height=12)],
                        spacing=2,
                        expand=True,
                    ),
                    ft.Column(
                        [
                            _skeleton_block(width=50, height=13),
                            _skeleton_block(width=100, height=6, radius=3),
                        ],
                        spacing=4,
                    ),
                    _skeleton_block(width=95, height=26, radius=14),   # badge
                    _skeleton_block(width=18, height=18, radius=3),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=24, vertical=14),
        )

    student_header = ft.Container(
        content=ft.Row(
            [_skeleton_block(width=50, height=11), _skeleton_block(width=120, height=11),
             ft.Container(expand=True),
             _skeleton_block(width=60, height=11), _skeleton_block(width=100, height=11),
             _skeleton_block(width=18, height=11)],
            spacing=12,
        ),
        padding=ft.padding.symmetric(horizontal=24, vertical=14),
        bgcolor=SECTION_BG_COLOR,
    )

    student_list = _skeleton_card(
        [
            ft.Row(
                [_skeleton_block(width=130, height=15), ft.Container(expand=True),
                 _skeleton_block(width=100, height=28, radius=6), _skeleton_block(width=100, height=28, radius=6)],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Container(height=8),
            student_header,
            _student_row(),
            ft.Divider(height=1, color=BORDER_COLOR),
            _student_row(),
            ft.Divider(height=1, color=BORDER_COLOR),
            _student_row(),
        ],
        padding=0,
    )

    return ft.Container(
        expand=True,
        bgcolor=BG_COLOR,
        content=ft.Column(
            [
                header,
                ft.Container(content=stat_row, padding=ft.padding.symmetric(horizontal=24)),
                ft.Container(height=16),
                ft.Container(content=breakdown_row, padding=ft.padding.symmetric(horizontal=24)),
                ft.Container(height=16),
                ft.Container(content=context_panel, padding=ft.padding.symmetric(horizontal=24)),
                ft.Container(height=16),
                ft.Container(content=student_list, padding=ft.padding.symmetric(horizontal=24)),
                ft.Container(height=40),
            ],
            spacing=0,
        ),
    )


def _account_skeleton():
    """Mirrors ui_account.py:
       - Top header: "Profile Settings" + subtitle + back button
       - Two-column layout: left nav sidebar | right content card
       - Left nav: 3 menu items + divider + stats (Evaluations / Role / Member since)
       - Right content: profile card with avatar row, 2×2 form fields, bio, save button
    """
    # Top header
    top_header = ft.Container(
        content=ft.Row(
            [
                ft.Column(
                    [
                        _skeleton_block(width=180, height=20),   # "Profile Settings"
                        ft.Container(height=2),
                        _skeleton_block(width=300, height=12),   # subtitle
                    ],
                    spacing=2,
                ),
                ft.Container(expand=True),
                _skeleton_block(width=200, height=14),           # back button
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.padding.only(left=32, right=32, top=16, bottom=0),
    )

    # Sidebar nav items
    def _nav_item(w=120):
        return ft.Container(
            content=ft.Row(
                [_skeleton_block(width=16, height=16, radius=3), ft.Container(width=8), _skeleton_block(width=w, height=13)],
                spacing=0,
            ),
            padding=ft.padding.symmetric(horizontal=14, vertical=9),
            border_radius=8,
        )

    left_nav = ft.Column(
        [
            ft.Container(  # first item (active highlight)
                content=ft.Row(
                    [_skeleton_block(width=16, height=16, radius=3), ft.Container(width=8), _skeleton_block(width=80, height=13)],
                    spacing=0,
                ),
                padding=ft.padding.symmetric(horizontal=14, vertical=9),
                border_radius=8,
                bgcolor="#eef2f7",
            ),
            ft.Container(height=6),
            _nav_item(w=90),
            ft.Container(height=6),
            _nav_item(w=110),
            ft.Container(height=14),
            ft.Divider(color=BORDER_COLOR),
            ft.Container(height=12),
            # Stats block
            ft.Column(
                [
                    ft.Row([_skeleton_block(width=15, height=15, radius=3), ft.Container(width=8), _skeleton_block(width=80, height=12)], spacing=0),
                    _skeleton_block(width=30, height=14),
                    ft.Container(height=12),
                    ft.Row([_skeleton_block(width=15, height=15, radius=3), ft.Container(width=8), _skeleton_block(width=50, height=12)], spacing=0),
                    _skeleton_block(width=70, height=13),
                    ft.Container(height=12),
                    ft.Row([_skeleton_block(width=15, height=15, radius=3), ft.Container(width=8), _skeleton_block(width=90, height=12)], spacing=0),
                    _skeleton_block(width=60, height=13),
                ],
                spacing=0,
            ),
        ],
        spacing=0,
    )

    # Right side — profile card
    avatar_row = ft.Row(
        [
            _skeleton_circle(64),
            ft.Container(width=14),
            ft.Column(
                [
                    _skeleton_block(width=140, height=16),   # name
                    _skeleton_block(width=200, height=12),   # email
                    ft.Container(height=4),
                    _skeleton_block(width=80, height=20, radius=10),  # role pill
                ],
                spacing=2,
            ),
        ],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    def _form_field(w=290):
        return ft.Column(
            [
                _skeleton_block(width=90, height=12),
                ft.Container(height=4),
                ft.Container(
                    height=40, width=w, border_radius=8,
                    border=ft.border.all(1, BORDER_COLOR), bgcolor=CARD_BG_COLOR,
                ),
            ],
            spacing=0,
        )

    profile_content = ft.Column(
        [
            _skeleton_block(width=160, height=15),    # "Personal Information"
            ft.Container(height=12),
            avatar_row,
            ft.Container(height=18),
            ft.Row([_form_field(), _form_field()], spacing=14),
            ft.Container(height=12),
            ft.Row([_form_field(), _form_field()], spacing=14),
            ft.Container(height=12),
            # Bio field (wider)
            ft.Column(
                [
                    _skeleton_block(width=40, height=12),
                    ft.Container(height=4),
                    ft.Container(
                        height=64, border_radius=8,
                        border=ft.border.all(1, BORDER_COLOR), bgcolor=CARD_BG_COLOR,
                    ),
                ],
                spacing=0,
            ),
            ft.Container(height=14),
            ft.Row([ft.Container(expand=True), _skeleton_block(width=130, height=38, radius=8, color=_BONE_DARK)]),
            ft.Container(height=18),
            # Recent activity
            ft.Container(
                content=ft.Column(
                    [
                        _skeleton_block(width=140, height=15),
                        ft.Container(height=10),
                        *[ft.Row([_skeleton_block(width=16, height=16, radius=3), ft.Container(width=10), _skeleton_block(width=200, height=12)], spacing=0)
                          for _ in range(3)],
                    ],
                    spacing=8,
                ),
                padding=ft.padding.all(16),
                bgcolor=SECTION_BG_COLOR,
                border_radius=10,
                border=ft.border.all(1, BORDER_COLOR),
            ),
        ],
        spacing=0,
    )

    profile_card = ft.Container(
        content=profile_content,
        padding=ft.padding.all(18),
        bgcolor=CARD_BG_COLOR,
        border_radius=10,
        border=ft.border.all(1, BORDER_COLOR),
        expand=True,
    )

    body = ft.Container(
        content=ft.Row(
            [
                ft.Container(width=200, content=left_nav),
                ft.Container(width=20),
                profile_card,
            ],
            vertical_alignment=ft.CrossAxisAlignment.START,
        ),
        padding=ft.padding.symmetric(horizontal=32),
    )

    return ft.Container(
        expand=True,
        bgcolor=BG_COLOR,
        content=ft.Column(
            [
                top_header,
                ft.Container(height=8),
                body,
                ft.Container(height=24),
            ],
            spacing=0,
        ),
    )


def _evaluation_skeleton():
    """Mirrors ui_short_answer.py / ui_essay.py / ui_code_report.py:
       - Output Type section: label + 3 button placeholders
       - Academic Prompt section: label + multiline text area
       - Rubric section: label + subtitle + 3 criterion rows (badge + text field)
       - Student Responses section: label + subtitle + upload area
       - Evaluate button
    """
    # Output type section
    output_type = ft.Container(
        content=ft.Column(
            [
                _skeleton_block(width=110, height=16),   # "Output Type"
                ft.Container(height=10),
                ft.Row(
                    [
                        _skeleton_block(width=120, height=40, radius=8, color=_BONE_DARK),
                        _skeleton_block(width=80, height=40, radius=8),
                        _skeleton_block(width=110, height=40, radius=8),
                    ],
                    spacing=10,
                ),
            ],
            spacing=0,
        ),
        padding=ft.padding.all(20),
        bgcolor=CARD_BG_COLOR,
        border_radius=12,
        border=ft.border.all(1, BORDER_COLOR),
    )

    # Prompt section
    prompt = ft.Container(
        content=ft.Column(
            [
                _skeleton_block(width=220, height=14),   # "Academic Prompt / Question"
                ft.Container(height=8),
                ft.Container(
                    height=80, border_radius=8,
                    border=ft.border.all(1, BORDER_COLOR), bgcolor=CARD_BG_COLOR,
                ),
            ],
            spacing=0,
        ),
        padding=ft.padding.all(20),
        bgcolor=CARD_BG_COLOR,
        border_radius=12,
        border=ft.border.all(1, BORDER_COLOR),
    )

    # Rubric section
    def _criterion_row():
        return ft.Column(
            [
                ft.Row(
                    [
                        _skeleton_circle(20, _BONE_DARK),      # numbered badge
                        ft.Container(width=8),
                        _skeleton_block(width=150, height=13),  # criterion name
                    ],
                    spacing=0,
                ),
                ft.Container(height=6),
                ft.Container(
                    height=52, border_radius=8,
                    border=ft.border.all(1, BORDER_COLOR), bgcolor=CARD_BG_COLOR,
                ),
            ],
            spacing=0,
        )

    rubric = ft.Container(
        content=ft.Column(
            [
                _skeleton_block(width=150, height=14),    # "Rubric Descriptor"
                ft.Container(height=4),
                _skeleton_block(width=400, height=12),    # subtitle
                ft.Container(height=12),
                _criterion_row(),
                ft.Container(height=12),
                _criterion_row(),
                ft.Container(height=12),
                _criterion_row(),
            ],
            spacing=0,
        ),
        padding=ft.padding.all(20),
        bgcolor=CARD_BG_COLOR,
        border_radius=12,
        border=ft.border.all(1, BORDER_COLOR),
    )

    # Upload section
    responses = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        _skeleton_block(width=150, height=14),
                        ft.Container(width=8),
                        _skeleton_block(width=14, height=14, radius=3),
                        ft.Container(width=4),
                        _skeleton_block(width=90, height=12),
                    ],
                    spacing=0,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(height=4),
                _skeleton_block(width=420, height=12),  # subtitle
                ft.Container(height=12),
                # Upload area (dashed box placeholder)
                ft.Container(
                    content=ft.Column(
                        [
                            _skeleton_block(width=48, height=48, radius=8),
                            ft.Container(height=12),
                            _skeleton_block(width=200, height=14),
                            ft.Container(height=4),
                            _skeleton_block(width=250, height=12),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    bgcolor="#f8fafc",
                    border=ft.border.all(2, "#cbd5e1"),
                    border_radius=12,
                    padding=ft.padding.symmetric(vertical=40, horizontal=20),
                    alignment=ft.alignment.center,
                ),
            ],
            spacing=0,
        ),
        padding=ft.padding.all(20),
        bgcolor=CARD_BG_COLOR,
        border_radius=12,
        border=ft.border.all(1, BORDER_COLOR),
    )

    # Evaluate button
    evaluate_btn = ft.Container(
        content=_skeleton_block(width=200, height=18, color="#d0d9e6"),
        height=52,
        border_radius=10,
        bgcolor=_BONE_DARK,
        alignment=ft.alignment.center,
    )

    return ft.Container(
        expand=True,
        bgcolor=BG_COLOR,
        padding=ft.padding.symmetric(horizontal=32, vertical=28),
        content=ft.Column(
            [
                _skeleton_block(width=280, height=26),      # page title
                ft.Container(height=6),
                _skeleton_block(width=350, height=13),      # subtitle
                ft.Container(height=20),
                output_type,
                ft.Container(height=16),
                prompt,
                ft.Container(height=16),
                rubric,
                ft.Container(height=16),
                responses,
                ft.Container(height=20),
                evaluate_btn,
            ],
            spacing=0,
        ),
    )


def _admin_users_skeleton():
    """Mirrors ui_admin.py:
       - Users section: search bar + filter pills + add-user button
       - Grid of user cards (3 placeholder cards in a wrapping row)
       - "Showing X of Y users" footer
    """
    # Search + pills + button row
    search = ft.Container(
        content=ft.Row(
            [_skeleton_block(width=18, height=18, radius=3), _skeleton_block(width=220, height=13)],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        height=42,
        border_radius=8,
        border=ft.border.all(1, BORDER_COLOR),
        padding=ft.padding.symmetric(horizontal=14, vertical=8),
        bgcolor=CARD_BG_COLOR,
        expand=True,
    )

    pills = ft.Row(
        [_skeleton_block(width=70, height=36, radius=20),
         _skeleton_block(width=80, height=36, radius=20),
         _skeleton_block(width=90, height=36, radius=20)],
        spacing=8,
    )

    add_btn = _skeleton_block(width=120, height=40, radius=8, color=_BONE_DARK)

    header_row = ft.Row(
        [search, ft.Container(width=16), pills, ft.Container(width=16), add_btn],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    # User card placeholders
    def _user_card():
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [_skeleton_circle(40), ft.Container(width=10),
                         ft.Column([_skeleton_block(width=120, height=14), _skeleton_block(width=160, height=12)], spacing=4, expand=True),
                         _skeleton_block(width=60, height=24, radius=12)],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=10),
                    ft.Divider(height=1, color=BORDER_COLOR),
                    ft.Container(height=10),
                    ft.Row([_skeleton_block(width=80, height=11), _skeleton_block(width=60, height=11)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Container(height=8),
                    ft.Row([_skeleton_block(width=80, height=11), _skeleton_block(width=80, height=11)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Container(height=8),
                    ft.Row([_skeleton_block(width=90, height=11), _skeleton_block(width=40, height=22, radius=11)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ],
                spacing=0,
            ),
            padding=ft.padding.all(16),
            bgcolor=CARD_BG_COLOR,
            border=ft.border.all(1, BORDER_COLOR),
            border_radius=12,
            width=320,
        )

    cards_row = ft.Row(
        [_user_card(), _user_card(), _user_card()],
        wrap=True,
        spacing=24,
        run_spacing=20,
    )

    users_section = ft.Container(
        content=ft.Column(
            [
                header_row,
                ft.Container(height=16),
                cards_row,
                ft.Container(height=12),
                ft.Row([ft.Container(expand=True), _skeleton_block(width=160, height=12)]),
            ],
            spacing=0,
        ),
        padding=ft.padding.all(24),
        bgcolor=CARD_BG_COLOR,
        border_radius=12,
        border=ft.border.all(1, BORDER_COLOR),
    )

    return ft.Container(
        expand=True,
        bgcolor=BG_COLOR,
        content=ft.Column(
            [
                ft.Container(content=users_section, padding=ft.padding.symmetric(horizontal=32)),
                ft.Container(height=40),
            ],
            spacing=0,
        ),
    )


def _admin_analytics_skeleton():
    """Mirrors ui_admin_analytics.py:
       - Header "Analytics" + "Last 30 days"
       - 2 stat cards row
       - 2-col row: pie chart + radar chart
       - Full-width bar chart
    """
    header = ft.Row(
        [_skeleton_block(width=120, height=22), ft.Container(expand=True), _skeleton_block(width=100, height=13)],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    # 2 stat cards
    def _stat():
        return ft.Container(
            content=ft.Column(
                [
                    _skeleton_block(width=130, height=13),
                    ft.Container(height=6),
                    _skeleton_block(width=80, height=28),
                    ft.Container(height=2),
                    _skeleton_block(width=150, height=12),
                ],
                spacing=0,
            ),
            padding=ft.padding.all(20),
            bgcolor=CARD_BG_COLOR,
            border_radius=12,
            border=ft.border.all(1, BORDER_COLOR),
            expand=True,
        )

    stats_row = ft.Row([_stat(), ft.Container(width=16), _stat()])

    # Chart cards
    def _chart_card(title_w=180, inner_h=240):
        return ft.Container(
            content=ft.Column(
                [
                    _skeleton_block(width=title_w, height=16),
                    ft.Container(height=16),
                    _skeleton_block(height=inner_h, radius=8),
                    ft.Container(height=12),
                    ft.Row(
                        [_skeleton_block(width=90, height=12), _skeleton_block(width=110, height=12), _skeleton_block(width=70, height=12)],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=20,
                    ),
                ],
                spacing=0,
            ),
            padding=ft.padding.all(24),
            bgcolor=CARD_BG_COLOR,
            border_radius=12,
            border=ft.border.all(1, BORDER_COLOR),
            expand=True,
        )

    charts_row = ft.Row([_chart_card(200, 240), ft.Container(width=16), _chart_card(180, 240)])

    bar_chart = ft.Container(
        content=ft.Column(
            [
                _skeleton_block(width=220, height=16),
                ft.Container(height=16),
                _skeleton_block(height=200, radius=8),
            ],
            spacing=0,
        ),
        padding=ft.padding.all(24),
        bgcolor=CARD_BG_COLOR,
        border_radius=12,
        border=ft.border.all(1, BORDER_COLOR),
    )

    return ft.Container(
        expand=True,
        bgcolor=BG_COLOR,
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Column(
                        [
                            header,
                            ft.Container(height=20),
                            stats_row,
                            ft.Container(height=24),
                            charts_row,
                            ft.Container(height=24),
                            bar_chart,
                            ft.Container(height=40),
                        ],
                        spacing=0,
                    ),
                    padding=ft.padding.symmetric(horizontal=32),
                ),
            ],
            spacing=0,
        ),
    )


def _admin_submissions_skeleton():
    """Mirrors ui_admin_submissions.py:
       - Filter section: search bar + filter icon + export button
       - Table header row
       - 5 submission placeholder rows
    """
    search = ft.Container(
        content=ft.Row(
            [_skeleton_block(width=18, height=18, radius=3), _skeleton_block(width=240, height=13)],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        height=42,
        border_radius=8,
        border=ft.border.all(1, BORDER_COLOR),
        padding=ft.padding.symmetric(horizontal=14, vertical=8),
        bgcolor=CARD_BG_COLOR,
        expand=True,
    )

    filter_icon = _skeleton_block(width=36, height=36, radius=8)
    export_btn = _skeleton_block(width=130, height=40, radius=20, color=_BONE_DARK)

    filter_section = ft.Container(
        content=ft.Row(
            [search, ft.Container(width=12), filter_icon, ft.Container(width=12), export_btn],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.padding.symmetric(horizontal=24, vertical=16),
    )

    # Table header
    table_header = ft.Container(
        content=ft.Row(
            [
                _skeleton_block(width=100, height=11, color=_BONE_DARK),  # STUDENT FILE
                ft.Container(expand=True),
                _skeleton_block(width=50, height=11, color=_BONE_DARK),   # SCORE
                _skeleton_block(width=100, height=11, color=_BONE_DARK),  # CLASSIFICATION
                _skeleton_block(width=60, height=11, color=_BONE_DARK),   # TYPE
                _skeleton_block(width=80, height=11, color=_BONE_DARK),   # EVALUATOR
                _skeleton_block(width=70, height=11, color=_BONE_DARK),   # DATE
                ft.Container(width=18),
            ],
            spacing=12,
        ),
        bgcolor=SECTION_BG_COLOR,
        padding=ft.padding.symmetric(horizontal=16, vertical=14),
    )

    # Submission rows
    def _sub_row():
        return ft.Container(
            content=ft.Row(
                [
                    _skeleton_block(width=18, height=18, radius=3),
                    _skeleton_block(width=160, height=13),
                    ft.Container(expand=True),
                    _skeleton_block(width=45, height=13),
                    _skeleton_block(width=95, height=22, radius=10),
                    _skeleton_block(width=80, height=13),
                    _skeleton_block(width=90, height=13),
                    _skeleton_block(width=80, height=13),
                    _skeleton_block(width=18, height=18, radius=3),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=16, vertical=14),
            border=ft.border.only(bottom=ft.BorderSide(1, BORDER_COLOR)),
        )

    submissions_card = ft.Container(
        content=ft.Column(
            [
                filter_section,
                ft.Container(
                    content=ft.Column(
                        [table_header, _sub_row(), _sub_row(), _sub_row(), _sub_row(), _sub_row()],
                        spacing=0,
                    ),
                    padding=ft.padding.symmetric(horizontal=24),
                ),
            ],
            spacing=0,
        ),
        padding=ft.padding.symmetric(vertical=24),
        bgcolor=CARD_BG_COLOR,
        border_radius=12,
        border=ft.border.all(1, BORDER_COLOR),
    )

    return ft.Container(
        expand=True,
        bgcolor=BG_COLOR,
        content=ft.Column(
            [
                ft.Container(content=submissions_card, padding=ft.padding.symmetric(horizontal=32)),
                ft.Container(height=40),
            ],
            spacing=0,
        ),
    )


def _admin_settings_skeleton():
    """Mirrors ui_admin_settings_audit.py:
       - Audit Log card with icon + title
       - Timeline entries (icon + action row + timestamp)
    """
    def _audit_entry():
        return ft.Container(
            content=ft.Row(
                [
                    _skeleton_block(width=16, height=16, radius=3),
                    ft.Container(width=12),
                    ft.Column(
                        [
                            ft.Row(
                                [_skeleton_block(width=140, height=13), _skeleton_block(width=200, height=13)],
                                spacing=8,
                            ),
                            ft.Container(height=2),
                            _skeleton_block(width=180, height=12),
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

    audit_card = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [_skeleton_block(width=20, height=20, radius=3), ft.Container(width=8), _skeleton_block(width=100, height=18)],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=0,
                ),
                ft.Container(height=16),
                _audit_entry(),
                _audit_entry(),
                _audit_entry(),
                _audit_entry(),
                _audit_entry(),
            ],
            spacing=0,
        ),
        padding=ft.padding.all(24),
        bgcolor=CARD_BG_COLOR,
        border_radius=12,
        border=ft.border.all(1, BORDER_COLOR),
    )

    return ft.Container(
        expand=True,
        bgcolor=BG_COLOR,
        content=ft.Column(
            [
                ft.Container(content=audit_card, padding=ft.padding.symmetric(horizontal=32)),
                ft.Container(height=40),
            ],
            spacing=0,
        ),
    )


# ─── Public API ──────────────────────────────────────────────────────

_SKELETON_MAP = {
    "dashboard": _dashboard_skeleton,
    "results": _results_skeleton,
    "account": _account_skeleton,
    "evaluation": _evaluation_skeleton,
    "admin_users": _admin_users_skeleton,
    "admin_analytics": _admin_analytics_skeleton,
    "admin_submissions": _admin_submissions_skeleton,
    "admin_settings": _admin_settings_skeleton,
}


def screen_skeleton(screen="evaluation"):
    """Return a lightweight loading shape matching the destination screen."""
    builder = _SKELETON_MAP.get(screen)
    if builder:
        return builder()

    # Fallback: any admin_ prefix → admin_users skeleton
    if screen.startswith("admin_"):
        return _admin_users_skeleton()

    # Default to evaluation skeleton
    return _evaluation_skeleton()


def PageSkeleton():
    """Backward-compatible default skeleton for callers outside navigation."""
    return screen_skeleton()


# ─── Evaluation progress dialog (unchanged) ─────────────────────────

class EvaluationProgressDialog:
    """
    Modal progress dialog displayed during AI model evaluation.
    Provides live status, file detail, and a progress bar.
    """
    def __init__(self, title: str = "Evaluating Responses", subtitle: str = "BERT Semantic Evaluation in progress..."):
        self.page = None
        self.title_text = ft.Text(title, size=17, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)
        self.subtitle_text = ft.Text(subtitle, size=12, color=TEXT_SECONDARY)
        
        self.spinner = ft.ProgressRing(width=28, height=28, stroke_width=3, color=PRIMARY_BLUE)
        self.status_label = ft.Text(
            "Initializing evaluation model...",
            size=13,
            weight=ft.FontWeight.W_600,
            color=TEXT_PRIMARY,
            no_wrap=False,
        )
        self.detail_label = ft.Text(
            "Loading neural network weights...",
            size=12,
            color=TEXT_SECONDARY,
            no_wrap=False,
        )
        self.progress_bar = ft.ProgressBar(
            value=None,
            color=PRIMARY_BLUE,
            bgcolor="#e2e8f0",
            height=6,
            border_radius=3,
        )
        self.percent_label = ft.Text("", size=11, weight=ft.FontWeight.BOLD, color=PRIMARY_BLUE)

        content = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Icon(ft.Icons.AUTO_AWESOME, color=PRIMARY_BLUE, size=20),
                                width=36,
                                height=36,
                                border_radius=18,
                                bgcolor="#eff6ff",
                                alignment=ft.alignment.center,
                            ),
                            ft.Column(
                                [
                                    self.title_text,
                                    self.subtitle_text,
                                ],
                                spacing=2,
                                expand=True,
                            ),
                        ],
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Divider(height=16, color=BORDER_COLOR),
                    ft.Row(
                        [
                            self.spinner,
                            ft.Column(
                                [
                                    self.status_label,
                                    self.detail_label,
                                ],
                                spacing=2,
                                expand=True,
                            ),
                        ],
                        spacing=14,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=8),
                    self.progress_bar,
                    ft.Row(
                        [
                            ft.Text("Please wait, do not close the window.", size=11, color=TEXT_SECONDARY, italic=True),
                            self.percent_label,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ],
                tight=True,
                spacing=6,
            ),
            width=440,
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
        )

        self.dialog = ft.AlertDialog(
            modal=True,
            content=content,
            bgcolor=CARD_BG_COLOR,
            shape=ft.RoundedRectangleBorder(radius=12),
        )

    def open(self, page: ft.Page):
        self.page = page
        try:
            page.open(self.dialog)
        except Exception:
            page.dialog = self.dialog
            self.dialog.open = True
            try:
                page.update()
            except Exception:
                pass

    def update_progress(self, status: str = None, detail: str = None, progress_pct: float = None):
        if status is not None:
            self.status_label.value = status
        if detail is not None:
            self.detail_label.value = detail
        if progress_pct is not None:
            clamped = max(0.0, min(1.0, float(progress_pct)))
            self.progress_bar.value = clamped
            self.percent_label.value = f"{int(clamped * 100)}%"
        else:
            self.progress_bar.value = None
            self.percent_label.value = ""

        if self.page:
            try:
                self.dialog.update()
            except Exception:
                try:
                    self.page.update()
                except Exception:
                    pass

    def close(self):
        if self.page:
            try:
                self.page.close(self.dialog)
            except Exception:
                self.dialog.open = False
                try:
                    self.page.update()
                except Exception:
                    pass
