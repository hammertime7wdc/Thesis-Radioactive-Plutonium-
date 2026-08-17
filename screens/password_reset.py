import re
import math
import time
import threading
import flet as ft

try:
    from database.auth import send_password_reset_email, reset_password_with_token
except ModuleNotFoundError:
    def send_password_reset_email(email: str):
        return False, "Database not available"
    def reset_password_with_token(token: str, new_password: str):
        return False, "Database not available"


def validate_password(password: str) -> tuple[bool, str]:
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


def build_reset_password_container(page: ft.Page, nav=None, on_go_to_sign_in=None):
    def go_back(e=None):
        if on_go_to_sign_in:
            on_go_to_sign_in(e)
        elif page.data and page.data.get("auth_active") and "auth_controller" in page.data:
            threading.Thread(
                target=page.data["auth_controller"]["switch_to_login"], daemon=True
            ).start()
        elif nav and hasattr(nav, "navigate_to_login"):
            nav.navigate_to_login()

    def tf(hint="", password=False, reveal=False):
        return ft.TextField(
            hint_text=hint,
            password=password,
            can_reveal_password=reveal,
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

    email_field = tf(hint="you@university.edu")
    code_field = tf(hint="Enter the 6-digit code sent to your email")
    new_password = tf(hint="Min. 8 chars: 1 uppercase, 1 number, 1 special", password=True, reveal=True)
    confirm_field = tf(hint="Confirm new password", password=True, reveal=True)

    message = ft.Text("", size=12, color=ft.Colors.RED_400, visible=False)

    header = ft.Row(
        [
            ft.Container(
                content=ft.Text("Q", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.BLUE_500, width=38, height=38, border_radius=8,
                alignment=ft.alignment.center,
                shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLUE_500,
                                    offset=ft.Offset(0, 0), spread_radius=2),
            ),
            ft.Column(
                [
                    ft.Text("QualCheck", size=17, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text("Semantic Evaluation System", size=11, color="#8b9bb4"),
                ],
                spacing=0,
            ),
        ],
        spacing=12,
        alignment=ft.MainAxisAlignment.START,
    )

    step1 = ft.Column(
        [
            ft.Text("Email address", size=13, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE),
            ft.Container(height=4),
            email_field,
            ft.Container(height=8),
        ],
        spacing=0,
        visible=True,
    )

    step2 = ft.Column(
        [
            ft.Text("6-Digit Verification Code", size=13, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE),
            ft.Container(height=4),
            code_field,
            ft.Container(height=8),
            ft.Text("New Password", size=13, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE),
            ft.Container(height=4),
            new_password,
            ft.Container(height=12),
            ft.Text("Confirm New Password", size=13, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE),
            ft.Container(height=4),
            confirm_field,
            ft.Container(height=8),
        ],
        spacing=0,
        visible=False,
    )

    def make_loading_btn(label):
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

    def on_send_reset(e):
        if not email_field.value:
            message.value = "Please enter your email address."
            message.color = ft.Colors.RED_400
            message.visible = True
            page.update()
            return

        action_btn.content = make_loading_btn("Sending code...")
        page.update()

        success, resp = send_password_reset_email(email_field.value)
        if success:
            step1.visible = False
            step2.visible = True
            action_btn.content = make_verify_btn()
            message.value = "Verification code sent to your email."
            message.color = ft.Colors.GREEN_400
        else:
            action_btn.content = make_send_btn()
            message.value = resp
            message.color = ft.Colors.RED_400
        message.visible = True
        page.update()

    def on_verify(e):
        if not code_field.value:
            message.value = "Please enter the verification code."
            message.color = ft.Colors.RED_400
            message.visible = True
            page.update()
            return

        is_valid, pwd_err = validate_password(new_password.value or "")
        if not is_valid:
            message.value = pwd_err
            message.color = ft.Colors.RED_400
            message.visible = True
            page.update()
            return

        if new_password.value != confirm_field.value:
            message.value = "Passwords do not match."
            message.color = ft.Colors.RED_400
            message.visible = True
            page.update()
            return

        action_btn.content = make_loading_btn("Verifying...")
        page.update()

        ok, msg = reset_password_with_token(code_field.value, new_password.value)
        if ok:
            message.value = "Password reset successfully! You can now sign in."
            message.color = ft.Colors.GREEN_400
            step2.visible = False
            step1.visible = True
            action_btn.content = make_send_btn()
            email_field.value = ""
            new_password.value = ""
            confirm_field.value = ""
            code_field.value = ""
        else:
            action_btn.content = make_verify_btn()
            message.value = msg
            message.color = ft.Colors.RED_400
        message.visible = True
        page.update()

    email_field.on_submit = on_send_reset
    code_field.on_submit = on_verify
    new_password.on_submit = on_verify
    confirm_field.on_submit = on_verify

    def make_send_btn():
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.MAIL_OUTLINE, size=16, color=ft.Colors.WHITE),
                    ft.Text("Send Reset Code", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ],
                alignment=ft.MainAxisAlignment.CENTER, spacing=8,
            ),
            width=400, height=46, bgcolor=ft.Colors.BLUE_600, border_radius=8,
            alignment=ft.alignment.center, ink=True,
            on_click=on_send_reset,
        )

    def make_verify_btn():
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=16, color=ft.Colors.WHITE),
                    ft.Text("Verify & Reset Password", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ],
                alignment=ft.MainAxisAlignment.CENTER, spacing=8,
            ),
            width=400, height=46, bgcolor=ft.Colors.BLUE_600, border_radius=8,
            alignment=ft.alignment.center, ink=True,
            on_click=on_verify,
        )

    action_btn = ft.Container(content=make_send_btn())

    reset_form = ft.Column(
        [
            header,
            ft.Container(height=10),
            ft.TextButton(
                "Back to sign in",
                icon=ft.Icons.ARROW_BACK,
                style=ft.ButtonStyle(color="#8b9bb4", padding=ft.padding.all(0)),
                on_click=go_back,
            ),
            ft.Container(height=18),
            ft.Container(
                content=ft.Icon(ft.Icons.LOCK_RESET_OUTLINED, color=ft.Colors.BLUE_300, size=28),
                width=52, height=52, alignment=ft.alignment.center,
                border_radius=26, bgcolor="#17395f", border=ft.border.all(1, "#245083"),
            ),
            ft.Container(height=18),
            ft.Text(
                "Reset your password",
                size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE,
            ),
            ft.Text(
                "Fill in your details, then enter the code we email you.",
                size=13, color="#8b9bb4",
            ),
            ft.Container(height=18),
            message,
            ft.Container(height=6),
            step1,
            step2,
            action_btn,
        ],
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.START,
    )

    return ft.Container(
        content=reset_form,
        padding=ft.padding.symmetric(horizontal=40, vertical=30),
    )


