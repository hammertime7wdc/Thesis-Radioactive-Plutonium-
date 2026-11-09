"""QualCheck login screen: split layout (hero panel + auth forms)."""

import asyncio
import json
import os
import sys
import threading
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import flet as ft

from services.google_oauth import sign_in_with_google
from services.login_lockout import (
    MAX_LOGIN_ATTEMPTS,
    format_lockout_message,  # noqa: F401  (re-exported for other screens)
    get_lockout_remaining_seconds,
    record_failed_login,
    reset_login_attempts,
)
from services.supabase_client import get_supabase_client
from utils.utils import (
    BG_COLOR,
    BORDER_COLOR,
    BUTTON_PRIMARY_BG,
    BUTTON_PRIMARY_TEXT,
    CARD_BG_COLOR,
    ERROR,
    INPUT_BG,
    INPUT_BORDER,
    INPUT_HINT,
    INPUT_TEXT,
    PRIMARY_BLUE,
    SUCCESS,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_TERTIARY,
)
from widgets.snackbar import show_snackbar

try:
    from screens.password_reset import main as reset_password_main
except ModuleNotFoundError:

    def reset_password_main(page, nav=None):
        page.clean()
        page.add(ft.Text("Reset password screen is unavailable."))


# ─────────────────────────────────────────────────────────────────────────────
# Design tokens
# ─────────────────────────────────────────────────────────────────────────────

FORM_WIDTH = 400
FIELD_HEIGHT = 46
RADIUS = 8
HERO_GRADIENT_END = "#4A2FD6"
DRIFT_SECONDS = 5
GOOGLE_LOGO_URL = "assets/google.png"
LOGIN_TITLE = "QualCheck Login"

SESSION_FILE = os.path.join(os.path.dirname(__file__), "..", ".session.json")
NON_CREDENTIAL_ERRORS = ("rate limit", "too many requests", "network", "timeout", "connection")


def white(opacity: float) -> str:
    return ft.Colors.with_opacity(opacity, ft.Colors.WHITE)


def _ensure_event_loop() -> None:
    """Worker threads have no asyncio loop by default; supabase needs one."""
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())


# ─────────────────────────────────────────────────────────────────────────────
# Shared form components (also imported by the other auth screens)
# ─────────────────────────────────────────────────────────────────────────────

def field_label(text: str) -> ft.Text:
    return ft.Text(text, size=13, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY)


def text_field(hint="", password=False, reveal=False, read_only=False, value="") -> ft.TextField:
    return ft.TextField(
        hint_text=hint,
        password=password,
        can_reveal_password=reveal,
        read_only=read_only,
        value=value,
        width=FORM_WIDTH,
        height=FIELD_HEIGHT,
        bgcolor=INPUT_BG,
        border_color=INPUT_BORDER,
        focused_border_color=PRIMARY_BLUE,
        border_radius=RADIUS,
        text_size=14,
        color=INPUT_TEXT,
        hint_style=ft.TextStyle(color=INPUT_HINT, size=13.5),
        content_padding=ft.padding.symmetric(horizontal=14, vertical=10),
    )


def google_button(label: str) -> ft.Container:
    return ft.Container(
        content=_google_row(label),
        width=FORM_WIDTH,
        height=FIELD_HEIGHT,
        bgcolor=CARD_BG_COLOR,
        border=ft.border.all(1, BORDER_COLOR),
        border_radius=RADIUS,
        alignment=ft.alignment.center,
        ink=True,
    )


def _google_row(label: str, loading: bool = False) -> ft.Row:
    lead = (
        ft.ProgressRing(width=16, height=16, stroke_width=2, color=TEXT_PRIMARY)
        if loading
        else ft.Image(src=GOOGLE_LOGO_URL, width=18, height=18)
    )
    return ft.Row(
        [lead, ft.Text(label, size=14, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY)],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=10,
    )


