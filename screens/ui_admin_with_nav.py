import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import flet as ft
from navigation.admin_navigation import AdminNavigation
from utils.utils import BG_COLOR


def main(page: ft.Page):
    page.title = "QualCheck Admin Panel"
    page.window_width = 1200
    page.window_height = 800
    page.padding = 0
    page.bgcolor = BG_COLOR
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO

    # Create admin navigation
    admin_nav = AdminNavigation(page)
    
    # Create app bar
    admin_nav.create_admin_app_bar()
    
    # Create secondary navigation bar with tabs
    admin_nav.create_secondary_nav_bar()
    
    # Navigate to users tab by default
    admin_nav.navigate_to_users()


if __name__ == "__main__":
    ft.app(target=main)