def main(page: ft.Page, nav=None):
    if page.data is None:
        page.data = {}

    if page.data.get("auth_active") and "auth_controller" in page.data:
        page.data["auth_controller"]["switch_to_reset_password"]()
        return

    page.title = "QualCheck - Reset Password"
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
        width=600, height=600,
        gradient=ft.RadialGradient(
            colors=[ft.Colors.with_opacity(0.12, ft.Colors.BLUE_400),
                    ft.Colors.with_opacity(0.0,  ft.Colors.BLUE_400)],
            stops=[0.0, 1.0],
        ),
        left=-100, top=-100,
    )
    blob2 = ft.Container(
        width=800, height=800,
        gradient=ft.RadialGradient(
            colors=[ft.Colors.with_opacity(0.08, ft.Colors.CYAN_400),
                    ft.Colors.with_opacity(0.0,  ft.Colors.CYAN_400)],
            stops=[0.0, 1.0],
        ),
        right=-200, bottom=-200,
    )
    blob3 = ft.Container(
        width=500, height=500,
        gradient=ft.RadialGradient(
            colors=[ft.Colors.with_opacity(0.10, ft.Colors.PURPLE_400),
                    ft.Colors.with_opacity(0.0,  ft.Colors.PURPLE_400)],
            stops=[0.0, 1.0],
        ),
        left=100, bottom=-100,
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
            threading.Thread(target=lambda: login_main(page, nav), daemon=True).start()

    def on_go_to_create_account(e=None):
        if page.data and page.data.get("auth_active") and "auth_controller" in page.data:
            threading.Thread(
                target=page.data["auth_controller"]["switch_to_create_account"],
                daemon=True,
            ).start()

    reset_container = build_reset_password_container(page, nav, on_go_to_sign_in)
    sign_in_holder = {"container": None, "email_ref": None}
    create_account_holder = {"container": None}
    switching_lock = {"active": False}

    form_wrapper = ft.Container(
        content=reset_container,
        animate_opacity=ft.Animation(180, ft.AnimationCurve.EASE_IN_OUT),
        opacity=1,
    )

    tab_signin = ft.Container(
        content=ft.Text("Sign In", size=14, weight=ft.FontWeight.W_500, color="#6b7f99", text_align=ft.TextAlign.CENTER),
        padding=ft.padding.symmetric(horizontal=24, vertical=14),
        bgcolor="#161f2e", expand=True, alignment=ft.alignment.center,
        border_radius=ft.border_radius.only(top_left=16),
        on_click=lambda e: on_go_to_sign_in(e), ink=True,
    )
    tab_create = ft.Container(
        content=ft.Text("Create Account", size=14, weight=ft.FontWeight.W_500, color="#6b7f99", text_align=ft.TextAlign.CENTER),
        padding=ft.padding.symmetric(horizontal=24, vertical=14),
        bgcolor="#161f2e", expand=True, alignment=ft.alignment.center,
        border_radius=ft.border_radius.only(top_right=16),
        on_click=lambda e: on_go_to_create_account(e), ink=True,
    )
    ind_signin = ft.Container(height=2, bgcolor="transparent", expand=True)
    ind_create = ft.Container(height=2, bgcolor="transparent", expand=True)
    tab_row = ft.Row(
        [
            ft.Column([tab_signin, ind_signin], spacing=0, expand=True),
            ft.Column([tab_create, ind_create], spacing=0, expand=True),
        ],
        spacing=0, expand=True, visible=False,
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

        if create_account_holder["container"] is None:
            from screens.ui_create_account import build_create_account_container
            ca_cont, _ = build_create_account_container(page, nav, on_go_to_sign_in)
            create_account_holder["container"] = ca_cont

        form_wrapper.animate_opacity = ft.Animation(180, ft.AnimationCurve.EASE_IN_OUT)
        form_wrapper.opacity = 0
        page.update()
        time.sleep(0.18)

        tab_row.visible = True
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

    def switch_to_reset_password():
        if switching_lock["active"]:
            return
        switching_lock["active"] = True

        form_wrapper.animate_opacity = ft.Animation(180, ft.AnimationCurve.EASE_IN_OUT)
        form_wrapper.opacity = 0
        page.update()
        time.sleep(0.18)

        tab_row.visible = False
        page.title = "QualCheck - Reset Password"
        form_wrapper.content = reset_container
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
                ft.Container(height=1, bgcolor="#1e2f46", visible=False),
                form_wrapper,
            ],
            spacing=0,
        ),
        bgcolor="#1c2c44",
        border_radius=16,
        width=480,
        border=ft.border.all(1, "#243447"),
        shadow=ft.BoxShadow(blur_radius=40, color="#070f1a", offset=ft.Offset(0, 12), spread_radius=0),
    )

    page_fade = ft.Container(
        content=ft.Stack(
            [
                blob1, blob2, blob3,
                ft.Column(
                    [
                        ft.Container(height=60),
                        card,
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
    ft.app(target=main)