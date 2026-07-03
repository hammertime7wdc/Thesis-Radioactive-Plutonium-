import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import flet as ft
from screens.ui_admin import main as admin_main
from screens.ui_admin_settings_audit import main as settings_audit_main
from screens.ui_admin_submissions import main as submissions_main
from screens.ui_account import main as account_main
from utils.utils import (
    CARD_BG_COLOR, PRIMARY_BLUE, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_TERTIARY, TEXT_WHITE,
    BUTTON_PRIMARY_BG, BUTTON_PRIMARY_TEXT, BUTTON_SECONDARY_BG, BUTTON_SECONDARY_TEXT,
    BORDER_COLOR
)
from services.session_manager import get_current_user


class AdminNavigation:
    """Navigation handler for Admin Panel sections"""
    
    def __init__(self, page: ft.Page, parent_nav=None):
        self.page = page
        self.parent_nav = parent_nav
        self.current_tab = 0
        self.main_content = None
        self.is_evaluation_mode = False
        self.is_admin_mode = False
        self.app_bar = None
    
    def create_admin_app_bar(self):
        """Create shared app bar for admin screens"""
        # Get current user info
        user = get_current_user()
        user_name = "User"
        user_initials = "U"
        
        if user and user.user:
            email = user.user.email
            # Extract name from email or use email as name
            user_name = email.split("@")[0].replace(".", " ").title()
            # Generate initials
            name_parts = user_name.split()
            if len(name_parts) >= 2:
                user_initials = (name_parts[0][0] + name_parts[1][0]).upper()
            else:
                user_initials = user_name[:2].upper()
        
        logo = ft.Container(
            content=ft.Text("Q", size=20, weight=ft.FontWeight.BOLD, color=TEXT_WHITE),
            bgcolor=PRIMARY_BLUE,
            width=36,
            height=36,
            border_radius=8,
            alignment=ft.alignment.center,
            shadow=ft.BoxShadow(
                blur_radius=8,
                spread_radius=0,
                color=PRIMARY_BLUE,
                offset=ft.Offset(0, 2),
            ),
        )

        brand = ft.Column(
            [
                ft.Text("QualCheck", size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Text("Rubric-Guided Semantic Evaluation System", size=11, color=TEXT_SECONDARY),
            ],
            spacing=2,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        def on_admin(e):
            pass  # Already on admin

        def on_new_evaluation(e):
            if self.parent_nav:
                self.parent_nav.is_evaluation_mode = False
                self.parent_nav.navigate_to_short_answer()
            else:
                from navigation.navigation import Navigation
                main_nav = Navigation(self.page)
                main_nav.navigate_to_short_answer()

        def on_dashboard(e):
            if self.parent_nav:
                self.parent_nav.navigate_to_dashboard()
            else:
                from navigation.navigation import Navigation
                main_nav = Navigation(self.page)
                main_nav.navigate_to_dashboard()

        self.app_bar = ft.AppBar(
            leading=ft.Row([ft.Container(width=12), logo, ft.Container(width=12), brand], alignment=ft.MainAxisAlignment.CENTER),
            leading_width=320,
            bgcolor=CARD_BG_COLOR,
            toolbar_height=70,
            center_title=False,
            title=ft.Row(
                [
                    ft.Container(width=20),
                    # Admin button (active) - solid blue button
                    ft.Container(
                        content=ft.Text("Admin", size=13, weight=ft.FontWeight.W_600, color=TEXT_WHITE),
                        padding=ft.padding.symmetric(horizontal=16, vertical=10),
                        bgcolor=PRIMARY_BLUE,
                        border_radius=8,
                        alignment=ft.alignment.center,
                        on_click=on_admin,
                    ),
                    ft.Container(width=8),
                    # New Evaluation - light gray button
                    ft.Container(
                        content=ft.Text("New Evaluation", size=13, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY),
                        padding=ft.padding.symmetric(horizontal=16, vertical=10),
                        bgcolor="#f1f5f9",
                        border_radius=8,
                        alignment=ft.alignment.center,
                        on_click=on_new_evaluation,
                    ),
                    ft.Container(width=8),
                    # Dashboard - light gray button
                    ft.Container(
                        content=ft.Text("Dashboard", size=13, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY),
                        padding=ft.padding.symmetric(horizontal=16, vertical=10),
                        bgcolor="#f1f5f9",
                        border_radius=8,
                        alignment=ft.alignment.center,
                        on_click=on_dashboard,
                    ),
                ]
            ),
            actions=[
                ft.Row(
                    [
                        # Vertical separator
                        ft.Container(
                            width=1,
                            height=32,
                            bgcolor="#e2e8f0",
                        ),
                        ft.Container(width=16),
                        # Clickable flat profile container (no border, no shadow)
                        ft.Container(
                            content=ft.Row(
                                [
                                    # Avatar with initials (AD) - light blue background, blue text
                                    ft.Container(
                                        content=ft.Text(user_initials, size=12, weight=ft.FontWeight.BOLD, color=PRIMARY_BLUE),
                                        width=32,
                                        height=32,
                                        border_radius=16,
                                        bgcolor="#eff6ff",
                                        alignment=ft.alignment.center,
                                    ),
                                    ft.Container(width=10),
                                    ft.Column(
                                        [
                                            ft.Text(user_name, size=13, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY),
                                            ft.Text("Admin", size=11, color=TEXT_SECONDARY),
                                        ],
                                        spacing=0,
                                        alignment=ft.MainAxisAlignment.CENTER,
                                    ),
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ink=True,
                            on_click=lambda e: self.navigate_to_account(),
                            border_radius=8,
                            padding=ft.padding.symmetric(horizontal=4, vertical=4),
                        ),
                        ft.Container(width=16),
                        # Logout button - outside of profile
                        ft.IconButton(
                            icon=ft.Icons.LOGOUT,
                            icon_size=20,
                            icon_color=TEXT_TERTIARY,
                            tooltip="Logout",
                            on_click=lambda e: self.navigate_to_login()
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(width=16),
            ],
        )
        self.page.appbar = self.app_bar

    def create_secondary_nav_bar(self):
        """Create secondary navigation bar with tabs"""
        def on_tab_change(e):
            self.current_tab = e.control.selected_index
            if self.current_tab == 0:
                self.navigate_to_users()
            elif self.current_tab == 1:
                self.navigate_to_analytics()
            elif self.current_tab == 2:
                self.navigate_to_submissions()
            elif self.current_tab == 3:
                self.navigate_to_settings_audit()

        # Custom tab styling
        def create_tab(text, icon, index):
            is_active = index == self.current_tab
            return ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(icon, size=18, color=TEXT_WHITE if is_active else TEXT_SECONDARY),
                        ft.Container(width=6),
                        ft.Text(text, size=13, weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.W_500, color=TEXT_WHITE if is_active else TEXT_PRIMARY),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                bgcolor=PRIMARY_BLUE if is_active else "#f1f5f9",
                border_radius=8,
                on_click=lambda e, idx=index: self._on_tab_click(idx),
            )

        self.secondary_nav = ft.Container(
            content=ft.Row(
                [
                    create_tab("Users", ft.Icons.PEOPLE_OUTLINE, 0),
                    ft.Container(width=8),
                    create_tab("Analytics", ft.Icons.BAR_CHART_OUTLINED, 1),
                    ft.Container(width=8),
                    create_tab("Submissions", ft.Icons.ARTICLE_OUTLINED, 2),
                    ft.Container(width=8),
                    create_tab("Settings & Audit", ft.Icons.SETTINGS_OUTLINED, 3),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            bgcolor=CARD_BG_COLOR,
            border=ft.border.only(bottom=ft.BorderSide(1, BORDER_COLOR)),
            padding=ft.padding.symmetric(horizontal=32, vertical=12),
            shadow=ft.BoxShadow(
                blur_radius=4,
                spread_radius=0,
                color=TEXT_TERTIARY,
                offset=ft.Offset(0, 1),
            ),
        )

    def _on_tab_click(self, index):
        """Handle tab click"""
        self.current_tab = index
        if index == 0:
            self.navigate_to_users()
        elif index == 1:
            self.navigate_to_analytics()
        elif index == 2:
            self.navigate_to_submissions()
        elif index == 3:
            self.navigate_to_settings_audit()

    def create_admin_header(self):
        """Create admin panel header with title and administrator badge matching the screenshot"""
        # Purple icon container on the left
        shield_icon = ft.Container(
            content=ft.Icon(ft.Icons.SHIELD, size=20, color=TEXT_WHITE),
            width=36,
            height=36,
            bgcolor="#a855f7",
            border_radius=8,
            alignment=ft.alignment.center,
        )

        admin_header = ft.Container(
            content=ft.Row(
                [
                    ft.Row(
                        [
                            shield_icon,
                            ft.Container(width=12),
                            ft.Column(
                                [
                                    ft.Text("Admin Panel", size=22, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                                    ft.Container(height=4),
                                    ft.Text("System administration & analytics", size=13, color=TEXT_SECONDARY),
                                ],
                                spacing=0,
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(expand=True),
                    # Administrator badge in purple on the right
                    ft.Container(
                        content=ft.Text("Administrator", size=12, weight=ft.FontWeight.W_600, color="#7e22ce"),
                        padding=ft.padding.symmetric(horizontal=12, vertical=6),
                        bgcolor="#f3e8ff",
                        border_radius=16,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.symmetric(horizontal=32, vertical=20),
        )
        return admin_header

    def navigate_to_users(self):
        """Navigate to Users tab"""
        self.current_tab = 0
        if not self.is_admin_mode:
            self.page.clean()
            self.page.window_width = 1200
            self.page.window_height = 800
            self.page.padding = 0
            self.page.bgcolor = "#f8fafc"
            self.page.theme_mode = ft.ThemeMode.LIGHT
            self.is_admin_mode = True
            self.create_admin_app_bar()
            self.create_secondary_nav_bar()
            self.page.add(self.secondary_nav)
            admin_header = self.create_admin_header()
            self.page.add(admin_header)
        else:
            # Just replace main content, keep app bar and nav bar
            if self.main_content:
                self.page.remove(self.main_content)
            # Update secondary nav to reflect current tab
            self.create_secondary_nav_bar()
            # Need to replace the secondary nav in the page
            # Find and remove old secondary nav
            for i, control in enumerate(self.page.controls):
                if hasattr(control, 'content') and hasattr(control.content, 'controls'):
                    # This is likely the secondary nav
                    self.page.controls[i] = self.secondary_nav
                    break
        admin_main(self.page, self)
        self.page.update()

    def navigate_to_analytics(self):
        """Navigate to Analytics tab (placeholder)"""
        self.current_tab = 1
        if not self.is_admin_mode:
            self.page.clean()
            self.page.window_width = 1200
            self.page.window_height = 800
            self.page.padding = 0
            self.page.bgcolor = "#f8fafc"
            self.page.theme_mode = ft.ThemeMode.LIGHT
            self.is_admin_mode = True
            self.create_admin_app_bar()
            self.create_secondary_nav_bar()
            self.page.add(self.secondary_nav)
            admin_header = self.create_admin_header()
            self.page.add(admin_header)
        else:
            # Just replace main content, keep app bar and nav bar
            if self.main_content:
                self.page.remove(self.main_content)
            # Update secondary nav to reflect current tab
            self.create_secondary_nav_bar()
            # Need to replace the secondary nav in the page
            for i, control in enumerate(self.page.controls):
                if hasattr(control, 'content') and hasattr(control.content, 'controls'):
                    self.page.controls[i] = self.secondary_nav
                    break
        # TODO: Implement analytics screen
        placeholder = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.ANALYTICS, size=64, color=TEXT_SECONDARY),
                    ft.Container(height=20),
                    ft.Text("Analytics", size=22, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ft.Container(height=8),
                    ft.Text("Analytics dashboard coming soon", size=13, color=TEXT_SECONDARY),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.all(40),
            alignment=ft.alignment.center,
            expand=True,
        )
        self.page.add(placeholder)
        self.main_content = placeholder
        self.page.update()

    def navigate_to_submissions(self):
        """Navigate to Submissions tab"""
        self.current_tab = 2
        if not self.is_admin_mode:
            self.page.clean()
            self.page.window_width = 1200
            self.page.window_height = 800
            self.page.padding = 0
            self.page.bgcolor = "#f8fafc"
            self.page.theme_mode = ft.ThemeMode.LIGHT
            self.is_admin_mode = True
            self.create_admin_app_bar()
            self.create_secondary_nav_bar()
            self.page.add(self.secondary_nav)
            admin_header = self.create_admin_header()
            self.page.add(admin_header)
        else:
            # Just replace main content, keep app bar and nav bar
            if self.main_content:
                self.page.remove(self.main_content)
            # Update secondary nav to reflect current tab
            self.create_secondary_nav_bar()
            # Need to replace the secondary nav in the page
            for i, control in enumerate(self.page.controls):
                if hasattr(control, 'content') and hasattr(control.content, 'controls'):
                    self.page.controls[i] = self.secondary_nav
                    break
        submissions_main(self.page, self)
        self.page.update()

    def navigate_to_settings_audit(self):
        """Navigate to Settings & Audit tab"""
        self.current_tab = 3
        if not self.is_admin_mode:
            self.page.clean()
            self.page.window_width = 1200
            self.page.window_height = 800
            self.page.padding = 0
            self.page.bgcolor = "#f8fafc"
            self.page.theme_mode = ft.ThemeMode.LIGHT
            self.is_admin_mode = True
            self.create_admin_app_bar()
            self.create_secondary_nav_bar()
            self.page.add(self.secondary_nav)
            admin_header = self.create_admin_header()
            self.page.add(admin_header)
        else:
            # Just replace main content, keep app bar and nav bar
            if self.main_content:
                self.page.remove(self.main_content)
            # Update secondary nav to reflect current tab
            self.create_secondary_nav_bar()
            # Need to replace the secondary nav in the page
            for i, control in enumerate(self.page.controls):
                if hasattr(control, 'content') and hasattr(control.content, 'controls'):
                    self.page.controls[i] = self.secondary_nav
                    break
        settings_audit_main(self.page, self)
        self.page.update()

    def navigate_to_account(self):
        """Navigate to account settings screen"""
        self.page.clean()
        self.page.appbar = None
        self.page.window_width = 1500
        self.page.window_height = 900
        self.page.padding = 0
        self.page.bgcolor = "#f8fafc"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.is_admin_mode = False
        self.app_bar = None
        account_main(self.page, self, role="admin")
        self.page.update()

    def navigate_to_admin(self):
        """Navigate to admin panel (initial entry)"""
        if not self.is_admin_mode:
            self.page.clean()
            self.page.window_width = 1200
            self.page.window_height = 800
            self.page.padding = 0
            self.page.bgcolor = "#f8fafc"
            self.page.theme_mode = ft.ThemeMode.LIGHT
            self.is_admin_mode = True
            self.create_admin_app_bar()
            self.create_secondary_nav_bar()
            self.page.add(self.secondary_nav)
            admin_header = self.create_admin_header()
            self.page.add(admin_header)
        else:
            # Just replace main content, keep app bar and nav bar
            if self.main_content:
                try:
                    self.page.remove(self.main_content)
                except ValueError:
                    pass  # Already removed from page
            # Update secondary nav to reflect current tab
            self.create_secondary_nav_bar()
            # Need to replace the secondary nav in the page
            for i, control in enumerate(self.page.controls):
                if hasattr(control, 'content') and hasattr(control.content, 'controls'):
                    self.page.controls[i] = self.secondary_nav
                    break
        admin_main(self.page, self)
        self.page.update()

    def navigate_to_login(self):
        from screens.ui_login import main as login_main
        self.page.clean()
        self.page.appbar = None
        self.page.window_width = 900
        self.page.window_height = 780
        self.page.padding = 0
        self.page.bgcolor = "#0f1e30"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.is_evaluation_mode = False
        self.is_admin_mode = False
        self.page.update()
        from navigation.navigation import Navigation
        login_main(self.page, self.parent_nav if self.parent_nav else Navigation(self.page))


def main(page: ft.Page):
    """Main entry point for admin navigation"""
    page.title = "QualCheck Admin"
    page.window_width = 1200
    page.window_height = 800
    page.padding = 0
    page.bgcolor = "#f8fafc"
    page.theme_mode = ft.ThemeMode.LIGHT
    
    nav = AdminNavigation(page)
    nav.navigate_to_admin()


if __name__ == "__main__":
    ft.app(target=main)