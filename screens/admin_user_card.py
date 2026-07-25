import flet as ft

from utils.utils import (
    CARD_BG_COLOR,
    PRIMARY_BLUE,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_TERTIARY,
    TEXT_WHITE,
    BORDER_COLOR,
    SECTION_BG_COLOR,
    SUCCESS,
)

# ── Color Palette ──────────────────────────────────────────────────
ADMIN_GRADIENT = ft.LinearGradient(
    begin=ft.alignment.top_left,
    end=ft.alignment.bottom_right,
    colors=["#A855F7", "#7E22CE"],
)
ADMIN_SOLID = "#7E22CE"
ADMIN_BADGE_BG = "#F3E8FF"
ADMIN_BADGE_TEXT = "#9333EA"

EVALUATOR_SOLID = "#1D4ED8"
EVALUATOR_BADGE_BG = "#DBEAFE"
EVALUATOR_BADGE_TEXT = "#2563EB"

INACTIVE_SOLID = "#6B7280"
INACTIVE_BADGE_BG = "#F3F4F6"
INACTIVE_BADGE_TEXT = "#6B7280"


def _format_created_at(created_at):
    if not created_at:
        return "N/A"
    try:
        from datetime import datetime

        if isinstance(created_at, str):
            return datetime.fromisoformat(created_at.replace("Z", "+00:00")).strftime("%Y-%m-%d")
        return str(created_at)[:10]
    except Exception:
        return str(created_at)[:10]