def or_divider(label: str = "or") -> ft.Row:
    def line():
        return ft.Container(height=1, bgcolor=BORDER_COLOR, expand=True)

    return ft.Row(
        [line(), ft.Text(label, size=11.5, weight=ft.FontWeight.W_500, color=TEXT_TERTIARY), line()],
        spacing=12,
        width=FORM_WIDTH,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


def _button_content(label: str, color: str, lead: ft.Control | None = None) -> ft.Row:
    controls = [lead] if lead else []
    controls.append(ft.Text(label, size=14, weight=ft.FontWeight.BOLD, color=color))
    return ft.Row(controls, alignment=ft.MainAxisAlignment.CENTER, spacing=8)


# ─────────────────────────────────────────────────────────────────────────────
# Left hero panel
# ─────────────────────────────────────────────────────────────────────────────

def _decor_circle(size: int, left: int, top: int, *, ring: bool = False) -> ft.Container:
    glide = ft.Animation(DRIFT_SECONDS * 1000, ft.AnimationCurve.EASE_IN_OUT)
    return ft.Container(
        width=size,
        height=size,
        left=left,
        top=top,
        scale=1,
        border_radius=size / 2,
        bgcolor=None if ring else white(0.07),
        border=ft.border.all(1, white(0.16)) if ring else None,
        animate_position=glide,
        animate_scale=glide,
    )


def _start_drift(page: ft.Page, motions: list) -> None:
    """Slowly float circles back and forth.

    motions: [(circle, (left, top), (dx, dy), scale), ...]
    A fresh token per call stops any loop left over from a previous build.
    """
    token = object()
    page.data["drift_token"] = token

    def run():
        time.sleep(0.6)  # let the first frame render
        far = False
        while page.data.get("auth_active") and page.data.get("drift_token") is token:
            far = not far
            for circle, (left, top), (dx, dy), scale in motions:
                circle.left = left + dx if far else left
                circle.top = top + dy if far else top
                circle.scale = scale if far else 1
            try:
                page.update()
            except Exception:
                break
            time.sleep(DRIFT_SECONDS)

    threading.Thread(target=run, daemon=True).start()


def _brand() -> ft.Row:
    logo = ft.Container(
        content=ft.Text("Q", size=18, weight=ft.FontWeight.BOLD, color=PRIMARY_BLUE),
        width=44,
        height=44,
        bgcolor=ft.Colors.WHITE,
        border_radius=12,
        alignment=ft.alignment.center,
        shadow=ft.BoxShadow(blur_radius=18, color=ft.Colors.with_opacity(0.18, ft.Colors.BLACK), offset=ft.Offset(0, 6)),
    )
    names = ft.Column(
        [
            ft.Text("QualCheck", size=17, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ft.Text("Rubric-guided semantic evaluation", size=11.5, color=white(0.8)),
        ],
        spacing=0,
    )
    return ft.Row([logo, names], spacing=12)


def _badge(text: str) -> ft.Container:
    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.VERIFIED_USER_OUTLINED, size=14, color=ft.Colors.WHITE),
                ft.Text(text, size=11.5, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
            ],
            spacing=8,
            tight=True,
        ),
        padding=ft.padding.symmetric(horizontal=12, vertical=7),
        border=ft.border.all(1, white(0.32)),
        bgcolor=white(0.10),
        border_radius=20,
    )


