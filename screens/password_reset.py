import flet as ft

try:
    from database.auth import send_password_reset_email
except ModuleNotFoundError:
    def send_password_reset_email(email: str):
        return False, "Database not available"


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

    header = ft.Row(
        [
            ft.Container(
                content=ft.Text("Q", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.BLUE_500,
                width=38,
                height=38,
                border_radius=8,
                alignment=ft.alignment.center,
                shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLUE_500, offset=ft.Offset(0, 0), spread_radius=2),
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

    message = ft.Text("", size=12, color=ft.Colors.RED_400, visible=False)
    email_field = ft.TextField(
        hint_text="you@university.edu",
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

    def go_back(e):
        if nav and hasattr(nav, "navigate_to_login"):
            nav.navigate_to_login()

    def send_reset(e):
        if not email_field.value:
            message.value = "Please enter your email address."
            message.color = ft.Colors.RED_400
            message.visible = True
            page.update()
            return

        success, response_message = send_password_reset_email(email_field.value)
        message.value = response_message
        message.color = ft.Colors.GREEN_400 if success else ft.Colors.RED_400
        message.visible = True
        page.update()

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
                    content=ft.Icon(ft.Icons.MAIL_OUTLINE_ROUNDED, color=ft.Colors.BLUE_300, size=28),
                    width=52,
                    height=52,
                    alignment=ft.alignment.center,
                    border_radius=26,
                    bgcolor="#17395f",
                    border=ft.border.all(1, "#245083"),
                ),
                ft.Container(height=18),
                ft.Text("Forgot your password?", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER),
                ft.Text(
                    "Enter your email and we’ll send a reset message.",
                    size=13,
                    color="#8b9bb4",
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=18),
                message,
                ft.Container(height=14),
                ft.Text("Email address", size=13, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE),
                ft.Container(height=4),
                email_field,
                ft.Container(height=14),
                ft.ElevatedButton(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.MAIL_OUTLINE, size=16, color=ft.Colors.WHITE),
                            ft.Text("Send Reset Code", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    width=400,
                    height=46,
                    bgcolor=ft.Colors.BLUE_600,
                    color=ft.Colors.WHITE,
                    on_click=send_reset,
                ),
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

    blob1 = ft.Container(width=600, height=600, gradient=ft.RadialGradient(colors=[ft.Colors.with_opacity(0.12, ft.Colors.BLUE_400), ft.Colors.with_opacity(0.0, ft.Colors.BLUE_400)], stops=[0.0, 1.0]), left=-100, top=-100)
    blob2 = ft.Container(width=800, height=800, gradient=ft.RadialGradient(colors=[ft.Colors.with_opacity(0.08, ft.Colors.CYAN_400), ft.Colors.with_opacity(0.0, ft.Colors.CYAN_400)], stops=[0.0, 1.0]), right=-200, bottom=-200)

    page.add(
        ft.Stack(
            [
                blob1,
                blob2,
                ft.Column(
                    [
                        ft.Container(height=120),
                        card,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                ),
            ],
            expand=True,
        )
    )