import sys
import os
import json
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import math
import time
import threading
import flet as ft
from services.supabase_client import get_supabase_client
from services.login_lockout import (
    MAX_LOGIN_ATTEMPTS,
    get_lockout_remaining_seconds,
    record_failed_login,
    reset_login_attempts,
    format_lockout_message,
)
from services.google_oauth import sign_in_with_google
from utils.utils import (
    BG_COLOR,
    CARD_BG_COLOR,
    PRIMARY_BLUE,
    PRIMARY_BLUE_DARK,
    PRIMARY_BLUE_LIGHT,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_TERTIARY,
    TEXT_WHITE,
    BORDER_COLOR,
    INPUT_BG,
    INPUT_BORDER,
    INPUT_TEXT,
    INPUT_HINT,
    BUTTON_PRIMARY_BG,
    BUTTON_PRIMARY_TEXT,
    ERROR,
    SUCCESS,
)

try:
    from screens.password_reset import main as reset_password_main
except ModuleNotFoundError:

    def reset_password_main(page, nav=None):
        page.clean()
        page.add(ft.Text("Reset password screen is unavailable."))


GOOGLE_LOGO_URL = "assets/google.png"


def google_button(label):
    return ft.Container(
        content=ft.Row(
            [
                ft.Image(src=GOOGLE_LOGO_URL, width=18, height=18),
                ft.Text(label, size=14, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
        ),
        bgcolor=CARD_BG_COLOR,
        border_radius=8,
        height=46,
        width=400,
        alignment=ft.alignment.center,
        border=ft.border.all(1, BORDER_COLOR),
        ink=True,
    )


def or_divider():
    line = ft.Container(height=1, bgcolor=BORDER_COLOR, expand=True)
    return ft.Row(
        [line, ft.Text("or", size=12, color=TEXT_TERTIARY), line],
        spacing=12,
        width=400,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


def text_field(hint="", password=False, reveal=False, read_only=False, value=""):
    return ft.TextField(
        hint_text=hint,
        password=password,
        can_reveal_password=reveal,
        read_only=read_only,
        value=value,
        width=400,
        height=46,
        bgcolor=INPUT_BG,
        border_color=INPUT_BORDER,
        focused_border_color=PRIMARY_BLUE,
        text_size=14,
        content_padding=ft.padding.symmetric(horizontal=14, vertical=10),
        hint_style=ft.TextStyle(color=INPUT_HINT),
        color=INPUT_TEXT,
        border_radius=8,
    )


# ---------------------------------------------------------------------------
# LEFT HERO PANEL — solid blue gradient, large soft overlapping circles,
# gentle breathing animation, headline + subtitle + topic pills.
# ---------------------------------------------------------------------------

def build_left_panel(page: ft.Page):
    circle_a = ft.Container(
        width=340,
        height=340,
        border_radius=170,
        bgcolor=ft.Colors.with_opacity(0.10, ft.Colors.WHITE),
        left=-90,
        top=-70,
        animate=ft.Animation(2200, ft.AnimationCurve.EASE_IN_OUT),
    )
    circle_b = ft.Container(
        width=460,
        height=460,
        border_radius=230,
        bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
        left=90,
        top=190,
        animate=ft.Animation(2600, ft.AnimationCurve.EASE_IN_OUT),
    )
    circle_c = ft.Container(
        width=260,
        height=260,
        border_radius=130,
        bgcolor=ft.Colors.with_opacity(0.10, ft.Colors.WHITE),
        left=210,
        top=560,
        animate=ft.Animation(2400, ft.AnimationCurve.EASE_IN_OUT),
    )

    def breathe():
        grown = False
        while page.data.get("auth_active", False):
            try:
                time.sleep(2.4)
                grown = not grown
                delta = 14 if grown else 0
                circle_a.width, circle_a.height = 340 + delta, 340 + delta
                circle_a.border_radius = (340 + delta) / 2
                circle_b.width, circle_b.height = 460 + (delta * 0.8), 460 + (delta * 0.8)
                circle_b.border_radius = (460 + delta * 0.8) / 2
                circle_c.width, circle_c.height = 260 + (delta * 1.2), 260 + (delta * 1.2)
                circle_c.border_radius = (260 + delta * 1.2) / 2
                page.update()
            except Exception:
                break

    threading.Thread(target=breathe, daemon=True).start()

    logo = ft.Container(
        content=ft.Text("Q", size=18, weight=ft.FontWeight.BOLD, color=PRIMARY_BLUE),
        bgcolor=ft.Colors.WHITE,
        width=42,
        height=42,
        border_radius=10,
        alignment=ft.alignment.center,
    )
    brand = ft.Column(
        [
            ft.Text("QualCheck", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ft.Text("Rubric-Guided Semantic Evaluation", size=11.5, color=ft.Colors.with_opacity(0.75, ft.Colors.WHITE)),
        ],
        spacing=0,
    )
    brand_row = ft.Row([logo, brand], spacing=12)

    headline = ft.Column(
        [
            ft.Text("Intelligent evaluation", size=42, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, height=1.15),
            ft.Text("powered by NLP", size=42, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, height=1.15),
        ],
        spacing=0,
    )

    subtitle = ft.Text(
        "Assess academic responses and code reports against structured "
        "rubrics using BERT-based semantic similarity scoring.",
        size=16,
        color=ft.Colors.with_opacity(0.85, ft.Colors.WHITE),
        width=420,
    )

    def pill(text):
        return ft.Container(
            content=ft.Text(text, size=11.5, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE),
            padding=ft.padding.symmetric(horizontal=14, vertical=8),
            border_radius=20,
            bgcolor=ft.Colors.with_opacity(0.16, ft.Colors.WHITE),
        )

    pills = ft.Row(
        [pill("BERT Embeddings"), pill("Cosine Similarity"), pill("Rubric-Based"), pill("PDF Analysis")],
        spacing=10,
        wrap=True,
    )

    caption = ft.Text(
        "Thesis research project NLP-based academic assessment system",
        size=11.5,
        italic=True,
        color=ft.Colors.with_opacity(0.6, ft.Colors.WHITE),
    )

    content_col = ft.Column(
        [
            brand_row,
            ft.Container(expand=True),
            headline,
            ft.Container(height=16),
            subtitle,
            ft.Container(height=30),
            pills,
            ft.Container(expand=True),
        ],
        spacing=0,
        expand=True,
    )

    panel = ft.Container(
        content=ft.Stack(
            [
                circle_a,
                circle_b,
                circle_c,
                ft.Container(content=content_col, padding=ft.padding.only(left=60, top=52, right=40, bottom=48), expand=True),
                ft.Container(content=caption, padding=ft.padding.only(left=60, bottom=48), alignment=ft.alignment.bottom_left),
            ],
            expand=True,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        ),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=[PRIMARY_BLUE, PRIMARY_BLUE_DARK],
        ),
        expand=6,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
    )
    return panel


# ---------------------------------------------------------------------------
# RIGHT PANEL — sign-in / create-account / reset-password forms
# ---------------------------------------------------------------------------

def build_sign_in_container(page: ft.Page, nav=None, on_go_to_create_account=None, on_forgot_password_cb=None):
    def handle_go_to_create_account(e=None):
        if on_go_to_create_account:
            on_go_to_create_account(e)
        else:
            if page.data and page.data.get("auth_active") and "auth_controller" in page.data:
                threading.Thread(
                    target=page.data["auth_controller"]["switch_to_create_account"],
                    daemon=True,
                ).start()
            else:
                from screens.ui_create_account import main as create_account_main
                threading.Thread(
                    target=lambda: create_account_main(page, nav), daemon=True
                ).start()

    def handle_forgot_password(e=None):
        if on_forgot_password_cb:
            on_forgot_password_cb(e)
        elif page.data and page.data.get("auth_active") and "auth_controller" in page.data:
            threading.Thread(
                target=page.data["auth_controller"]["switch_to_reset_password"],
                daemon=True,
            ).start()
        else:
            reset_password_main(page, nav)

    lockout_timer_active = {"value": False}

    error_text = ft.Text("", size=12, color=ERROR, visible=False)

    timer_display = ft.Text(
        "00:00",
        size=15,
        weight=ft.FontWeight.BOLD,
        color=ERROR,
        font_family="monospace",
    )

    lockout_card = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Icon(ft.Icons.LOCK_CLOCK_OUTLINED, color=ERROR, size=20),
                    padding=8,
                    bgcolor="#fee2e2",
                    border_radius=8,
                ),
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text("Account Locked", size=13, weight=ft.FontWeight.BOLD, color="#b91c1c"),
                                timer_display,
                            ],
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
        bgcolor="#fef2f2",
        border=ft.border.all(1, "#fecaca"),
        border_radius=8,
        padding=ft.padding.symmetric(horizontal=12, vertical=10),
        width=400,
        visible=False,
    )

    si_email = text_field(hint="you@university.edu")
    si_password = text_field(password=True, reveal=True)
    sign_in_btn_content = ft.Row(
        [
            ft.Icon(ft.Icons.LOGIN_ROUNDED, size=16, color=BUTTON_PRIMARY_TEXT),
            ft.Text("Sign in", size=14, weight=ft.FontWeight.BOLD, color=BUTTON_PRIMARY_TEXT),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=8,
    )
    sign_in_btn = ft.Container(
        content=sign_in_btn_content,
        width=400,
        height=48,
        bgcolor=BUTTON_PRIMARY_BG,
        border_radius=8,
        alignment=ft.alignment.center,
        ink=True,
    )

    def start_lockout_countdown(remaining_seconds: int):
        if lockout_timer_active["value"]:
            return

        lockout_timer_active["value"] = True

        def countdown_thread():
            seconds_left = remaining_seconds

            error_text.visible = False
            lockout_card.visible = True

            sign_in_btn.disabled = True
            sign_in_btn.bgcolor = BORDER_COLOR
            sign_in_btn.content = ft.Row(
                [
                    ft.Icon(ft.Icons.LOCK_OUTLINED, size=16, color=TEXT_TERTIARY),
                    ft.Text("Sign in disabled", size=14, weight=ft.FontWeight.BOLD, color=TEXT_TERTIARY),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            )

            while seconds_left > 0 and page.title == "QualCheck Login":
                mins, secs = divmod(seconds_left, 60)
                timer_display.value = f"{mins:02d}:{secs:02d}"
                page.update()

                time.sleep(1)
                seconds_left -= 1

            if page.title == "QualCheck Login":
                lockout_card.visible = False
                error_text.value = "Lockout period ended. You may try logging in again."
                error_text.color = SUCCESS
                error_text.visible = True

                sign_in_btn.disabled = False
                sign_in_btn.bgcolor = BUTTON_PRIMARY_BG
                sign_in_btn.content = sign_in_btn_content
                page.update()

            lockout_timer_active["value"] = False

        threading.Thread(target=countdown_thread, daemon=True).start()

    def _finish_login(supabase, auth_response, reset_button_fn, email_hint=None):
        supabase.auth.set_session(
            access_token=auth_response.session.access_token,
            refresh_token=auth_response.session.refresh_token,
        )
        profile_response = (
            supabase.table("profiles")
            .select("role, is_active")
            .eq("id", auth_response.user.id)
            .single()
            .execute()
        )
        role = (
            profile_response.data.get("role", "evaluator") if profile_response.data else "evaluator"
        )
        is_active = profile_response.data.get("is_active", True) if profile_response.data else True
        if not is_active:
            try:
                supabase.auth.sign_out()
            except Exception:
                pass
            error_text.value = "Your account has been disabled. Please contact an administrator."
            error_text.color = ERROR
            error_text.visible = True
            reset_button_fn()
            page.update()
            return

        session_data = {
            "access_token": auth_response.session.access_token,
            "refresh_token": auth_response.session.refresh_token,
            "user_id": auth_response.user.id,
        }
        session_file = os.path.join(os.path.dirname(__file__), "..", ".session.json")
        with open(session_file, "w") as f:
            json.dump(session_data, f)

        if email_hint:
            reset_login_attempts(email_hint)

        if page.data:
            page.data["auth_active"] = False

        if nav:
            def fade_and_navigate():
                if page.controls:
                    for c in page.controls:
                        c.opacity = 0
                    page.update()
                time.sleep(0.2)
                if role == "admin":
                    nav.navigate_to_admin()
                elif role == "evaluator":
                    nav.navigate_to_short_answer()

            threading.Thread(target=fade_and_navigate, daemon=True).start()
        else:
            if role == "admin":
                nav.navigate_to_admin()
            elif role == "evaluator":
                nav.navigate_to_short_answer()
            else:
                error_text.value = "Invalid user role."
                error_text.color = ERROR
                error_text.visible = True
                reset_button_fn()
                page.update()

    def _reset_sign_in_btn():
        sign_in_btn.disabled = False
        sign_in_btn.bgcolor = BUTTON_PRIMARY_BG
        sign_in_btn.content = sign_in_btn_content

    def on_login(e):
        if sign_in_btn.disabled or lockout_timer_active["value"]:
            return
        if not si_email.value or not si_password.value:
            error_text.value = "Please enter email and password."
            error_text.color = ERROR
            error_text.visible = True
            page.update()
            return

        email_value = si_email.value.strip()

        error_text.visible = False
        sign_in_btn.disabled = True
        sign_in_btn.content = ft.Row(
            [
                ft.ProgressRing(width=16, height=16, stroke_width=2, color=BUTTON_PRIMARY_TEXT),
                ft.Text("Signing in...", size=14, weight=ft.FontWeight.BOLD, color=BUTTON_PRIMARY_TEXT),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
        )
        page.update()

        def login_thread():
            try:
                import asyncio

                try:
                    asyncio.get_event_loop()
                except RuntimeError:
                    asyncio.set_event_loop(asyncio.new_event_loop())

                remaining_lockout = get_lockout_remaining_seconds(email_value)
                if remaining_lockout > 0:
                    start_lockout_countdown(int(remaining_lockout))
                    return

                supabase = get_supabase_client()
                try:
                    auth_response = supabase.auth.sign_in_with_password(
                        {"email": email_value, "password": si_password.value}
                    )
                except Exception as auth_ex:
                    auth_err_msg = str(auth_ex).lower()
                    non_credential_markers = (
                        "rate limit",
                        "too many requests",
                        "network",
                        "timeout",
                        "connection",
                    )
                    if any(marker in auth_err_msg for marker in non_credential_markers):
                        raise
                    attempts_used, is_locked, lockout_seconds = record_failed_login(email_value)
                    if is_locked:
                        start_lockout_countdown(int(lockout_seconds))
                    else:
                        remaining_attempts = MAX_LOGIN_ATTEMPTS - attempts_used
                        error_text.value = (
                            f"Invalid email or password. {remaining_attempts} "
                            f"attempt{'s' if remaining_attempts != 1 else ''} remaining."
                        )
                        error_text.color = ERROR
                        error_text.visible = True
                        sign_in_btn.disabled = False
                        sign_in_btn.content = sign_in_btn_content
                        page.update()
                    return

                _finish_login(supabase, auth_response, _reset_sign_in_btn, email_hint=email_value)
            except Exception as ex:
                error_text.value = f"Login failed: {str(ex)}"
                error_text.color = ERROR
                error_text.visible = True
                sign_in_btn.disabled = False
                sign_in_btn.content = sign_in_btn_content
                page.update()

        threading.Thread(target=login_thread, daemon=True).start()

    sign_in_btn.on_click = on_login
    si_email.on_submit = on_login
    si_password.on_submit = on_login

    def _google_button_content(label):
        return ft.Row(
            [
                ft.Image(src=GOOGLE_LOGO_URL, width=18, height=18),
                ft.Text(label, size=14, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
        )

    def _google_loading_content(label):
        return ft.Row(
            [
                ft.ProgressRing(width=16, height=16, stroke_width=2, color=TEXT_PRIMARY),
                ft.Text(label, size=14, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
        )

    google_signin_processing = {"value": False}

    def _reset_google_button():
        google_btn_signin.content = _google_button_content("Continue with Google")

    def on_google_login(e):
        if google_signin_processing["value"]:
            return
        google_signin_processing["value"] = True
        error_text.visible = False
        google_btn_signin.content = _google_loading_content("Waiting for Google...")
        page.update()

        def google_thread():
            try:
                auth_response = sign_in_with_google()
                supabase = get_supabase_client()
                _finish_login(supabase, auth_response, _reset_google_button)
            except Exception as ex:
                message = f"Google sign-in failed: {str(ex)}"
                error_text.value = message
                error_text.color = ERROR
                error_text.visible = True
                _reset_google_button()
                page.update()
            finally:
                google_signin_processing["value"] = False

        threading.Thread(target=google_thread, daemon=True).start()

    google_btn_signin = google_button("Continue with Google")
    google_btn_signin.on_click = on_google_login

    sign_in_form = ft.Column(
        [
            ft.Text("Sign in to your account", size=25, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ft.Text("Enter your credentials to access QualCheck", size=13, color=TEXT_SECONDARY),
            ft.Container(height=26),
            ft.Text("Email address", size=13, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY),
            ft.Container(height=6),
            si_email,
            ft.Container(height=16),
            ft.Row(
                [
                    ft.Text("Password", size=13, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY),
                    ft.TextButton(
                        "Forgot password?",
                        style=ft.ButtonStyle(color=PRIMARY_BLUE, padding=ft.padding.all(0)),
                        on_click=lambda e: handle_forgot_password(e),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                width=400,
            ),
            ft.Container(height=6),
            si_password,
            ft.Container(height=10),
            error_text,
            lockout_card,
            ft.Container(height=20),
            sign_in_btn,
            ft.Container(height=20),
            or_divider(),
            ft.Container(height=20),
            google_btn_signin,
            ft.Container(height=26),
            ft.Row(
                [
                    ft.Text("Don't have an account?", size=13, color=TEXT_SECONDARY),
                    ft.TextButton(
                        "Create one",
                        style=ft.ButtonStyle(color=PRIMARY_BLUE, padding=ft.padding.all(0)),
                        on_click=lambda e: handle_go_to_create_account(e),
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=4,
            ),
            ft.Container(height=22),
            ft.Container(height=1, bgcolor=BORDER_COLOR, width=400),
            ft.Container(height=16),
            ft.Column(
                [
                    ft.Text("Access is restricted to authorised evaluators.", size=11.5, color=TEXT_TERTIARY, text_align=ft.TextAlign.CENTER),
                    ft.Text("Contact your system administrator for access.", size=11.5, color=TEXT_TERTIARY, text_align=ft.TextAlign.CENTER),
                ],
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                width=400,
            ),
        ],
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.START,
    )

    container = ft.Container(content=sign_in_form)
    return container, si_email


# ---------------------------------------------------------------------------
# MAIN — split-screen composition
# ---------------------------------------------------------------------------

def main(page: ft.Page, nav=None):
    if page.data is None:
        page.data = {}

    # Only take the "just switch tabs" shortcut if the login screen's own
    # controls are actually still on the page. If something cleaned the
    # page (e.g. Navigation.logout() -> page.clean()) while
    # page.data["auth_active"] was still True, taking this shortcut would
    # call the OLD switch_to_login() closure, which just tweaks opacity on
    # detached controls and never rebuilds anything — resulting in a
    # blank/broken screen. Falling through to the full rebuild below is
    # always safe.
    if (
        page.data.get("auth_active")
        and "auth_controller" in page.data
        and page.controls
    ):
        page.data["auth_controller"]["switch_to_login"]()
        return

    page.title = "QualCheck Login"
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
    page.clean()

    page.data["auth_active"] = True

    def on_go_to_create_account(e=None):
        if page.data and page.data.get("auth_active") and "auth_controller" in page.data:
            threading.Thread(
                target=page.data["auth_controller"]["switch_to_create_account"],
                daemon=True,
            ).start()
        else:
            from screens.ui_create_account import main as create_account_main
            threading.Thread(
                target=lambda: create_account_main(page, nav), daemon=True
            ).start()

    def on_go_to_sign_in(e=None, prefill_email=None):
        if page.data and page.data.get("auth_active") and "auth_controller" in page.data:
            threading.Thread(
                target=lambda: page.data["auth_controller"]["switch_to_login"](prefill_email),
                daemon=True,
            ).start()

    def on_forgot_password_cb(e=None):
        if page.data and page.data.get("auth_active") and "auth_controller" in page.data:
            threading.Thread(
                target=page.data["auth_controller"]["switch_to_reset_password"],
                daemon=True,
            ).start()
        else:
            reset_password_main(page, nav)

    # --- minimal tab toggle (Sign In / Create Account) -------------------------
    tab_signin = ft.Container(
        content=ft.Text("Sign In", size=13, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
        padding=ft.padding.only(bottom=10),
        on_click=lambda e: on_go_to_sign_in(e),
    )
    tab_create = ft.Container(
        content=ft.Text("Create Account", size=13, weight=ft.FontWeight.W_500, color=TEXT_TERTIARY),
        padding=ft.padding.only(bottom=10),
        on_click=lambda e: on_go_to_create_account(e),
    )
    ind_signin = ft.Container(height=2, width=52, bgcolor=PRIMARY_BLUE)
    ind_create = ft.Container(height=2, width=110, bgcolor="transparent")
    tab_row = ft.Row(
        [
            ft.Column([tab_signin, ind_signin], spacing=0),
            ft.Column([tab_create, ind_create], spacing=0),
        ],
        spacing=28,
    )

    sign_in_container, si_email_ref = build_sign_in_container(page, nav, on_go_to_create_account, on_forgot_password_cb)
    create_account_holder = {"container": None}
    reset_password_holder = {"container": None}
    switching_lock = {"active": False}

    form_wrapper = ft.Container(
        content=sign_in_container,
        animate_opacity=ft.Animation(180, ft.AnimationCurve.EASE_IN_OUT),
        opacity=1,
    )

    def switch_to_create_account():
        if switching_lock["active"]:
            return
        switching_lock["active"] = True

        if create_account_holder["container"] is None:
            from screens.ui_create_account import build_create_account_container
            ca_cont, _ = build_create_account_container(page, nav, on_go_to_sign_in)
            create_account_holder["container"] = ca_cont

        form_wrapper.opacity = 0
        page.update()
        time.sleep(0.18)

        tab_row.visible = True
        tab_signin.content.color = TEXT_TERTIARY
        tab_signin.content.weight = ft.FontWeight.W_500
        ind_signin.bgcolor = "transparent"
        tab_create.content.color = TEXT_PRIMARY
        tab_create.content.weight = ft.FontWeight.BOLD
        ind_create.bgcolor = PRIMARY_BLUE

        page.title = "QualCheck Create Account"
        form_wrapper.content = create_account_holder["container"]
        form_wrapper.opacity = 1
        page.update()

        switching_lock["active"] = False

    def switch_to_login(prefill_email=None):
        if switching_lock["active"]:
            return
        switching_lock["active"] = True

        if prefill_email and si_email_ref:
            si_email_ref.value = prefill_email

        form_wrapper.opacity = 0
        page.update()
        time.sleep(0.18)

        tab_row.visible = True
        tab_create.content.color = TEXT_TERTIARY
        tab_create.content.weight = ft.FontWeight.W_500
        ind_create.bgcolor = "transparent"
        tab_signin.content.color = TEXT_PRIMARY
        tab_signin.content.weight = ft.FontWeight.BOLD
        ind_signin.bgcolor = PRIMARY_BLUE

        page.title = "QualCheck Login"
        form_wrapper.content = sign_in_container
        form_wrapper.opacity = 1
        page.update()

        switching_lock["active"] = False

    def switch_to_reset_password():
        if switching_lock["active"]:
            return
        switching_lock["active"] = True

        if reset_password_holder["container"] is None:
            from screens.password_reset import build_reset_password_container
            reset_password_holder["container"] = build_reset_password_container(page, nav, on_go_to_sign_in)

        form_wrapper.opacity = 0
        page.update()
        time.sleep(0.18)

        tab_row.visible = False

        page.title = "QualCheck - Reset Password"
        form_wrapper.content = reset_password_holder["container"]
        form_wrapper.opacity = 1
        page.update()

        switching_lock["active"] = False

    page.data["auth_controller"] = {
        "switch_to_login": switch_to_login,
        "switch_to_create_account": switch_to_create_account,
        "switch_to_reset_password": switch_to_reset_password,
    }

    left_panel = build_left_panel(page)

    right_panel = ft.Container(
        content=ft.Column(
            [
                tab_row,
                ft.Container(height=26),
                form_wrapper,
            ],
            spacing=0,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.START,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
        bgcolor=BG_COLOR,
        padding=ft.padding.symmetric(horizontal=54, vertical=40),
        expand=5,
        alignment=ft.alignment.center,
    )

    layout = ft.Row(
        [left_panel, right_panel],
        spacing=0,
        expand=True,
        vertical_alignment=ft.CrossAxisAlignment.STRETCH,
    )

    page_fade = ft.Container(
        content=layout,
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