def _step_card(icon: str, label: str) -> ft.Container:
    return ft.Container(
        content=ft.Column(
            [
                ft.Icon(icon, size=18, color=ft.Colors.WHITE),
                ft.Text(label, size=12.5, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
            ],
            spacing=14,
        ),
        expand=True,
        padding=ft.padding.all(16),
        bgcolor=white(0.12),
        border=ft.border.all(1, white(0.20)),
        border_radius=14,
    )


def _steps_row() -> ft.Row:
    arrow = lambda: ft.Icon(ft.Icons.ARROW_FORWARD_ROUNDED, size=14, color=white(0.7))  # noqa: E731
    return ft.Row(
        [
            _step_card(ft.Icons.UPLOAD_FILE_OUTLINED, "Upload PDFs"),
            arrow(),
            _step_card(ft.Icons.CHECKLIST_ROUNDED, "Apply rubric"),
            arrow(),
            _step_card(ft.Icons.BAR_CHART_ROUNDED, "Review results"),
        ],
        spacing=8,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


def _check_item(text: str) -> ft.Row:
    return ft.Row(
        [
            ft.Icon(ft.Icons.CHECK_ROUNDED, size=15, color=white(0.9)),
            ft.Text(text, size=12.5, color=white(0.9)),
        ],
        spacing=10,
    )


def _feature_grid() -> ft.Row:
    left = ["Batch PDF evaluation", "Per-student results"]
    right = ["Type-specific criteria", "BERT semantic scoring"]
    return ft.Row(
        [
            ft.Column([_check_item(t) for t in left], spacing=12, expand=True),
            ft.Column([_check_item(t) for t in right], spacing=12, expand=True),
        ],
        vertical_alignment=ft.CrossAxisAlignment.START,
    )


def build_left_panel(page: ft.Page | None = None) -> ft.Container:
    caption = ft.Text(
        "Thesis research project · NLP-based academic assessment system",
        size=11.5,
        color=white(0.65),
    )

    big_circle = _decor_circle(380, left=-130, top=-120)
    ring_circle = _decor_circle(520, left=380, top=330, ring=True)
    if page is not None:
        _start_drift(
            page,
            [
                (big_circle, (-130, -120), (90, 70), 1.12),
                (ring_circle, (380, 330), (-70, -60), 0.92),
            ],
        )

    content = ft.Column(
        [
            _brand(),
            ft.Container(expand=True),
            _badge("Research-backed academic assessment"),
            ft.Container(height=76),
            _steps_row(),
            ft.Container(height=28),
            _feature_grid(),
            ft.Container(expand=True),
            caption,
        ],
        spacing=0,
        expand=True,
        horizontal_alignment=ft.CrossAxisAlignment.START,
    )

    return ft.Container(
        content=ft.Stack(
            [
                big_circle,
                ring_circle,
                ft.Container(
                    content=content,
                    padding=ft.padding.only(left=60, top=52, right=56, bottom=40),
                    expand=True,
                ),
            ],
            expand=True,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        ),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=[PRIMARY_BLUE, HERO_GRADIENT_END],
        ),
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        expand=6,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Sign-in form
# ─────────────────────────────────────────────────────────────────────────────

def build_sign_in_container(page: ft.Page, nav=None, on_go_to_create_account=None, on_forgot_password_cb=None):
    controller = lambda: page.data.get("auth_controller") if page.data and page.data.get("auth_active") else None  # noqa: E731

    def go_to_create_account(e=None):
        if on_go_to_create_account:
            return on_go_to_create_account(e)
        if ctrl := controller():
            threading.Thread(target=ctrl["switch_to_create_account"], daemon=True).start()
        else:
            from screens.ui_create_account import main as create_account_main

            threading.Thread(target=lambda: create_account_main(page, nav), daemon=True).start()

    def go_to_forgot_password(e=None):
        if on_forgot_password_cb:
            return on_forgot_password_cb(e)
        if ctrl := controller():
            threading.Thread(target=ctrl["switch_to_reset_password"], daemon=True).start()
        else:
            reset_password_main(page, nav)

    # ── controls ────────────────────────────────────────────────────────────
    email_input = text_field(hint="you@university.edu")
    password_input = text_field(hint="Enter your password", password=True, reveal=True)
    error_text = ft.Text("", size=12, color=ERROR, visible=False)
    timer_text = ft.Text("00:00", size=15, weight=ft.FontWeight.BOLD, color=ERROR, font_family="monospace")

    lockout_card = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Icon(ft.Icons.LOCK_CLOCK_OUTLINED, color=ERROR, size=20),
                    padding=8,
                    bgcolor="#fee2e2",
                    border_radius=RADIUS,
                ),
                ft.Column(
                    [
                        ft.Row(
                            [ft.Text("Account locked", size=13, weight=ft.FontWeight.BOLD, color="#b91c1c"), timer_text],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            width=300,
                        ),
                        ft.Text("Too many failed attempts. Please wait.", size=11, color=TEXT_SECONDARY),
                    ],
                    spacing=2,
                    expand=True,
                ),
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        width=FORM_WIDTH,
        bgcolor="#fef2f2",
        border=ft.border.all(1, "#fecaca"),
        border_radius=RADIUS,
        padding=ft.padding.symmetric(horizontal=12, vertical=10),
        visible=False,
    )

    sign_in_btn = ft.Container(
        width=FORM_WIDTH,
        height=48,
        bgcolor=BUTTON_PRIMARY_BG,
        border_radius=RADIUS,
        alignment=ft.alignment.center,
        ink=True,
    )

    button_states = {
        "idle": lambda: _button_content("Sign in", BUTTON_PRIMARY_TEXT),
        "loading": lambda: _button_content(
            "Signing in...",
            BUTTON_PRIMARY_TEXT,
            ft.ProgressRing(width=16, height=16, stroke_width=2, color=BUTTON_PRIMARY_TEXT),
        ),
        "locked": lambda: _button_content(
            "Sign in disabled", TEXT_TERTIARY, ft.Icon(ft.Icons.LOCK_OUTLINED, size=16, color=TEXT_TERTIARY)
        ),
    }

    def set_button_state(state: str):
        sign_in_btn.disabled = state != "idle"
        sign_in_btn.bgcolor = BORDER_COLOR if state == "locked" else BUTTON_PRIMARY_BG
        sign_in_btn.content = button_states[state]()

    def show_message(message: str, color: str = ERROR):
        error_text.value = message
        error_text.color = color
        error_text.visible = True
        page.update()

    set_button_state("idle")

    # ── lockout countdown ───────────────────────────────────────────────────
    lockout_active = {"value": False}

    def start_lockout_countdown(seconds: int):
        if lockout_active["value"]:
            return
        lockout_active["value"] = True

        def run():
            remaining = seconds
            error_text.visible = False
            lockout_card.visible = True
            set_button_state("locked")

            while remaining > 0 and page.title == LOGIN_TITLE:
                timer_text.value = "{:02d}:{:02d}".format(*divmod(remaining, 60))
                page.update()
                time.sleep(1)
                remaining -= 1

            if page.title == LOGIN_TITLE:
                lockout_card.visible = False
                set_button_state("idle")
                show_message("Lockout period ended. You may try logging in again.", SUCCESS)
            lockout_active["value"] = False

        threading.Thread(target=run, daemon=True).start()

    # ── post-authentication ─────────────────────────────────────────────────
    def finish_login(supabase, auth_response, reset_button, email_hint=None):
        def reject(message: str):
            try:
                supabase.auth.sign_out()
            except Exception:
                pass
            reset_button()
            show_message(message)

        session = auth_response.session
        supabase.auth.set_session(access_token=session.access_token, refresh_token=session.refresh_token)

        rows = supabase.table("profiles").select("role, is_active").eq("id", auth_response.user.id).execute().data
        profile = rows[0] if rows else None
        if not profile:
            return reject("This Google account is not registered in QualCheck. Please contact an administrator.")
        if not profile.get("is_active", True):
            return reject("Your account has been disabled. Please contact an administrator.")

        role = profile.get("role", "evaluator")
        routes = {"admin": nav.navigate_to_admin, "evaluator": nav.navigate_to_short_answer} if nav else {}
        route = routes.get(role)
        if route is None:
            return reject("Invalid user role.")

        with open(SESSION_FILE, "w") as f:
            json.dump(
                {
                    "access_token": session.access_token,
                    "refresh_token": session.refresh_token,
                    "user_id": auth_response.user.id,
                },
                f,
            )
        if email_hint:
            reset_login_attempts(email_hint)
        if page.data:
            page.data["auth_active"] = False

        def fade_and_navigate():
            for control in page.controls:
                control.opacity = 0
            page.update()
            time.sleep(0.2)
            route()
            show_snackbar(page, "Signed in successfully.")

        threading.Thread(target=fade_and_navigate, daemon=True).start()

    # ── email / password login ──────────────────────────────────────────────
    def attempt_password_login(email: str):
        _ensure_event_loop()

        remaining_lockout = get_lockout_remaining_seconds(email)
        if remaining_lockout > 0:
            return start_lockout_countdown(int(remaining_lockout))

        supabase = get_supabase_client()
        try:
            auth_response = supabase.auth.sign_in_with_password({"email": email, "password": password_input.value})
        except Exception as auth_error:
            if any(marker in str(auth_error).lower() for marker in NON_CREDENTIAL_ERRORS):
                raise
            attempts_used, is_locked, lockout_seconds = record_failed_login(email)
            if is_locked:
                return start_lockout_countdown(int(lockout_seconds))
            left = MAX_LOGIN_ATTEMPTS - attempts_used
            set_button_state("idle")
            return show_message(f"Invalid email or password. {left} attempt{'s' if left != 1 else ''} remaining.")

        finish_login(supabase, auth_response, lambda: set_button_state("idle"), email_hint=email)

    def on_login(e=None):
        if sign_in_btn.disabled or lockout_active["value"]:
            return
        if not email_input.value or not password_input.value:
            return show_message("Please enter email and password.")

        error_text.visible = False
        set_button_state("loading")
        page.update()

        def worker():
            try:
                attempt_password_login(email_input.value.strip())
            except Exception as ex:
                set_button_state("idle")
                show_message(f"Login failed: {ex}")

        threading.Thread(target=worker, daemon=True).start()

    sign_in_btn.on_click = on_login
    email_input.on_submit = on_login
    password_input.on_submit = on_login

    # ── google login ────────────────────────────────────────────────────────
    google_btn = google_button("Google")
    google_busy = {"value": False}

    def on_google_login(e=None):
        if google_busy["value"]:
            return
        google_busy["value"] = True
        error_text.visible = False
        google_btn.content = _google_row("Waiting for Google...", loading=True)
        page.update()

        def reset_google_button():
            google_btn.content = _google_row("Google")
            page.update()

        def worker():
            try:
                auth_response = sign_in_with_google()
                finish_login(get_supabase_client(), auth_response, reset_google_button)
            except Exception as ex:
                reset_google_button()
                show_message(f"Google sign-in failed: {ex}")
            finally:
                google_busy["value"] = False

        threading.Thread(target=worker, daemon=True).start()

    google_btn.on_click = on_google_login

    # ── layout ──────────────────────────────────────────────────────────────
    def gap(height: int) -> ft.Container:
        return ft.Container(height=height)

    link_style = ft.ButtonStyle(color=PRIMARY_BLUE, padding=ft.padding.all(0))

    form = ft.Column(
        [
            ft.Text("Welcome back", size=30, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ft.Text("Sign in to continue evaluating academic responses.", size=13, color=TEXT_SECONDARY),
            gap(26),
            field_label("Email address"),
            gap(8),
            email_input,
            gap(18),
            ft.Row(
                [
                    field_label("Password"),
                    ft.TextButton("Forgot password?", style=link_style, on_click=go_to_forgot_password),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                width=FORM_WIDTH,
            ),
            gap(8),
            password_input,
            gap(10),
            error_text,
            lockout_card,
            gap(14),
            sign_in_btn,
            gap(24),
            or_divider("or continue with"),
            gap(24),
            google_btn,
            gap(28),
            ft.Container(height=1, bgcolor=BORDER_COLOR, width=FORM_WIDTH),
            gap(16),
            ft.Text(
                "Student submissions are available only to authorized evaluators.",
                size=11.5,
                color=TEXT_TERTIARY,
                width=FORM_WIDTH,
                text_align=ft.TextAlign.CENTER,
            ),
        ],
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.START,
    )
    return ft.Container(content=form), email_input


# ─────────────────────────────────────────────────────────────────────────────
# Screen composition
# ─────────────────────────────────────────────────────────────────────────────

def _configure_window(page: ft.Page):
    page.title = LOGIN_TITLE
    page.window_width = 1180
    page.window_height = 760
    page.window_min_width = 960
    page.window_min_height = 640
    page.window_resizable = True
    page.padding = 0
    page.bgcolor = BG_COLOR
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = None
    page.appbar = None


def main(page: ft.Page, nav=None):
    if page.data is None:
        page.data = {}

    # Fast path: only valid while this screen's controls are still mounted.
    # If something called page.clean() (e.g. Navigation.logout()) the old
    # switch_to_login closure would touch detached controls → blank screen,
    # so in that case we fall through to a full rebuild.
    if page.data.get("auth_active") and "auth_controller" in page.data and page.controls:
        page.data["auth_controller"]["switch_to_login"]()
        return

    _configure_window(page)
    page.clean()
    page.data["auth_active"] = True

    # ── tab bar ─────────────────────────────────────────────────────────────
    tabs: dict[str, ft.Container] = {}

    def make_tab(key: str, label: str, on_click) -> ft.Container:
        tabs[key] = ft.Container(
            content=ft.Text(label, size=13),
            padding=ft.padding.only(left=2, right=2, bottom=10),
            on_click=on_click,
        )
        return tabs[key]

    def style_tabs(active: str):
        for key, tab in tabs.items():
            is_active = key == active
            tab.border = ft.border.only(bottom=ft.BorderSide(2, PRIMARY_BLUE if is_active else "transparent"))
            tab.content.color = TEXT_PRIMARY if is_active else TEXT_TERTIARY
            tab.content.weight = ft.FontWeight.BOLD if is_active else ft.FontWeight.W_500

    def threaded(fn):
        return lambda *_: threading.Thread(target=fn, daemon=True).start()

    tab_bar = ft.Column(
        [
            ft.Row(
                [
                    make_tab("signin", "Sign in", threaded(lambda: switch_to_login())),
                    make_tab("create", "Create account", threaded(lambda: switch_to_create_account())),
                ],
                spacing=28,
            ),
            ft.Container(height=1, bgcolor=BORDER_COLOR, width=FORM_WIDTH),
            ft.Container(height=30),
        ],
        spacing=0,
    )
    style_tabs("signin")

    # ── view switching ──────────────────────────────────────────────────────
    def go_to_sign_in(e=None, prefill_email=None):
        if page.data.get("auth_active") and "auth_controller" in page.data:
            threading.Thread(target=lambda: switch_to_login(prefill_email), daemon=True).start()

    def go_to_create_account(e=None):
        if page.data.get("auth_active") and "auth_controller" in page.data:
            threading.Thread(target=switch_to_create_account, daemon=True).start()
        else:
            from screens.ui_create_account import main as create_account_main

            threading.Thread(target=lambda: create_account_main(page, nav), daemon=True).start()

    def go_to_forgot_password(e=None):
        if page.data.get("auth_active") and "auth_controller" in page.data:
            threading.Thread(target=switch_to_reset_password, daemon=True).start()
        else:
            reset_password_main(page, nav)

    sign_in_view, email_ref = build_sign_in_container(page, nav, go_to_create_account, go_to_forgot_password)
    views = {"signin": sign_in_view}
    switching = {"active": False}

    form_wrapper = ft.Container(
        content=sign_in_view,
        opacity=1,
        animate_opacity=ft.Animation(180, ft.AnimationCurve.EASE_IN_OUT),
    )

    def swap_view(view_key: str, title: str, active_tab: str | None, factory=None):
        if switching["active"]:
            return
        switching["active"] = True
        try:
            if view_key not in views:
                views[view_key] = factory()

            form_wrapper.opacity = 0
            page.update()
            time.sleep(0.18)

            tab_bar.visible = active_tab is not None
            if active_tab:
                style_tabs(active_tab)
            page.title = title
            form_wrapper.content = views[view_key]
            form_wrapper.opacity = 1
            page.update()
        finally:
            switching["active"] = False

    def switch_to_login(prefill_email=None):
        if prefill_email:
            email_ref.value = prefill_email
        swap_view("signin", LOGIN_TITLE, "signin")

    def switch_to_create_account():
        def factory():
            from screens.ui_create_account import build_create_account_container

            container, _ = build_create_account_container(page, nav, go_to_sign_in)
            return container

        swap_view("create", "QualCheck Create Account", "create", factory)

    def switch_to_reset_password():
        def factory():
            from screens.password_reset import build_reset_password_container

            return build_reset_password_container(page, nav, go_to_sign_in)

        swap_view("reset", "QualCheck - Reset Password", None, factory)

    page.data["auth_controller"] = {
        "switch_to_login": switch_to_login,
        "switch_to_create_account": switch_to_create_account,
        "switch_to_reset_password": switch_to_reset_password,
    }

    # ── assemble ────────────────────────────────────────────────────────────
    right_panel = ft.Container(
        content=ft.Column(
            [ft.Column([tab_bar, form_wrapper], spacing=0, width=FORM_WIDTH)],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
        bgcolor=BG_COLOR,
        padding=ft.padding.symmetric(horizontal=48, vertical=40),
        alignment=ft.alignment.center,
        expand=5,
    )

    page_fade = ft.Container(
        content=ft.Row(
            [build_left_panel(page), right_panel],
            spacing=0,
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
        ),
        expand=True,
        opacity=0,
        animate_opacity=ft.Animation(260, ft.AnimationCurve.EASE_OUT),
    )
    page.add(page_fade)
    page.update()
    time.sleep(0.03)
    page_fade.opacity = 1
    page.update()


if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")