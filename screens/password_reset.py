import re
import math
import time
import threading
import flet as ft
from utils.resend_control import build_resend_code_control

try:
    from database.auth import (
        resend_password_reset_email,
        reset_password_with_token,
        send_password_reset_email,
    )
except ModuleNotFoundError:
    def send_password_reset_email(email: str):
        return False, "Database not available"

    def resend_password_reset_email(email: str):
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
    # State variable for tracking current step (1: Email, 2: Inbox Check, 3: Reset Form)
    current_step = {"val": 1}
    processing = {"value": False}

    def navigate_back(e=None):
        if current_step["val"] in (2, 3):
            # Step back to email input view
            current_step["val"] = 1
            show_step(1)
        else:
            # Return to sign in screen
            if on_go_to_sign_in:
                on_go_to_sign_in(e)
            elif page.data and page.data.get("auth_active") and "auth_controller" in page.data:
                threading.Thread(
                    target=page.data["auth_controller"]["switch_to_login"], daemon=True
                ).start()
            elif nav and hasattr(nav, "navigate_to_login"):
                nav.navigate_to_login()

    def tf(hint="", password=False, reveal=False, text_align=ft.TextAlign.LEFT):
        return ft.TextField(
            hint_text=hint,
            password=password,
            can_reveal_password=reveal,
            width=380,
            height=44,
            bgcolor="#1b293e",
            border_color="#2a3d58",
            focused_border_color=ft.Colors.BLUE_400,
            text_size=14,
            text_align=text_align,
            content_padding=ft.padding.symmetric(horizontal=14, vertical=10),
            hint_style=ft.TextStyle(color="#546a8a"),
            color=ft.Colors.WHITE,
            border_radius=8,
        )

    # Input Fields
    email_field = tf(hint="you@university.edu")
    code_field = ft.TextField(
        hint_text="• • • • • •",
        width=380,
        height=44,
        bgcolor="#1b293e",
        border_color="#2a3d58",
        focused_border_color=ft.Colors.BLUE_400,
        text_size=14,
        text_align=ft.TextAlign.CENTER,
        content_padding=ft.padding.symmetric(horizontal=14, vertical=10),
        hint_style=ft.TextStyle(color="#546a8a"),
        color=ft.Colors.WHITE,
        border_radius=8,
        max_length=6,
        input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]"),
    )
    new_password = tf(
        hint="Min. 8 chars: 1 lowercase, 1 uppercase, 1 number, 1 special",
        password=True,
        reveal=True,
    )
    confirm_field = tf(hint="••••••••", password=True, reveal=True)

    message = ft.Text("", size=12, color=ft.Colors.RED_400, visible=False, text_align=ft.TextAlign.CENTER)

    # Top Brand Header
    header = ft.Row(
        [
            ft.Container(
                content=ft.Text("Q", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.BLUE_600,
                width=38,
                height=38,
                border_radius=8,
                alignment=ft.alignment.center,
                shadow=ft.BoxShadow(
                    blur_radius=10, color=ft.Colors.with_opacity(0.4, ft.Colors.BLUE_500),
                    offset=ft.Offset(0, 2)
                ),
            ),
            ft.Column(
                [
                    ft.Text("QualCheck", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.Text("Semantic Evaluation System", size=11, color="#6c82a3"),
                ],
                spacing=0,
            ),
        ],
        spacing=12,
        alignment=ft.MainAxisAlignment.START,
        width=380,
    )

    back_btn_text = ft.Text("Back to sign in", size=13, color="#8096b5")
    back_button = ft.GestureDetector(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.ARROW_BACK, size=14, color="#8096b5"),
                back_btn_text,
            ],
            spacing=6,
            width=380,
        ),
        on_tap=navigate_back,
    )

    # Helper function for primary action buttons
    def primary_button(text: str, icon=None, on_click=None):
        def button_content():
            controls = []
            if icon:
                controls.append(ft.Icon(icon, size=16, color=ft.Colors.WHITE))
            controls.append(ft.Text(text, size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE))
            return ft.Row(controls, alignment=ft.MainAxisAlignment.CENTER, spacing=8)

        button = ft.Container(
            content=button_content(),
            width=380,
            height=44,
            bgcolor="#2563eb",
            border_radius=8,
            alignment=ft.alignment.center,
            ink=True,
            on_click=on_click,
        )
        button.data = {"default_content": button_content, "default_handler": on_click}
        return button

    def set_button_loading(button, label: str, is_loading: bool):
        if is_loading:
            button.content = ft.Row(
                [
                    ft.ProgressRing(width=16, height=16, stroke_width=2, color=ft.Colors.WHITE),
                    ft.Text(label, size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            )
            button.on_click = None
        else:
            button.content = button.data["default_content"]()
            button.on_click = button.data["default_handler"]

    def set_resend_loading(is_loading: bool):
        resend_link.disabled = is_loading
        resend_link.text = "Resending code..." if is_loading else "Didn't receive it? Resend"

    # Icon Badges
    def make_badge(icon, bg_color="#1d2e47", icon_color="#3b82f6"):
        return ft.Container(
            content=ft.Icon(icon, color=icon_color, size=24),
            width=52,
            height=52,
            alignment=ft.alignment.center,
            border_radius=26,
            bgcolor=bg_color,
            border=ft.border.all(1, ft.Colors.with_opacity(0.3, icon_color)),
        )

    # ------------------ STEP 1: Enter Email ------------------
    step1_btn = primary_button("Send Reset Code", icon=ft.Icons.MAIL_OUTLINE)

    step1 = ft.Column(
        [
            ft.Container(height=12),
            make_badge(ft.Icons.EMAIL_OUTLINED, bg_color="#192a42", icon_color="#3b82f6"),
            ft.Container(height=14),
            ft.Text("Forgot your password?", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ft.Text("Enter your email and we'll send you a reset code.", size=13, color="#8096b5", text_align=ft.TextAlign.CENTER),
            ft.Container(height=20),
            ft.Column(
                [
                    ft.Text("Email address", size=13, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE),
                    ft.Container(height=4),
                    email_field,
                ],
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.START,
            ),
            ft.Container(height=16),
            step1_btn,
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        width=380,
        spacing=0,
        visible=True,
    )

    # ------------------ STEP 2: Inbox Notice ------------------
    sent_email_text = ft.Text("", size=13, color="#8096b5", text_align=ft.TextAlign.CENTER)

    step2_btn = primary_button("Enter reset code", icon=ft.Icons.VPN_KEY_OUTLINED)

    resend_link = build_resend_code_control(
        on_click=None,
        label_color="#8096b5",
        action_color="#60a5fa",
    )

    step2 = ft.Column(
        [
            ft.Container(height=12),
            make_badge(ft.Icons.MAIL_OUTLINE, bg_color="#192a42", icon_color="#3b82f6"),
            ft.Container(height=14),
            ft.Text("Forgot your password?", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ft.Text("Enter your email and we'll send you a reset code.", size=13, color="#8096b5", text_align=ft.TextAlign.CENTER),
            ft.Container(height=20),
            ft.Container(
                content=ft.Icon(ft.Icons.CHECK, color="#10b981", size=18),
                width=36,
                height=36,
                alignment=ft.alignment.center,
                border_radius=18,
                bgcolor="#12352b",
            ),
            ft.Container(height=14),
            ft.Text("Check your inbox", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ft.Container(height=6),
            sent_email_text,
            ft.Container(height=20),
            step2_btn,
            ft.Container(height=12),
            resend_link,
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        width=380,
        spacing=0,
        visible=False,
    )

    # ------------------ STEP 3: Reset Password Form ------------------
    step3_btn = primary_button("Reset Password", icon=ft.Icons.VPN_KEY_OUTLINED)

    step3 = ft.Column(
        [
            ft.Container(height=12),
            make_badge(ft.Icons.VPN_KEY_OUTLINED, bg_color="#192a42", icon_color="#3b82f6"),
            ft.Container(height=14),
            ft.Text("Reset your password", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ft.Text("Enter the 6-digit code from your email and choose a new password.", size=13, color="#8096b5", text_align=ft.TextAlign.CENTER),
            ft.Container(height=20),
            ft.Column(
                [
                    ft.Text("6-digit code", size=13, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE),
                    ft.Container(height=4),
                    code_field,
                    ft.Container(height=12),
                    ft.Text("New password", size=13, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE),
                    ft.Container(height=4),
                    new_password,
                    ft.Container(height=12),
                    ft.Text("Confirm new password", size=13, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE),
                    ft.Container(height=4),
                    confirm_field,
                ],
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.START,
            ),
            ft.Container(height=20),
            step3_btn,
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        width=380,
        spacing=0,
        visible=False,
    )

    # View Controller Logic
    def show_step(step_number: int):
        current_step["val"] = step_number
        step1.visible = (step_number == 1)
        step2.visible = (step_number == 2)
        step3.visible = (step_number == 3)

        back_btn_text.value = "Back" if step_number == 3 else "Back to sign in"
        message.visible = False
        page.update()

    # Handlers
    def on_send_reset(e):
        if processing["value"]:
            return
        if not email_field.value:
            message.value = "Please enter your email address."
            message.color = ft.Colors.RED_400
            message.visible = True
            page.update()
            return

        processing["value"] = True
        set_button_loading(step1_btn, "Sending code...", True)
        page.update()
        try:
            success, resp = send_password_reset_email(email_field.value)
            if success:
                sent_email_text.spans = [
                    ft.TextSpan("We sent a reset code to "),
                    ft.TextSpan(email_field.value, ft.TextStyle(weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)),
                    ft.TextSpan(". It expires in 5 minutes."),
                ]
                show_step(2)
            else:
                message.value = resp
                message.color = ft.Colors.RED_400
                message.visible = True
        finally:
            processing["value"] = False
            set_button_loading(step1_btn, "Sending code...", False)
            page.update()

    def on_go_to_step_3(e):
        show_step(3)

    def on_resend(e):
        if processing["value"]:
            return
        if not email_field.value:
            message.value = "Please enter your email address."
            message.color = ft.Colors.RED_400
            message.visible = True
            page.update()
            return

        processing["value"] = True
        set_resend_loading(True)
        page.update()
        try:
            success, resp = resend_password_reset_email(email_field.value)
            message.value = "A new verification code was sent to your email." if success else resp
            message.color = ft.Colors.GREEN_400 if success else ft.Colors.RED_400
            message.visible = True
        finally:
            processing["value"] = False
            set_resend_loading(False)
            page.update()

    def on_verify(e):
        if processing["value"]:
            return
        if not code_field.value:
            message.value = "Please enter the verification code."
            message.color = ft.Colors.RED_400
            message.visible = True
            page.update()
            return
        if len(code_field.value.strip()) != 6:
            message.value = "Please enter the 6-digit verification code."
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

        processing["value"] = True
        set_button_loading(step3_btn, "Resetting password...", True)
        page.update()
        try:
            ok, msg = reset_password_with_token(code_field.value, new_password.value)
            if ok:
                message.value = "Password reset successfully! You can now sign in."
                message.color = ft.Colors.GREEN_400
                message.visible = True
                page.update()
                time.sleep(1.5)
                navigate_back()
            else:
                message.value = msg
                message.color = ft.Colors.RED_400
                message.visible = True
        finally:
            processing["value"] = False
            set_button_loading(step3_btn, "Reset Password", False)
            page.update()

    # Wire up button callbacks
    step1_btn.on_click = on_send_reset
    step2_btn.on_click = on_go_to_step_3
    step3_btn.on_click = on_verify
    resend_link.controls[1].on_click = on_resend

    email_field.on_submit = on_send_reset
    code_field.on_submit = on_verify
    new_password.on_submit = on_verify
    confirm_field.on_submit = on_verify

    reset_form = ft.Column(
        [
            header,
            ft.Container(height=16),
            back_button,
            ft.Container(height=10),
            message,
            step1,
            step2,
            step3,
        ],
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        width=380,
    )

    return ft.Container(
        content=reset_form,
        padding=ft.padding.symmetric(horizontal=35, vertical=32),
    )


def main(page: ft.Page, nav=None):
    if page.data is None:
        page.data = {}

    if page.data.get("auth_active") and "auth_controller" in page.data:
        page.data["auth_controller"]["switch_to_reset_password"]()
        return

    page.title = "QualCheck - Reset Password"
    page.window_width = 900
    page.window_height = 800
    page.window_min_width = 900
    page.window_min_height = 800
    page.window_resizable = True
    page.padding = 0
    page.bgcolor = "#0b1523"
    page.theme_mode = ft.ThemeMode.DARK
    page.appbar = None
    page.clean()

    # Background ambient lighting blobs
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

    page.data["auth_active"] = True

    def animate_blobs():
        t = 0.0
        while page.data.get("auth_active", False):
            try:
                blob1.top = -100 + 60 * math.sin(t)
                blob1.left = -100 + 80 * math.cos(t * 0.8)
                blob2.bottom = -200 + 80 * math.cos(t * 0.9)
                blob2.right = -200 + 100 * math.sin(t * 0.7)
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

    reset_container = build_reset_password_container(page, nav, on_go_to_sign_in)

    # Card component
    card = ft.Container(
        content=reset_container,
        bgcolor="#152234",
        border_radius=16,
        width=450,
        border=ft.border.all(1, "#213248"),
        shadow=ft.BoxShadow(blur_radius=40, color="#040912", offset=ft.Offset(0, 12), spread_radius=0),
    )

    # Bottom features footer
    footer_features = ft.Row(
        [
            ft.Column(
                [
                    ft.Text("BERT", size=13, weight=ft.FontWeight.BOLD, color="#3b82f6"),
                    ft.Text("Embeddings", size=11, color="#536988"),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2,
            ),
            ft.Column(
                [
                    ft.Text("Cosine", size=13, weight=ft.FontWeight.BOLD, color="#3b82f6"),
                    ft.Text("Similarity", size=11, color="#536988"),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2,
            ),
            ft.Column(
                [
                    ft.Text("Rubric", size=13, weight=ft.FontWeight.BOLD, color="#3b82f6"),
                    ft.Text("Guided", size=11, color="#536988"),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2,
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=36,
    )

    page_content = ft.Stack(
        [
            blob1, blob2,
            ft.Column(
                [
                    ft.Container(height=40),
                    card,
                    ft.Container(height=28),
                    footer_features,
                    ft.Container(height=30),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
        ],
        expand=True,
    )

    page.add(page_content)


if __name__ == "__main__":
    ft.app(target=main)