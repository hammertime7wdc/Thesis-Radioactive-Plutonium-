import flet as ft

from utils.utils import PRIMARY_BLUE, TEXT_WHITE


def show_snackbar(page: ft.Page, message: str, bgcolor: str = PRIMARY_BLUE) -> None:
    """Display a consistent snackbar using the installed Flet API."""
    page.open(
        ft.SnackBar(
            content=ft.Text(message, color=TEXT_WHITE),
            bgcolor=bgcolor,
        )
    )
