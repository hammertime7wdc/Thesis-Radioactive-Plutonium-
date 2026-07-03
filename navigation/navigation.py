import flet as ft
from screens.ui_login import main as login_main
from screens.password_reset import main as reset_password_main
from screens.ui_short_answer import main as short_answer_main
from screens.ui_essay import main as essay_main
from screens.ui_code_report import main as code_report_main
from screens.ui_account import main as account_main
from navigation.admin_navigation import AdminNavigation
from utils.utils import (
    CARD_BG_COLOR, PRIMARY_BLUE, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_TERTIARY, TEXT_WHITE,
    BUTTON_PRIMARY_BG, BUTTON_PRIMARY_TEXT, BORDER_COLOR
)
from services.session_manager import get_current_user, get_user_role


class Navigation:
    """Navigation handler for QualCheck application"""

    def __init__(self, page: ft.Page):
        self.page = page
        self.current_screen = None
        self.is_evaluation_mode = False
        self.app_bar = None
        self.main_content = None
        self.admin_nav = AdminNavigation(page, self)

    def create_evaluation_app_bar(self):
        """Create shared app bar for evaluation screens matching the screenshot design"""
        # Get current user info
        user = get_current_user()
        user_name = "Google User"
        user_initials = "GU"
        
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
        )

        brand = ft.Column(
            [
                ft.Text("QualCheck", size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Text("Rubric-Guided Semantic Evaluation System", size=10, color=TEXT_SECONDARY),
            ],
            spacing=2,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        # Check if the user is an admin to show Admin switching button
        role = get_user_role()
        
        buttons_row = [ft.Container(width=20)]
        if role == "admin":
            buttons_row.extend([
                # Admin - light gray button when on evaluator side
                ft.Container(
                    content=ft.Text("Admin", size=13, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY),
                    padding=ft.padding.symmetric(horizontal=16, vertical=10),
                    bgcolor="#f1f5f9",
                    border_radius=8,
                    alignment=ft.alignment.center,
                    on_click=lambda e: self.navigate_to_admin(),
                ),
                ft.Container(width=8),
            ])
            
        buttons_row.extend([
            # New Evaluation - solid blue button
            ft.Container(
                content=ft.Text("New Evaluation", size=13, weight=ft.FontWeight.W_600, color=TEXT_WHITE),
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                bgcolor=PRIMARY_BLUE,
                border_radius=8,
                alignment=ft.alignment.center,
                on_click=lambda e: self.navigate_to_short_answer(),
            ),
            ft.Container(width=8),
            # Dashboard - light gray button
            ft.Container(
                content=ft.Text("Dashboard", size=13, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY),
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                bgcolor="#f1f5f9",
                border_radius=8,
                alignment=ft.alignment.center,
                on_click=lambda e: self.navigate_to_dashboard(),
            ),
        ])

        self.app_bar = ft.AppBar(
            leading=ft.Row([ft.Container(width=12), logo, ft.Container(width=12), brand], alignment=ft.MainAxisAlignment.CENTER),
            leading_width=320,
            bgcolor=CARD_BG_COLOR,
            toolbar_height=70,
            center_title=False,
            title=ft.Row(buttons_row),
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
                        # Clickable profile container
                        ft.Container(
                            content=ft.Row(
                                [
                                    # Avatar with initials
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
                                            ft.Text("Evaluator", size=11, color=TEXT_SECONDARY),
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

    def navigate_to_login(self):
        """Navigate to login screen"""
        self.page.clean()
        self.page.appbar = None
        self.page.window_width = 900
        self.page.window_height = 780
        self.page.padding = 0
        self.page.bgcolor = "#0f1e30"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.is_evaluation_mode = False
        self.is_admin_mode = False
        self.app_bar = None
        self.page.update()
        login_main(self.page, self)

    def navigate_to_reset_password(self):
        """Navigate to the reset password screen"""
        self.page.clean()
        self.page.appbar = None
        self.page.window_width = 900
        self.page.window_height = 780
        self.page.window_min_width = 900
        self.page.window_min_height = 780
        self.page.padding = 0
        self.page.bgcolor = "#0f1e30"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.is_evaluation_mode = False
        self.app_bar = None
        self.page.update()
        reset_password_main(self.page, self)

    def navigate_to_short_answer(self):
        """Navigate to short answer evaluation screen"""
        if not self.is_evaluation_mode:
            self.page.clean()
            self.page.window_width = 1200
            self.page.window_height = 800
            self.page.padding = 0
            self.page.bgcolor = "#f8fafc"
            self.page.theme_mode = ft.ThemeMode.LIGHT
            self.is_evaluation_mode = True
            self.create_evaluation_app_bar()
        else:
            # Just replace main content, keep app bar
            if self.main_content:
                try:
                    self.page.remove(self.main_content)
                except ValueError:
                    pass  # Already removed from page
        short_answer_main(self.page, self)

    def navigate_to_essay(self):
        """Navigate to essay evaluation screen"""
        if not self.is_evaluation_mode:
            self.page.clean()
            self.page.window_width = 1200
            self.page.window_height = 800
            self.page.padding = 0
            self.page.bgcolor = "#f8fafc"
            self.page.theme_mode = ft.ThemeMode.LIGHT
            self.is_evaluation_mode = True
            self.create_evaluation_app_bar()
        else:
            # Just replace main content, keep app bar
            if self.main_content:
                try:
                    self.page.remove(self.main_content)
                except ValueError:
                    pass  # Already removed from page
        essay_main(self.page, self)

    def navigate_to_code_report(self):
        """Navigate to code report evaluation screen"""
        if not self.is_evaluation_mode:
            self.page.clean()
            self.page.window_width = 1200
            self.page.window_height = 800
            self.page.padding = 0
            self.page.bgcolor = "#f8fafc"
            self.page.theme_mode = ft.ThemeMode.LIGHT
            self.is_evaluation_mode = True
            self.create_evaluation_app_bar()
        else:
            # Just replace main content, keep app bar
            if self.main_content:
                try:
                    self.page.remove(self.main_content)
                except ValueError:
                    pass  # Already removed from page
        code_report_main(self.page, self)

    def navigate_to_dashboard(self):
        """Navigate to dashboard (placeholder)"""
        # TODO: Implement dashboard screen
        print("Dashboard navigation - not implemented yet")

    def navigate_to_account(self):
        """Navigate to evaluator account settings"""
        self.page.clean()
        self.page.appbar = None
        self.page.window_width = 1500
        self.page.window_height = 900
        self.page.padding = 0
        self.page.bgcolor = "#f8fafc"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.is_evaluation_mode = False
        self.app_bar = None
        account_main(self.page, self, role="evaluator")
        self.page.update()

    def navigate_to_admin(self):
        """Navigate to admin panel"""
        self.admin_nav.is_admin_mode = False
        self.admin_nav.navigate_to_admin()