import re
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


def main(page: ft.Page, nav=None):
    page.title = "QualCheck - Reset Password"
    page.window_width = 900
    page.window_height = 780
    page.window_min_width = 900
    page.window_min_height = 780
    page.window_resizable = True
    page.padding = 0
    page.bgcolor = "#0f1e30"
    page.theme_mode = ft.ThemeMode.DARK
    page.clean()

    # ── Shared field style ────────────────────────────────────────
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

    # ── Fields ───────────────────────────────────────────────────
    email_field    = tf(hint="you@university.edu")
    code_field     = tf(hint="Enter the 6-digit code sent to your email")
    new_password   = tf(hint="Min. 8 chars: 1 uppercase, 1 number, 1 special", password=True, reveal=True)
    confirm_field  = tf(hint="Confirm new password", password=True, reveal=True)

    message = ft.Text("", size=12, color=ft.Colors.RED_400, visible=False)

    # ── Brand header ─────────────────────────────────────────────
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

    def go_back(e):
        if nav and hasattr(nav, "navigate_to_login"):
            nav.navigate_to_login()

    # ── Step 1 — email + passwords ───────────────────────────────
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

    # ── Step 2 — verification code only ─────────────────────────
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

    # ── Handlers (defined BEFORE the buttons that reference them) ─
    def on_send_reset(e):
        # Validate email first, then send the reset code by SMTP.
        if not email_field.value:
            message.value = "Please enter your email address."
            message.color = ft.Colors.RED_400
            message.visible = True
            page.update()
            return

        success, resp = send_password_reset_email(email_field.value)
        if success:
            # Switch to step 2 inline — no dialog
            step1.visible = False
            step2.visible = True
            action_btn.content = make_verify_btn()
            message.value = "Verification code sent to your email."
            message.color = ft.Colors.GREEN_400
        else:
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

        ok, msg = reset_password_with_token(code_field.value, new_password.value)
        if ok:
            message.value = "Password reset successfully! You can now sign in."
            message.color = ft.Colors.GREEN_400
            # Reset back to step 1 cleanly
            step2.visible = False
            step1.visible = True
            action_btn.content = make_send_btn()
            email_field.value = ""
            new_password.value = ""
            confirm_field.value = ""
            code_field.value = ""
        else:
            message.value = msg
            message.color = ft.Colors.RED_400
        message.visible = True
        page.update()

    # ── Action button (swaps between steps) ──────────────────────
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

    # ── Card ─────────────────────────────────────────────────────
    card = ft.Container(
        content=ft.Column(
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
        ),
        bgcolor="#1c2c44",
        border_radius=16,
        width=480,
        padding=ft.padding.symmetric(horizontal=40, vertical=30),
        border=ft.border.all(1, "#243447"),
        shadow=ft.BoxShadow(blur_radius=40, color="#070f1a", offset=ft.Offset(0, 12), spread_radius=0),
    )

    # ── Background blobs ─────────────────────────────────────────
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

    page.add(
        ft.Stack(
            [
                blob1, blob2,
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
        )
    )


if __name__ == "__main__":
    ft.app(target=main)