import flet as ft
from navigation.navigation import Navigation


def main(page: ft.Page):
    page.title = "QualCheck"
    page.window_width = 1200
    page.window_height = 800
    page.padding = 0
    page.bgcolor = "#0f172a"
    page.theme_mode = ft.ThemeMode.DARK

    # Initialize navigation
    nav = Navigation(page)
    
    # Start with login screen
    nav.navigate_to_login()


if __name__ == "__main__":
    ft.app(target=main)
