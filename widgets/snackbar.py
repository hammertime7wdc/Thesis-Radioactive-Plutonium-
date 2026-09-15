import flet as ft

from utils.utils import ERROR, PRIMARY_BLUE, PRIMARY_BLUE_DARK, TEXT_WHITE


def show_snackbar(page: ft.Page, message: str, bgcolor: str = PRIMARY_BLUE) -> None:
    """Display a compact, consistent status notification."""
    is_error = bgcolor == ERROR
    surface_color = ERROR if is_error else PRIMARY_BLUE_DARK
    icon = ft.Icons.ERROR_OUTLINE if is_error else ft.Icons.CHECK_CIRCLE_OUTLINE

    page.open(
        ft.SnackBar(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Icon(icon, size=18, color=surface_color),
                        width=28,
                        height=28,
                        border_radius=14,
                        bgcolor=TEXT_WHITE,
                        alignment=ft.alignment.center,
                    ),
                    ft.Text(
                        message,
                        color=TEXT_WHITE,
                        size=13,
                        weight=ft.FontWeight.W_600,
                        expand=True,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=surface_color,
            behavior=ft.SnackBarBehavior.FLOATING,
            show_close_icon=True,
            close_icon_color=TEXT_WHITE,
            duration=3500,
            margin=ft.margin.only(left=20, right=20, bottom=20),
            padding=ft.padding.symmetric(horizontal=14, vertical=10),
            width=440,
            elevation=6,
            shape=ft.RoundedRectangleBorder(radius=12),
        )
    )
