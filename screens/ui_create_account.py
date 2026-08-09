import sys
import os
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import math
import time
import threading
import flet as ft
from services.supabase_client import get_supabase_client
from services.google_oauth import sign_in_with_google
from services.registration import (
    generate_access_code,
    send_signup_verification,
    complete_registration,
)

try:
    from database.auth import validate_password
except (ModuleNotFoundError, ImportError):

    def validate_password(password: str) -> tuple[bool, str]:
        """
        Validate password against security requirements.
        Fallback used only if database.auth is unavailable.
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least 1 lowercase letter"
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least 1 uppercase letter"
        if not re.search(r'\d', password):
            return False, "Password must contain at least 1 number"
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least 1 special character"
        return True, ""


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


def loading_button(label):
    return ft.Container(
        content=ft.Row(
            [
                ft.ProgressRing(width=16, height=16, stroke_width=2, color=ft.Colors.WHITE),
                ft.Text(label, size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
        ),
        width=400,
        height=46,
        bgcolor=ft.Colors.BLUE_600,
        border_radius=8,
        alignment=ft.alignment.center,
    )


def action_button(label, icon, on_click):
    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(icon, size=16, color=ft.Colors.WHITE),
                ft.Text(label, size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
        ),
        width=400,
        height=46,
        bgcolor=ft.Colors.BLUE_600,
        border_radius=8,
        alignment=ft.alignment.center,
        ink=True,
        on_click=on_click,
    )


def build_create_account_container(page: ft.Page, nav=None, on_go_to_sign_in=None):
    def handle_go_to_sign_in(e=None, prefill_email=None):
        if on_go_to_sign_in:
            on_go_to_sign_in(e, prefill_email=prefill_email)
        else:
            if page.data and page.data.get("auth_active") and "auth_controller" in page.data:
                threading.Thread(
                    target=lambda: page.data["auth_controller"]["switch_to_login"](prefill_email),
                    daemon=True,
                ).start()
            else:
                from screens.ui_login import main as login_main
                threading.Thread(
                    target=lambda: login_main(page, nav), daemon=True
                ).start()

    ca_error = ft.Text("", size=12, color=ft.Colors.RED_400, visible=False)

    ca_fullname = text_field(hint="Prof. Maria Santos")
    ca_email = text_field(hint="you@university.edu")
    ca_password = text_field(
        hint="Min. 8 chars: 1 uppercase, 1 number, 1 special", password=True, reveal=True
    )
    ca_confirm = text_field(password=True, reveal=True)
    ca_code_field = text_field(
        hint="Enter the 6-digit code sent to your email", read_only=False, value=""
    )

    class SignupState:
        step = 1
        access_code = None
        processing = False

    signup_state = SignupState()

    def on_create_account(e):
        if signup_state.processing:
            return

        if signup_state.step == 1:
            if (
                not ca_fullname.value
                or not ca_email.value
                or not ca_password.value
                or not ca_confirm.value
            ):
                ca_error.value = "Please fill in all fields."
                ca_error.visible = True
                ca_error.color = ft.Colors.RED_400
                page.update()
                return
            if ca_password.value != ca_confirm.value:
                ca_error.value = "Passwords do not match."
                ca_error.visible = True
                ca_error.color = ft.Colors.RED_400
                page.update()
                return
            is_valid, password_error = validate_password(ca_password.value)
            if not is_valid:
                ca_error.value = password_error
                ca_error.visible = True
                ca_error.color = ft.Colors.RED_400
                page.update()
                return

            ca_error.visible = False
            signup_state.processing = True
            ca_action_button_container.content = loading_button("Sending code...")
            page.update()

            def send_code_thread():
                signup_state.access_code = generate_access_code()
                try:
                    send_signup_verification(
                        email=ca_email.value,
                        full_name=ca_fullname.value,
                        temp_password=ca_password.value,
                        access_code=signup_state.access_code,
                    )
                    signup_state.step = 2
                    ca_step1.visible = False
                    ca_step2.visible = True
                    ca_action_button_container.content = action_button(
                        "Verify & Complete", ft.Icons.CHECK_CIRCLE_OUTLINE, on_create_account
                    )
                    ca_error.value = "Verification code sent to your email."
                    ca_error.color = ft.Colors.GREEN_400
                    ca_error.visible = True
                except Exception as email_error:
                    ca_error.value = f"Failed to send email: {email_error}"
                    ca_error.color = ft.Colors.RED_400
                    ca_error.visible = True
                    ca_action_button_container.content = action_button(
                        "Create Account", ft.Icons.PERSON_ADD_ROUNDED, on_create_account
                    )
                finally:
                    signup_state.processing = False
                    page.update()

            threading.Thread(target=send_code_thread, daemon=True).start()
        else:
            if not ca_code_field.value:
                ca_error.value = "Please enter the verification code."
                ca_error.visible = True
                ca_error.color = ft.Colors.RED_400
                page.update()
                return
            if ca_code_field.value != signup_state.access_code:
                ca_error.value = "Invalid verification code."
                ca_error.visible = True
                ca_error.color = ft.Colors.RED_400
                page.update()
                return

            ca_error.visible = False
            signup_state.processing = True
            ca_action_button_container.content = loading_button("Creating account...")
            page.update()

            def create_account_thread():
                try:
                    complete_registration(
                        email=ca_email.value,
                        password=ca_password.value,
                        full_name=ca_fullname.value,
                        access_code=signup_state.access_code,
                    )
                    handle_go_to_sign_in(None, prefill_email=ca_email.value)
                except Exception as ex:
                    error_msg = str(ex).lower()
                    if "rate limit" in error_msg or "too many requests" in error_msg:
                        ca_error.value = (
                            "Too many registration attempts. "
                            "Please wait a few minutes and try again."
                        )
                    else:
                        ca_error.value = f"Registration failed: {str(ex)}"
                    ca_error.color = ft.Colors.RED_400
                    ca_error.visible = True
                    ca_action_button_container.content = action_button(
                        "Verify & Complete", ft.Icons.CHECK_CIRCLE_OUTLINE, on_create_account
                    )
                finally:
                    signup_state.processing = False
                    page.update()

            threading.Thread(target=create_account_thread, daemon=True).start()

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
        google_btn_signup.content = _google_button_content("Sign up with Google")

    def on_google_login(e):
        if google_signin_processing["value"]:
            return
        google_signin_processing["value"] = True
        ca_error.visible = False
        google_btn_signup.content = _google_loading_content("Waiting for Google...")
        page.update()

        def google_thread():
            try:
                auth_response = sign_in_with_google()
                supabase = get_supabase_client()
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
                    profile_response.data.get("role", "evaluator")
                    if profile_response.data
                    else "evaluator"
                )
                is_active = (
                    profile_response.data.get("is_active", True)
                    if profile_response.data
                    else True
                )
                if not is_active:
                    try:
                        supabase.auth.sign_out()
                    except Exception:
                        pass
                    ca_error.value = "Your account has been disabled. Please contact an administrator."
                    ca_error.color = ft.Colors.RED_400
                    ca_error.visible = True
                    _reset_google_button()
                    page.update()
                    return

                session_data = {
                    "access_token": auth_response.session.access_token,
                    "refresh_token": auth_response.session.refresh_token,
                    "user_id": auth_response.user.id,
                }
                session_file = os.path.join(os.path.dirname(__file__), "..", ".session.json")
                with open(session_file, "w") as f:
                    import json
                    json.dump(session_data, f)

                if page.data:
                    page.data["auth_active"] = False

                if nav:
                    if role == "admin":
                        nav.navigate_to_admin()
                    elif role == "evaluator":
                        nav.navigate_to_short_answer()
                    else:
                        ca_error.value = "Invalid user role."
                        ca_error.color = ft.Colors.RED_400
                        ca_error.visible = True
                        _reset_google_button()
                        page.update()
            except Exception as ex:
                ca_error.value = f"Google sign-in failed: {str(ex)}"
                ca_error.color = ft.Colors.RED_400
                ca_error.visible = True
                _reset_google_button()
                page.update()
            finally:
                google_signin_processing["value"] = False

        threading.Thread(target=google_thread, daemon=True).start()

    google_btn_signup = google_button("Sign up with Google")
    google_btn_signup.on_click = on_google_login

    ca_step1 = ft.Column(
        [
            ft.Text("Full Name", size=13, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE),
            ft.Container(height=4),
            ca_fullname,
            ft.Container(height=8),
            ft.Text("Email", size=13, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE),
            ft.Container(height=4),
            ca_email,
            ft.Container(height=8),
            ft.Text("Password", size=13, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE),
            ft.Container(height=4),
            ca_password,
            ft.Container(height=8),
            ft.Text("Confirm Password", size=13, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE),
            ft.Container(height=4),
            ca_confirm,
            ft.Container(height=8),
        ],
        spacing=0,
        visible=True,
    )
    ca_step2 = ft.Column(
        [
            ft.Text(
                "6-Digit Verification Code",
                size=13,
                weight=ft.FontWeight.W_500,
                color=ft.Colors.WHITE,
            ),
            ft.Container(height=4),
            ca_code_field,
            ft.Container(height=8),
        ],
        spacing=0,
        visible=False,
    )
    ca_action_button_container = ft.Container(
        content=action_button("Create Account", ft.Icons.PERSON_ADD_ROUNDED, on_create_account)
    )

    create_account_form = ft.Column(
        [
            brand_header(),
            ft.Container(height=8),
            ft.Text(
                "Create your account", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE
            ),
            ft.Text("Join QualCheck as an evaluator", size=13, color="#8b9bb4"),
            ft.Container(height=12),
            google_btn_signup,
            ft.Container(height=10),
            or_divider(),
            ft.Container(height=10),
            ca_step1,
            ca_step2,
            ca_error,
            ft.Container(height=14),
            ca_action_button_container,
            ft.Container(height=16),
            ft.Row(
                [
                    ft.Text("Already have an account?", size=13, color="#4a5b75"),
                    ft.TextButton(
                        "Sign in",
                        style=ft.ButtonStyle(color=ft.Colors.BLUE_400, padding=ft.padding.all(0)),
                        on_click=lambda e: handle_go_to_sign_in(e),
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
        content=create_account_form,
        padding=ft.padding.symmetric(horizontal=40, vertical=30),
    )
    return container, ca_email


def main(page: ft.Page, nav=None):
    if page.data is None:
        page.data = {}

    if page.data.get("auth_active") and "auth_controller" in page.data:
        page.data["auth_controller"]["switch_to_create_account"]()
        return

    page.title = "QualCheck Create Account"
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

    def on_go_to_sign_in(e=None, prefill_email=None):
        if page.data and page.data.get("auth_active") and "auth_controller" in page.data:
            threading.Thread(
                target=lambda: page.data["auth_controller"]["switch_to_login"](prefill_email),
                daemon=True,
            ).start()
        else:
            from screens.ui_login import main as login_main
            threading.Thread(
                target=lambda: login_main(page, nav), daemon=True
            ).start()

    def on_go_to_create_account(e=None):
        if page.data and page.data.get("auth_active") and "auth_controller" in page.data:
            threading.Thread(
                target=page.data["auth_controller"]["switch_to_create_account"],
                daemon=True,
            ).start()

    tab_signin = ft.Container(
        content=ft.Text(
            "Sign In",
            size=14,
            weight=ft.FontWeight.W_500,
            color="#6b7f99",
            text_align=ft.TextAlign.CENTER,
        ),
        padding=ft.padding.symmetric(horizontal=24, vertical=14),
        bgcolor="#161f2e",
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
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.WHITE,
            text_align=ft.TextAlign.CENTER,
        ),
        padding=ft.padding.symmetric(horizontal=24, vertical=14),
        bgcolor="#1c2c44",
        expand=True,
        alignment=ft.alignment.center,
        border_radius=ft.border_radius.only(top_right=16),
        on_click=lambda e: on_go_to_create_account(e),
        ink=True,
    )
    ind_signin = ft.Container(height=2, bgcolor="transparent", expand=True)
    ind_create = ft.Container(height=2, bgcolor=ft.Colors.BLUE_500, expand=True)
    tab_row = ft.Row(
        [
            ft.Column([tab_signin, ind_signin], spacing=0, expand=True),
            ft.Column([tab_create, ind_create], spacing=0, expand=True),
        ],
        spacing=0,
        expand=True,
    )
    tab_divider = ft.Container(height=1, bgcolor="#1e2f46")

    create_account_container, _ = build_create_account_container(page, nav, on_go_to_sign_in)
    sign_in_holder = {"container": None, "email_ref": None}
    reset_password_holder = {"container": None}
    switching_lock = {"active": False}

    form_wrapper = ft.Container(
        content=create_account_container,
        animate_opacity=ft.Animation(180, ft.AnimationCurve.EASE_IN_OUT),
        opacity=1,
    )

    def switch_to_login(prefill_email=None):
        if switching_lock["active"]:
            return
        switching_lock["active"] = True

        if sign_in_holder["container"] is None:
            from screens.ui_login import build_sign_in_container
            si_cont, si_email_ref = build_sign_in_container(page, nav, on_go_to_create_account)
            sign_in_holder["container"] = si_cont
            sign_in_holder["email_ref"] = si_email_ref

        if prefill_email and sign_in_holder["email_ref"]:
            sign_in_holder["email_ref"].value = prefill_email

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
        form_wrapper.content = sign_in_holder["container"]
        form_wrapper.opacity = 1
        page.update()

        switching_lock["active"] = False

    def switch_to_create_account():
        if switching_lock["active"]:
            return
        switching_lock["active"] = True

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
        form_wrapper.content = create_account_container
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