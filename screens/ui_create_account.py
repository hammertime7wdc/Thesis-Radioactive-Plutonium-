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
from utils.resend_control import build_resend_code_control
from utils.utils import (
    BG_COLOR,
    CARD_BG_COLOR,
    PRIMARY_BLUE,
    PRIMARY_BLUE_DARK,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_TERTIARY,
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


def loading_button(label):
    return ft.Container(
        content=ft.Row(
            [
                ft.ProgressRing(width=16, height=16, stroke_width=2, color=BUTTON_PRIMARY_TEXT),
                ft.Text(label, size=14, weight=ft.FontWeight.BOLD, color=BUTTON_PRIMARY_TEXT),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
        ),
        width=400,
        height=48,
        bgcolor=BUTTON_PRIMARY_BG,
        border_radius=8,
        alignment=ft.alignment.center,
    )


def action_button(label, icon, on_click):
    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(icon, size=16, color=BUTTON_PRIMARY_TEXT),
                ft.Text(label, size=14, weight=ft.FontWeight.BOLD, color=BUTTON_PRIMARY_TEXT),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
        ),
        width=400,
        height=48,
        bgcolor=BUTTON_PRIMARY_BG,
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

    ca_error = ft.Text("", size=12, color=ERROR, visible=False)

    ca_fullname = text_field(hint="Prof. Maria Santos")
    ca_email = text_field(hint="you@university.edu")
    ca_password = text_field(
        hint="Min. 8 chars: 1 uppercase, 1 number, 1 special", password=True, reveal=True
    )
    ca_confirm = text_field(password=True, reveal=True)
    ca_code_field = ft.TextField(
        hint_text="• • • • • •",
        width=400,
        height=46,
        bgcolor=INPUT_BG,
        border_color=INPUT_BORDER,
        focused_border_color=PRIMARY_BLUE,
        text_size=14,
        text_align=ft.TextAlign.CENTER,
        content_padding=ft.padding.symmetric(horizontal=14, vertical=10),
        hint_style=ft.TextStyle(color=INPUT_HINT),
        color=INPUT_TEXT,
        border_radius=8,
        max_length=6,
        input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]"),
    )

    verify_email_text = ft.Text(
        "",
        size=13,
        color=TEXT_SECONDARY,
        text_align=ft.TextAlign.CENTER,
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
                ca_error.color = ERROR
                page.update()
                return
            if ca_password.value != ca_confirm.value:
                ca_error.value = "Passwords do not match."
                ca_error.visible = True
                ca_error.color = ERROR
                page.update()
                return
            is_valid, password_error = validate_password(ca_password.value)
            if not is_valid:
                ca_error.value = password_error
                ca_error.visible = True
                ca_error.color = ERROR
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
                    verify_email_text.spans = [
                        ft.TextSpan("We sent a 6-digit code to\n"),
                        ft.TextSpan(
                            ca_email.value,
                            ft.TextStyle(weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ),
                    ]
                    ca_step1_header.visible = False
                    ca_step1.visible = False
                    google_btn_signup.visible = False
                    ca_or_divider.visible = False
                    ca_bottom_row.visible = False
                    ca_back_link.visible = True
                    ca_step2_header.visible = True
                    ca_step2.visible = True
                    ca_resend_row.visible = True
                    ca_action_button_container.content = action_button(
                        "Verify Email", ft.Icons.CHECK, on_create_account
                    )
                    ca_error.value = "Verification code sent to your email."
                    ca_error.color = SUCCESS
                    ca_error.visible = True
                except Exception as email_error:
                    ca_error.value = f"Failed to send email: {email_error}"
                    ca_error.color = ERROR
                    ca_error.visible = True
                    ca_action_button_container.content = action_button(
                        "Create Account", ft.Icons.PERSON_ADD_ROUNDED, on_create_account
                    )
                finally:
                    signup_state.processing = False
                    page.update()

            threading.Thread(target=send_code_thread, daemon=True).start()
        else:
            if not ca_code_field.value or len(ca_code_field.value) != 6:
                ca_error.value = "Please enter the verification code."
                ca_error.visible = True
                ca_error.color = ERROR
                page.update()
                return
            if ca_code_field.value != signup_state.access_code:
                ca_error.value = "Invalid verification code."
                ca_error.visible = True
                ca_error.color = ERROR
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
                    ca_error.value = "Account created successfully."
                    ca_error.color = SUCCESS
                    ca_error.visible = True
                except Exception as ex:
                    error_msg = str(ex).lower()
                    if "rate limit" in error_msg or "too many requests" in error_msg:
                        ca_error.value = (
                            "Too many registration attempts. "
                            "Please wait a few minutes and try again."
                        )
                    else:
                        ca_error.value = f"Registration failed: {str(ex)}"
                    ca_error.color = ERROR
                    ca_error.visible = True
                    ca_action_button_container.content = action_button(
                        "Verify Email", ft.Icons.CHECK, on_create_account
                    )
                finally:
                    signup_state.processing = False
                    if signup_state.step == 2 and ca_action_button_container.content is not None:
                        ca_action_button_container.content = action_button(
                            "Verify Email", ft.Icons.CHECK, on_create_account
                        )
                    page.update()

            threading.Thread(target=create_account_thread, daemon=True).start()

    def on_resend_code(e):
        if signup_state.processing:
            return
        signup_state.processing = True
        ca_action_button_container.content = loading_button("Resending code...")
        page.update()

        def resend_thread():
            signup_state.access_code = generate_access_code()
            try:
                send_signup_verification(
                    email=ca_email.value,
                    full_name=ca_fullname.value,
                    temp_password=ca_password.value,
                    access_code=signup_state.access_code,
                )
                ca_error.value = "A new code was sent to your email."
                ca_error.color = SUCCESS
                ca_error.visible = True
            except Exception as email_error:
                ca_error.value = f"Failed to resend code: {email_error}"
                ca_error.color = ERROR
                ca_error.visible = True
            finally:
                ca_action_button_container.content = action_button(
                    "Verify Email", ft.Icons.CHECK, on_create_account
                )
                signup_state.processing = False
                page.update()

        threading.Thread(target=resend_thread, daemon=True).start()

    def on_back_to_signup(e):
        if signup_state.processing:
            return
        signup_state.step = 1
        ca_error.visible = False
        ca_back_link.visible = False
        ca_step1_header.visible = True
        ca_step1.visible = True
        google_btn_signup.visible = True
        ca_or_divider.visible = True
        ca_bottom_row.visible = True
        ca_step2_header.visible = False
        ca_step2.visible = False
        ca_resend_row.visible = False
        ca_action_button_container.content = action_button(
            "Create Account", ft.Icons.PERSON_ADD_ROUNDED, on_create_account
        )
        page.update()

    ca_fullname.on_submit = on_create_account
    ca_email.on_submit = on_create_account
    ca_password.on_submit = on_create_account
    ca_confirm.on_submit = on_create_account
    ca_code_field.on_submit = on_create_account

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
                    ca_error.color = ERROR
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
                        ca_error.color = ERROR
                        ca_error.visible = True
                        _reset_google_button()
                        page.update()
            except Exception as ex:
                ca_error.value = f"Google sign-in failed: {str(ex)}"
                ca_error.color = ERROR
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
            ft.Text("Full Name", size=13, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY),
            ft.Container(height=6),
            ca_fullname,
            ft.Container(height=14),
            ft.Text("Email", size=13, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY),
            ft.Container(height=6),
            ca_email,
            ft.Container(height=14),
            ft.Text("Password", size=13, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY),
            ft.Container(height=6),
            ca_password,
            ft.Container(height=14),
            ft.Text("Confirm Password", size=13, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY),
            ft.Container(height=6),
            ca_confirm,
            ft.Container(height=8),
        ],
        spacing=0,
        visible=True,
    )
    ca_step2 = ft.Column(
        [
            ft.Text("Verification code", size=13, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY),
            ft.Container(height=6),
            ca_code_field,
            ft.Container(height=8),
        ],
        spacing=0,
        visible=False,
    )
    ca_action_button_container = ft.Container(
        content=action_button("Create Account", ft.Icons.PERSON_ADD_ROUNDED, on_create_account)
    )

    ca_step1_header = ft.Column(
        [
            ft.Text(
                "Create your account", size=25, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY
            ),
            ft.Text("Join QualCheck as an evaluator", size=13, color=TEXT_SECONDARY),
        ],
        spacing=0,
        visible=True,
    )

    ca_back_link = ft.GestureDetector(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.ARROW_BACK, size=14, color=TEXT_SECONDARY),
                ft.Text("Back to sign up", size=13, color=TEXT_SECONDARY),
            ],
            spacing=6,
        ),
        on_tap=on_back_to_signup,
        visible=False,
    )

    ca_step2_header = ft.Column(
        [
            ft.Container(
                content=ft.Icon(ft.Icons.MAIL_OUTLINE, color=PRIMARY_BLUE, size=24),
                width=52,
                height=52,
                alignment=ft.alignment.center,
                border_radius=26,
                bgcolor="#eef4ff",
                border=ft.border.all(1, ft.Colors.with_opacity(0.35, PRIMARY_BLUE)),
            ),
            ft.Container(height=14),
            ft.Text("Verify your email", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ft.Container(height=4),
            verify_email_text,
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=0,
        width=400,
        visible=False,
    )

    ca_resend_row = build_resend_code_control(
        on_click=on_resend_code,
        label_color=TEXT_TERTIARY,
        action_color=PRIMARY_BLUE,
        visible=False,
    )

    ca_or_divider = or_divider()

    ca_bottom_row = ft.Row(
        [
            ft.Text("Already have an account?", size=13, color=TEXT_SECONDARY),
            ft.TextButton(
                "Sign in",
                style=ft.ButtonStyle(color=PRIMARY_BLUE, padding=ft.padding.all(0)),
                on_click=lambda e: handle_go_to_sign_in(e),
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=4,
        visible=True,
    )

    create_account_form = ft.Column(
        [
            ca_back_link,
            ft.Container(height=8),
            ca_step1_header,
            ca_step2_header,
            ft.Container(height=22),
            google_btn_signup,
            ft.Container(height=18),
            ca_or_divider,
            ft.Container(height=18),
            ca_step1,
            ca_step2,
            ca_error,
            ft.Container(height=14),
            ca_action_button_container,
            ft.Container(height=12),
            ca_resend_row,
            ft.Container(height=20),
            ca_bottom_row,
        ],
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.START,
    )

    container = ft.Container(content=create_account_form)
    return container, ca_email


def main(page: ft.Page, nav=None):
    if page.data is None:
        page.data = {}

    if page.data.get("auth_active") and "auth_controller" in page.data:
        page.data["auth_controller"]["switch_to_create_account"]()
        return

    page.title = "QualCheck Create Account"
    page.window_width = 1180
    page.window_height = 780
    page.window_min_width = 960
    page.window_min_height = 640
    page.window_resizable = True
    page.padding = 0
    page.bgcolor = BG_COLOR
    page.theme_mode = ft.ThemeMode.LIGHT
    page.appbar = None
    page.clean()

    page.data["auth_active"] = True

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

    # --- minimal tab toggle (Sign In / Create Account), matches ui_login.py ---
    tab_signin = ft.Container(
        content=ft.Text("Sign In", size=13, weight=ft.FontWeight.W_500, color=TEXT_TERTIARY),
        padding=ft.padding.only(bottom=10),
        on_click=lambda e: on_go_to_sign_in(e),
    )
    tab_create = ft.Container(
        content=ft.Text("Create Account", size=13, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
        padding=ft.padding.only(bottom=10),
        on_click=lambda e: on_go_to_create_account(e),
    )
    ind_signin = ft.Container(height=2, width=52, bgcolor="transparent")
    ind_create = ft.Container(height=2, width=110, bgcolor=PRIMARY_BLUE)
    tab_row = ft.Row(
        [
            ft.Column([tab_signin, ind_signin], spacing=0),
            ft.Column([tab_create, ind_create], spacing=0),
        ],
        spacing=28,
    )

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
        form_wrapper.content = sign_in_holder["container"]
        form_wrapper.opacity = 1
        page.update()

        switching_lock["active"] = False

    def switch_to_create_account():
        if switching_lock["active"]:
            return
        switching_lock["active"] = True

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

    from screens.ui_login import build_left_panel
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