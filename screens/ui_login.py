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

try:
    from screens.password_reset import main as reset_password_main
except ModuleNotFoundError:

    def reset_password_main(page, nav=None):
        page.clean()
        page.add(ft.Text("Reset password screen is unavailable."))


def brand_header():
    logo = ft.Container(
        content=ft.Text("Q", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
        bgcolor=ft.Colors.BLUE_500,
        width=38,
        height=38,
        border_radius=8,
        alignment=ft.alignment.center,
        shadow=ft.BoxShadow(
            blur_radius=10, color=ft.Colors.BLUE_500, offset=ft.Offset(0, 0), spread_radius=2
        ),
    )
    brand = ft.Column(
        [
            ft.Text("QualCheck", size=17, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ft.Text("Semantic Evaluation System", size=11, color="#8b9bb4"),
        ],
        spacing=0,
    )
    return ft.Row([logo, brand], spacing=12, alignment=ft.MainAxisAlignment.START)


GOOGLE_LOGO_URL = "assets/google.png"


def google_button(label):
    return ft.Container(
        content=ft.Row(
            [
                ft.Image(src=GOOGLE_LOGO_URL, width=18, height=18),
                ft.Text(label, size=14, weight=ft.FontWeight.W_500, color="#1a1a1a"),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
        ),
        bgcolor=ft.Colors.WHITE,
        border_radius=8,
        height=44,
        width=400,
        alignment=ft.alignment.center,
        border=ft.border.all(1, "#d1d5db"),
        ink=True,
    )


def or_divider():
    line = ft.Container(height=1, bgcolor="#2a3b54", expand=True)
    return ft.Row(
        [line, ft.Text("or", size=12, color="#4a5b75"), line],
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
        height=44,
        bgcolor="#1e2f46",
        border_color="#2e4060",
        focused_border_color=ft.Colors.BLUE_400,
        text_size=14,
        content_padding=ft.padding.symmetric(horizontal=14, vertical=10),
        hint_style=ft.TextStyle(color="#4a5b75"),
        color=ft.Colors.WHITE,
        border_radius=8,
    )


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

    error_text = ft.Text("", size=12, color=ft.Colors.RED_400, visible=False)

    timer_display = ft.Text(
        "00:00",
        size=15,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.RED_400,
        font_family="monospace",
    )

    lockout_card = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Icon(ft.Icons.LOCK_CLOCK_OUTLINED, color=ft.Colors.RED_400, size=20),
                    padding=8,
                    bgcolor="#3b1d28",
                    border_radius=8,
                ),
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text(
                                    "Account Locked",
                                    size=13,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.RED_300,
                                ),
                                timer_display,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            width=300,
                        ),
                        ft.Text(
                            "Too many failed attempts. Please wait.",
                            size=11,
                            color="#9daec8",
                        ),
                    ],
                    spacing=2,
                    expand=True,
                ),
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor="#24141e",
        border=ft.border.all(1, "#522232"),
        border_radius=8,
        padding=ft.padding.symmetric(horizontal=12, vertical=10),
        width=400,
        visible=False,
    )

    si_email = text_field(hint="you@university.edu")
    si_password = text_field(password=True, reveal=True)
    sign_in_btn_content = ft.Row(
        [
            ft.Icon(ft.Icons.LOGIN_ROUNDED, size=16, color=ft.Colors.WHITE),
            ft.Text("Sign in", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=8,
    )
    sign_in_btn = ft.Container(
        content=sign_in_btn_content,
        width=400,
        height=46,
        bgcolor=ft.Colors.BLUE_600,
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
            sign_in_btn.bgcolor = "#1a2638"
            sign_in_btn.content = ft.Row(
                [
                    ft.Icon(ft.Icons.LOCK_OUTLINED, size=16, color="#4a5b75"),
                    ft.Text(
                        "Sign in disabled", size=14, weight=ft.FontWeight.BOLD, color="#4a5b75"
                    ),
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
                error_text.color = ft.Colors.GREEN_400
                error_text.visible = True

                sign_in_btn.disabled = False
                sign_in_btn.bgcolor = ft.Colors.BLUE_600
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
            error_text.color = ft.Colors.RED_400
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
                error_text.color = ft.Colors.RED_400
                error_text.visible = True
                reset_button_fn()
                page.update()

    def _reset_sign_in_btn():
        sign_in_btn.disabled = False
        sign_in_btn.bgcolor = ft.Colors.BLUE_600
        sign_in_btn.content = sign_in_btn_content

    def on_login(e):
        if sign_in_btn.disabled or lockout_timer_active["value"]:
            return
        if not si_email.value or not si_password.value:
            error_text.value = "Please enter email and password."
            error_text.color = ft.Colors.RED_400
            error_text.visible = True
            page.update()
            return

        email_value = si_email.value.strip()

        error_text.visible = False
        sign_in_btn.disabled = True
        sign_in_btn.content = ft.Row(
            [
                ft.ProgressRing(width=16, height=16, stroke_width=2, color=ft.Colors.WHITE),
                ft.Text("Signing in...", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
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
                        error_text.color = ft.Colors.RED_400
                        error_text.visible = True
                        sign_in_btn.disabled = False
                        sign_in_btn.content = sign_in_btn_content
                        page.update()
                    return

                _finish_login(supabase, auth_response, _reset_sign_in_btn, email_hint=email_value)
            except Exception as ex:
                error_text.value = f"Login failed: {str(ex)}"
                error_text.color = ft.Colors.RED_400
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
                ft.Text(label, size=14, weight=ft.FontWeight.W_500, color="#1a1a1a"),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
        )

    def _google_loading_content(label):
        return ft.Row(
            [
                ft.ProgressRing(width=16, height=16, stroke_width=2, color="#1a1a1a"),
                ft.Text(label, size=14, weight=ft.FontWeight.W_500, color="#1a1a1a"),
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
                error_text.color = ft.Colors.RED_400
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
            brand_header(),
            ft.Container(height=8),
            ft.Text("Welcome back", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ft.Text("Sign in to continue evaluating responses", size=13, color="#8b9bb4"),
            ft.Container(height=12),
            google_btn_signin,
            ft.Container(height=10),
            or_divider(),
            ft.Container(height=10),
            ft.Text("Email", size=13, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE),
            ft.Container(height=4),
            si_email,
            ft.Container(height=8),
            ft.Row(
                [
                    ft.Text("Password", size=13, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE),
                    ft.TextButton(
                        "Forgot password?",
                        style=ft.ButtonStyle(color=ft.Colors.BLUE_400, padding=ft.padding.all(0)),
                        on_click=lambda e: handle_forgot_password(e),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                width=400,
            ),
            ft.Container(height=4),
            si_password,
            ft.Container(height=6),
            error_text,
            lockout_card,
            ft.Container(height=14),
            sign_in_btn,
            ft.Container(height=16),
            ft.Row(
                [
                    ft.Text("Don't have an account?", size=13, color="#4a5b75"),
                    ft.TextButton(
                        "Create one",
                        style=ft.ButtonStyle(color=ft.Colors.BLUE_400, padding=ft.padding.all(0)),
                        on_click=lambda e: handle_go_to_create_account(e),
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=4,
            ),
        ],
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.START,
    )

    container = ft.Container(
        content=sign_in_form,
        padding=ft.padding.symmetric(horizontal=40, vertical=30),
    )
    return container, si_email


def main(page: ft.Page, nav=None):
    if page.data is None:
        page.data = {}

    if page.data.get("auth_active") and "auth_controller" in page.data:
        page.data["auth_controller"]["switch_to_login"]()
        return

    page.title = "QualCheck Login"
    page.window_width = 900
    page.window_height = 780
    page.window_min_width = 900
    page.window_min_height = 780
    page.window_resizable = True
    page.padding = 0
    page.bgcolor = "#0f1e30"
    page.theme_mode = ft.ThemeMode.DARK
    page.appbar = None
    page.clean()

    blob1 = ft.Container(
        width=600,
        height=600,
        gradient=ft.RadialGradient(
            colors=[
                ft.Colors.with_opacity(0.12, ft.Colors.BLUE_400),
                ft.Colors.with_opacity(0.0, ft.Colors.BLUE_400),
            ],
            stops=[0.0, 1.0],
        ),
        left=-100,
        top=-100,
    )
    blob2 = ft.Container(
        width=800,
        height=800,
        gradient=ft.RadialGradient(
            colors=[
                ft.Colors.with_opacity(0.08, ft.Colors.CYAN_400),
                ft.Colors.with_opacity(0.0, ft.Colors.CYAN_400),
            ],
            stops=[0.0, 1.0],
        ),
        right=-200,
        bottom=-200,
    )
    blob3 = ft.Container(
        width=500,
        height=500,
        gradient=ft.RadialGradient(
            colors=[
                ft.Colors.with_opacity(0.10, ft.Colors.PURPLE_400),
                ft.Colors.with_opacity(0.0, ft.Colors.PURPLE_400),
            ],
            stops=[0.0, 1.0],
        ),
        left=100,
        bottom=-100,
    )

    page.data["auth_active"] = True

    def animate_blobs():
        t = 0.0
        while page.title in ("QualCheck Login", "QualCheck Create Account", "QualCheck - Reset Password") and page.data.get("auth_active", False):
            try:
                blob1.top = -100 + 80 * math.sin(t)
                blob1.left = -100 + 120 * math.cos(t * 0.8)
                blob2.bottom = -200 + 100 * math.cos(t * 0.9)
                blob2.right = -200 + 150 * math.sin(t * 0.7)
                blob3.bottom = -100 + 120 * math.sin(t * 1.1)
                blob3.left = 100 + 80 * math.cos(t * 0.6)
                page.update()
                time.sleep(0.05)
                t += 0.05
            except Exception:
                break

    threading.Thread(target=animate_blobs, daemon=True).start()

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

    tab_signin = ft.Container(
        content=ft.Text(
            "Sign In",
            size=14,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.WHITE,
            text_align=ft.TextAlign.CENTER,
        ),
        padding=ft.padding.symmetric(horizontal=24, vertical=14),
        bgcolor="#1c2c44",
        expand=True,
        alignment=ft.alignment.center,
        border_radius=ft.border_radius.only(top_left=16),
        on_click=lambda e: on_go_to_sign_in(e),
        ink=True,
    )
    tab_create = ft.Container(
        content=ft.Text(
            "Create Account",
            size=14,
            weight=ft.FontWeight.W_500,
            color="#6b7f99",
            text_align=ft.TextAlign.CENTER,
        ),
        padding=ft.padding.symmetric(horizontal=24, vertical=14),
        bgcolor="#161f2e",
        expand=True,
        alignment=ft.alignment.center,
        border_radius=ft.border_radius.only(top_right=16),
        on_click=lambda e: on_go_to_create_account(e),
        ink=True,
    )
    ind_signin = ft.Container(height=2, bgcolor=ft.Colors.BLUE_500, expand=True)
    ind_create = ft.Container(height=2, bgcolor="transparent", expand=True)
    tab_row = ft.Row(
        [
            ft.Column([tab_signin, ind_signin], spacing=0, expand=True),
            ft.Column([tab_create, ind_create], spacing=0, expand=True),
        ],
        spacing=0,
        expand=True,
    )
    tab_divider = ft.Container(height=1, bgcolor="#1e2f46")

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

        form_wrapper.animate_opacity = ft.Animation(180, ft.AnimationCurve.EASE_IN_OUT)
        form_wrapper.opacity = 0
        page.update()
        time.sleep(0.18)

        tab_row.visible = True
        tab_divider.visible = True

        tab_signin.bgcolor = "#161f2e"
        tab_signin.content.color = "#6b7f99"
        tab_signin.content.weight = ft.FontWeight.W_500
        ind_signin.bgcolor = "transparent"

        tab_create.bgcolor = "#1c2c44"
        tab_create.content.color = ft.Colors.WHITE
        tab_create.content.weight = ft.FontWeight.BOLD
        ind_create.bgcolor = ft.Colors.BLUE_500

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

        form_wrapper.animate_opacity = ft.Animation(180, ft.AnimationCurve.EASE_IN_OUT)
        form_wrapper.opacity = 0
        page.update()
        time.sleep(0.18)

        tab_row.visible = True
        tab_divider.visible = True

        tab_create.bgcolor = "#161f2e"
        tab_create.content.color = "#6b7f99"
        tab_create.content.weight = ft.FontWeight.W_500
        ind_create.bgcolor = "transparent"

        tab_signin.bgcolor = "#1c2c44"
        tab_signin.content.color = ft.Colors.WHITE
        tab_signin.content.weight = ft.FontWeight.BOLD
        ind_signin.bgcolor = ft.Colors.BLUE_500

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

        form_wrapper.animate_opacity = ft.Animation(180, ft.AnimationCurve.EASE_IN_OUT)
        form_wrapper.opacity = 0
        page.update()
        time.sleep(0.18)

        tab_row.visible = False
        tab_divider.visible = False

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

    card = ft.Container(
        content=ft.Column(
            [
                tab_row,
                tab_divider,
                form_wrapper,
            ],
            spacing=0,
        ),
        bgcolor="#1c2c44",
        border_radius=16,
        width=480,
        border=ft.border.all(1, "#243447"),
        shadow=ft.BoxShadow(
            blur_radius=40, color="#070f1a", offset=ft.Offset(0, 12), spread_radius=0
        ),
    )

    bottom_links = ft.Row(
        [
            ft.Column(
                [
                    ft.Text("BERT", color=ft.Colors.BLUE_400, size=12, weight=ft.FontWeight.BOLD),
                    ft.Text("Embeddings", color="#4a5b75", size=11),
                ],
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Container(width=24),
            ft.Column(
                [
                    ft.Text("Cosine", color=ft.Colors.BLUE_400, size=12, weight=ft.FontWeight.BOLD),
                    ft.Text("Similarity", color="#4a5b75", size=11),
                ],
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Container(width=24),
            ft.Column(
                [
                    ft.Text("Rubric", color=ft.Colors.BLUE_400, size=12, weight=ft.FontWeight.BOLD),
                    ft.Text("Guided", color="#4a5b75", size=11),
                ],
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
    )
    page_fade = ft.Container(
        content=ft.Stack(
            [
                blob1,
                blob2,
                blob3,
                ft.Column(
                    [
                        ft.Container(height=60),
                        card,
                        ft.Container(height=28),
                        bottom_links,
                        ft.Container(height=40),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                ),
            ],
            expand=True,
            clip_behavior=ft.ClipBehavior.NONE,
        ),
        expand=True,
        opacity=0,
        animate_opacity=ft.Animation(220, ft.AnimationCurve.EASE_OUT),
    )
    page.add(page_fade)
    page.update()
    time.sleep(0.03)
    page_fade.opacity = 1
    page.update()


if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")