def _make_stat_box(label, value):
    return ft.Container(
        content=ft.Column(
            [
                ft.Text(label, size=11, color="#94A3B8"),
                ft.Text(
                    str(value),
                    size=15 if isinstance(value, str) and len(str(value)) > 12 else 17,
                    weight=ft.FontWeight.BOLD,
                    color=TEXT_PRIMARY,
                    text_align=ft.TextAlign.CENTER,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
            ],
            spacing=4,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor="#F8FAFC",
        border=ft.border.all(1, "#F1F5F9"),
        border_radius=16,
        padding=ft.padding.symmetric(vertical=14, horizontal=8),
        alignment=ft.alignment.center,
        expand=True,
    )


def build_user_card(page: ft.Page, user: dict, on_toggle_status):
    name = user.get("name") or "Unknown"
    email = user.get("email") or ""
    role = (user.get("role") or "evaluator").lower()
    department = user.get("department", "N/A")
    created_at = _format_created_at(user.get("created_at", ""))
    is_active = user.get("is_active", True)
    avatar_url = (
        user.get("avatar_url")
        or user.get("display_avatar_url")
        or user.get("profile_image")
        or user.get("picture_url")
        or ""
    )
    if not isinstance(avatar_url, str):
        avatar_url = ""
    avatar_url = avatar_url.strip()

    initials = "".join([word[0].upper() for word in name.split() if word])[:2] or "U"

    # Header and Avatar Theme Setup
    if not is_active:
        header_gradient = None
        header_bg = INACTIVE_SOLID
        avatar_bg = INACTIVE_SOLID
    elif role == "admin":
        header_gradient = ADMIN_GRADIENT
        header_bg = ADMIN_SOLID
        avatar_bg = ADMIN_SOLID
    else:
        header_gradient = None
        header_bg = EVALUATOR_SOLID
        avatar_bg = EVALUATOR_SOLID

    # Avatar Component
    avatar_fallback = ft.Container(
        content=ft.Text(initials, size=20, weight=ft.FontWeight.BOLD, color=TEXT_WHITE),
        width=64,
        height=64,
        border_radius=16,
        bgcolor=avatar_bg,
        alignment=ft.alignment.center,
    )

    if avatar_url:
        avatar = ft.Container(
            content=ft.Image(
                src=avatar_url,
                fit=ft.ImageFit.COVER,
                border_radius=16,
                error_content=avatar_fallback,
                width=64,
                height=64,
            ),
            width=64,
            height=64,
            border_radius=18,
            border=ft.border.all(4, "#FFFFFF"),
            bgcolor=avatar_bg,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            ink=True,
        )
    else:
        avatar = ft.Container(
            content=avatar_fallback,
            width=64,
            height=64,
            border_radius=18,
            border=ft.border.all(4, "#FFFFFF"),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            ink=True,
        )

    def open_avatar_preview(e):
        if not avatar_url:
            return

        preview_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(name, color=TEXT_PRIMARY),
            content=ft.Container(
                content=ft.Image(
                    src=avatar_url,
                    fit=ft.ImageFit.CONTAIN,
                    width=420,
                    height=420,
                    border_radius=18,
                    error_content=ft.Container(
                        content=ft.Text(initials, size=56, weight=ft.FontWeight.BOLD, color=TEXT_WHITE),
                        width=220,
                        height=220,
                        border_radius=24,
                        bgcolor=avatar_bg,
                        alignment=ft.alignment.center,
                    ),
                ),
                width=440,
                height=440,
                alignment=ft.alignment.center,
            ),
            actions=[ft.TextButton("Close", on_click=lambda ev: page.close(preview_dialog))],
        )
        page.open(preview_dialog)

    avatar.on_click = open_avatar_preview

    # Mint Green Capsule Status Badge (Top Right)
    badge_bg = "#DCFCE7" if is_active else "#F3F4F6"
    dot_color = "#16A34A" if is_active else "#6B7280"
    text_color = "#15803D" if is_active else "#374151"

    status_badge = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    width=6,
                    height=6,
                    border_radius=3,
                    bgcolor=dot_color,
                ),
                ft.Text(
                    "Active" if is_active else "Inactive",
                    size=11,
                    weight=ft.FontWeight.W_600,
                    color=text_color,
                ),
            ],
            tight=True,
            spacing=5,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=badge_bg,
        padding=ft.padding.symmetric(horizontal=10, vertical=3),
        border_radius=999,
    )

    header = ft.Container(
        content=ft.Row([ft.Container(expand=True), status_badge], alignment=ft.MainAxisAlignment.END),
        height=100,
        gradient=header_gradient,
        bgcolor=header_bg if not header_gradient else None,
        padding=ft.padding.only(left=16, right=16, top=14, bottom=16),
        border_radius=ft.border_radius.only(top_left=16, top_right=16),
    )

    header_stack = ft.Stack(
        [
            header,
            ft.Container(content=avatar, top=52, left=20),
        ],
        height=124,
    )

    # Role Badge
    if role == "admin":
        badge_bg_role = ADMIN_BADGE_BG
        badge_text_role = ADMIN_BADGE_TEXT
        badge_label = "Admin"
    else:
        badge_bg_role = EVALUATOR_BADGE_BG
        badge_text_role = EVALUATOR_BADGE_TEXT
        badge_label = "Evaluator"

    role_badge = ft.Container(
        content=ft.Text(
            badge_label,
            size=12,
            weight=ft.FontWeight.W_600,
            color=badge_text_role,
        ),
        bgcolor=badge_bg_role,
        padding=ft.padding.symmetric(horizontal=10, vertical=4),
        border_radius=12,
    )

    # Status Toggle Switch
    status_switch = ft.Switch(
        value=is_active,
        active_color="#22C55E",
        scale=0.85,
    )
    status_switch.on_change = lambda e, u=user, sw=status_switch: on_toggle_status(u, e.control.value, sw)

    body = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text(name, size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                                ft.Text(email, size=12, color="#94A3B8"),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        role_badge,
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
                ft.Container(height=16),
                ft.Row(
                    [
                        _make_stat_box("Evaluations", user.get("evaluations_count", 0)),
                        ft.Container(width=10),
                        _make_stat_box("Subject", department),
                    ]
                ),
                ft.Container(height=16),
                ft.Divider(height=1, color="#F1F5F9"),
                ft.Container(height=8),
                ft.Row(
                    [
                        ft.Text(f"Joined {created_at}", size=12, color="#94A3B8"),
                        ft.Container(expand=True),
                        ft.Text(
                            "Enabled" if is_active else "Disabled",
                            size=12,
                            weight=ft.FontWeight.W_600,
                            color="#22C55E" if is_active else "#94A3B8",
                        ),
                        ft.Container(width=4),
                        status_switch,
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=0,
        ),
        padding=ft.padding.only(left=20, right=20, top=16, bottom=16),
    )

    return ft.Container(
        content=ft.Column([header_stack, body], spacing=0),
        width=380,
        bgcolor=CARD_BG_COLOR,
        border_radius=20,
        border=ft.border.all(1, "#E5EAF1"),
        shadow=ft.BoxShadow(
            blur_radius=12,
            color="#0000000A",
            offset=ft.Offset(0, 4),
            spread_radius=0,
        ),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
    )


def build_user_cards(page: ft.Page, users: list[dict], on_toggle_status):
    cards = []
    for user in users:
        try:
            cards.append(build_user_card(page, user, on_toggle_status))
        except Exception as ex:
            print(f"Error building admin card for {user.get('email', 'unknown')}: {ex}")
    return cards


def build_user_management_header(
    total_count: int = 4,
    active_count: int = 3,
    inactive_count: int = 1,
    selected_filter: str = "all",
    on_search=None,
    on_filter_change=None,
    on_add_user=None,
):
    search_bar = ft.TextField(
        hint_text="Search by name, email or subject...",
        hint_style=ft.TextStyle(color="#94A3B8", size=13),
        prefix_icon=ft.Icons.SEARCH,
        height=42,
        content_padding=ft.padding.symmetric(horizontal=12, vertical=8),
        border_radius=10,
        border_color="#E2E8F0",
        bgcolor="#FFFFFF",
        cursor_color="#2563EB",
        text_size=13,
        expand=True,
        on_change=on_search,
    )

    def make_filter_tab(label: str, count: int, key: str):
        is_selected = selected_filter == key
        return ft.Container(
            content=ft.Text(
                f"{label} ({count})",
                size=12,
                weight=ft.FontWeight.W_600 if is_selected else ft.FontWeight.W_500,
                color="#FFFFFF" if is_selected else "#64748B",
            ),
            bgcolor="#2563EB" if is_selected else ft.Colors.TRANSPARENT,
            padding=ft.padding.symmetric(horizontal=14, vertical=8),
            border_radius=20,
            ink=True,
            on_click=lambda _: on_filter_change(key) if on_filter_change else None,
        )

    add_user_btn = ft.ElevatedButton(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.ADD, size=16, color="#FFFFFF"),
                ft.Text("Add User", size=13, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
            ],
            tight=True,
            spacing=4,
        ),
        style=ft.ButtonStyle(
            bgcolor="#2563EB",
            elevation=0,
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
        ),
        on_click=on_add_user,
    )

    return ft.Row(
        [
            ft.Container(content=search_bar, width=380),
            ft.Row(
                [
                    make_filter_tab("All", total_count, "all"),
                    make_filter_tab("Active", active_count, "active"),
                    make_filter_tab("Inactive", inactive_count, "inactive"),
                ],
                spacing=4,
            ),
            ft.Container(expand=True),
            add_user_btn,
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


def build_user_management_view(page: ft.Page, users: list[dict], on_toggle_status, on_add_user):
    total_count = len(users)
    active_count = sum(1 for u in users if u.get("is_active", True))
    inactive_count = total_count - active_count

    header_bar = build_user_management_header(
        total_count=total_count,
        active_count=active_count,
        inactive_count=inactive_count,
        selected_filter="all",
        on_add_user=on_add_user,
    )

    user_cards = build_user_cards(page, users, on_toggle_status)

    cards_grid = ft.Row(
        controls=user_cards,
        wrap=True,
        spacing=20,
        run_spacing=20,
    )

    return ft.Container(
        content=ft.Column(
            [
                header_bar,
                ft.Container(height=12),
                cards_grid,
            ],
            spacing=12,
        ),
        padding=24,
        bgcolor="#F8FAFC",
        expand=True,
    )