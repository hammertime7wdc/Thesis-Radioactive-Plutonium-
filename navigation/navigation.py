import flet as ft
from screens.ui_login import main as login_main
from screens.password_reset import main as reset_password_main
from screens.ui_short_answer import main as short_answer_main
from screens.ui_essay import main as essay_main
from screens.ui_code_report import main as code_report_main
from screens.ui_account import main as account_main
from screens.ui_dashboard import main as dashboard_main
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
        self.current_view = "dashboard"  # Track current view: "dashboard", "evaluation", "account", "admin"
        self.loading_overlay = None

    def show_loading(self):
        """Show loading overlay"""
        self.loading_overlay = ft.Container(
            content=ft.Column(
                [
                    ft.ProgressRing(width=40, height=40, stroke_width=3, color=PRIMARY_BLUE),
                    ft.Container(height=16),
                    ft.Text("Loading...", size=14, color=TEXT_SECONDARY),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor="#ffffff",
            alignment=ft.alignment.center,
            expand=True,
        )
        self.page.add(self.loading_overlay)
        self.page.update()

    def hide_loading(self):
        """Hide loading overlay"""
        if self.loading_overlay:
            try:
                self.page.remove(self.loading_overlay)
            except ValueError:
                pass
            self.loading_overlay = None
            self.page.update()

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

        # Determine button colors based on current view
        dashboard_bg = PRIMARY_BLUE if self.current_view == "dashboard" else "#f1f5f9"
        dashboard_color = TEXT_WHITE if self.current_view == "dashboard" else TEXT_PRIMARY
        dashboard_weight = ft.FontWeight.W_600 if self.current_view == "dashboard" else ft.FontWeight.W_500

        evaluation_bg = PRIMARY_BLUE if self.current_view == "evaluation" else "#f1f5f9"
        evaluation_color = TEXT_WHITE if self.current_view == "evaluation" else TEXT_PRIMARY
        evaluation_weight = ft.FontWeight.W_600 if self.current_view == "evaluation" else ft.FontWeight.W_500

        buttons_row.extend([
            # New Evaluation button
            ft.Container(
                content=ft.Text("New Evaluation", size=13, weight=evaluation_weight, color=evaluation_color),
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                bgcolor=evaluation_bg,
                border_radius=8,
                alignment=ft.alignment.center,
                on_click=lambda e: self.navigate_to_short_answer(),
            ),
            ft.Container(width=8),
            # Dashboard button
            ft.Container(
                content=ft.Text("Dashboard", size=13, weight=dashboard_weight, color=dashboard_color),
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                bgcolor=dashboard_bg,
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

    def _update_appbar_buttons(self):
        """Update the app bar button active states in-place without recreating the app bar"""
        if not self.app_bar or not self.app_bar.title:
            return
        title_row = self.app_bar.title
        if not hasattr(title_row, 'controls'):
            return
        for child in title_row.controls:
            if not hasattr(child, 'on_click') or child.on_click is None:
                continue
            if not hasattr(child, 'content') or not isinstance(child.content, ft.Text):
                continue
            label = child.content.value
            if label == "New Evaluation":
                is_active = self.current_view == "evaluation"
                child.bgcolor = PRIMARY_BLUE if is_active else "#f1f5f9"
                child.content.color = TEXT_WHITE if is_active else TEXT_PRIMARY
                child.content.weight = ft.FontWeight.W_600 if is_active else ft.FontWeight.W_500
            elif label == "Dashboard":
                is_active = self.current_view == "dashboard"
                child.bgcolor = PRIMARY_BLUE if is_active else "#f1f5f9"
                child.content.color = TEXT_WHITE if is_active else TEXT_PRIMARY
                child.content.weight = ft.FontWeight.W_600 if is_active else ft.FontWeight.W_500

    def _swap_evaluator_content(self, content_loader):
        """Swap only the main content area, keeping the app bar in place"""
        self.page.window_width = 1200
        self.page.window_height = 800
        self.page.padding = 0
        self.page.bgcolor = "#f8fafc"
        self.page.theme_mode = ft.ThemeMode.LIGHT

        if not self.is_evaluation_mode:
            # First time entering evaluator mode: clean everything and build app bar
            self.page.clean()
            self.is_evaluation_mode = True
            self.create_evaluation_app_bar()
            content_loader()
            self.page.update()
        else:
            # Subsequent switches: only remove old content and update button styles
            if self.main_content and self.main_content in self.page.controls:
                try:
                    self.page.remove(self.main_content)
                except ValueError:
                    pass
                self.main_content = None
            self._update_appbar_buttons()
            content_loader()
            self.page.update()

    def navigate_to_short_answer(self):
        """Navigate to short answer evaluation screen"""
        self.current_view = "evaluation"
        self._swap_evaluator_content(lambda: short_answer_main(self.page, self))

    def navigate_to_essay(self):
        """Navigate to essay evaluation screen"""
        self.current_view = "evaluation"
        self._swap_evaluator_content(lambda: essay_main(self.page, self))

    def navigate_to_code_report(self):
        """Navigate to code report evaluation screen"""
        self.current_view = "evaluation"
        self._swap_evaluator_content(lambda: code_report_main(self.page, self))

    def navigate_to_dashboard(self):
        """Navigate to dashboard"""
        self.current_view = "dashboard"
        self._swap_evaluator_content(lambda: dashboard_main(self.page, self, role="evaluator"))

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
        self.is_evaluation_mode = False
        self.admin_nav.is_admin_mode = False
        self.admin_nav.navigate_to_admin()