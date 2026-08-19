import flet as ft


def build_resend_code_control(on_click, label_color: str, action_color: str, visible: bool = True):
    """Shared visual treatment for existing resend-code actions."""
    return ft.Row(
        [
            ft.Text("Didn't receive it?", size=13, color=label_color),
            ft.TextButton(
                "Resend code",
                icon=ft.Icons.REFRESH,
                style=ft.ButtonStyle(
                    color=action_color,
                    padding=ft.padding.all(0),
                ),
                on_click=on_click,
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=4,
        visible=visible,
    )
