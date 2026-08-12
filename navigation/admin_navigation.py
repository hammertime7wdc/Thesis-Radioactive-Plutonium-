import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import flet as ft
from screens.ui_admin import main as admin_main
from screens.ui_admin_settings_audit import main as settings_audit_main
from screens.ui_admin_submissions import main as submissions_main
from screens.ui_admin_analytics import main as analytics_main
from screens.ui_account import main as account_main
from utils.utils import (
    CARD_BG_COLOR, PRIMARY_BLUE, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_TERTIARY, TEXT_WHITE,
    BUTTON_PRIMARY_BG, BUTTON_PRIMARY_TEXT, BUTTON_SECONDARY_BG, BUTTON_SECONDARY_TEXT,
    BORDER_COLOR
)
from services.session_manager import get_current_user

# Duration (ms) for the fade-out and fade-in halves of the transition.
_FADE_MS = 150


class AdminNavigation:
    """Navigation handler for Admin Panel sections"""
    
    def __init__(self, page: ft.Page, parent_nav=None):
        self.page = page
        self.parent_nav = parent_nav
        self.current_tab = 0
        self.main_content = None
        self.secondary_nav = None
        self.admin_header = None
        self.is_evaluation_mode = False
        self.is_admin_mode = False
        self.app_bar = None
        self.loading_overlay = None
        # Persistent wrapper for smooth fade transitions within admin tabs.
        self._content_wrapper = None
        # Transition ID to prevent race conditions during navigation
        self._transition_id = 0
    
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
            alignment=ft.alignment.Alignment(0, 0),
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
                self.parent_nav.is_evaluation_mode = False
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
                        alignment=ft.alignment.Alignment(0, 0),
                        on_click=on_admin,
                    ),
                    ft.Container(width=8),
                    # New Evaluation - light gray button
                    ft.Container(
                        content=ft.Text("New Evaluation", size=13, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY),
                        padding=ft.padding.symmetric(horizontal=16, vertical=10),
                        bgcolor="#f1f5f9",
                        border_radius=8,
                        alignment=ft.alignment.Alignment(0, 0),
                        on_click=on_new_evaluation,
                    ),
                    ft.Container(width=8),
                    # Dashboard - light gray button
                    ft.Container(
                        content=ft.Text("Dashboard", size=13, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY),
                        padding=ft.padding.symmetric(horizontal=16, vertical=10),
                        bgcolor="#f1f5f9",
                        border_radius=8,
                        alignment=ft.alignment.Alignment(0, 0),
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
                                        alignment=ft.alignment.Alignment(0, 0),
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
            bgcolor="#f8fafc",
            border=ft.border.only(bottom=ft.BorderSide(1, BORDER_COLOR)),
            padding=ft.padding.symmetric(horizontal=32, vertical=12),
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
            alignment=ft.alignment.Alignment(0, 0),
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
            alignment=ft.alignment.Alignment(0, 0),
            expand=True,
        )
        self.page.add(self.loading_overlay)
        self.page.update()

    def hide_loading(self):
        """Hide loading overlay"""
        if hasattr(self, 'loading_overlay') and self.loading_overlay:
            try:
                self.page.remove(self.loading_overlay)
            except ValueError:
                pass
            self.loading_overlay = None
            self.page.update()

    def _update_tab_styles(self):
        """Update the tab bar styling in-place without recreating/removing it"""
        if not self.secondary_nav or not self.secondary_nav.content:
            return
        tab_row = self.secondary_nav.content
        tab_index = 0
        for child in tab_row.controls:
            # Skip spacer containers (width=8)
            if hasattr(child, 'on_click') and child.on_click is not None:
                is_active = tab_index == self.current_tab
                child.bgcolor = PRIMARY_BLUE if is_active else "#f1f5f9"
                # Update icon and text colors inside the row
                if child.content and hasattr(child.content, 'controls'):
                    for inner in child.content.controls:
                        if isinstance(inner, ft.Icon):
                            inner.color = TEXT_WHITE if is_active else TEXT_SECONDARY
                        elif isinstance(inner, ft.Text):
                            inner.color = TEXT_WHITE if is_active else TEXT_PRIMARY
                            inner.weight = ft.FontWeight.W_600 if is_active else ft.FontWeight.W_500
                tab_index += 1

    def _swap_content(self, content_loader):
        """Swap only the main content area with a smooth fade transition,
        keeping header and nav bar in place."""
        self._transition_id += 1
        current_id = self._transition_id

        if not self.is_admin_mode:
            # ----- First time entering admin: clean everything and build full layout -----
            
            # Smooth fade out before changing the screen
            if self.page.controls:
                for c in self.page.controls:
                    c.animate_opacity = ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT)
                    c.opacity = 0
                self.page.update()
                time.sleep(0.2)
                
            # Set page configurations (idempotent)
            self.page.window_width = 1200
            self.page.window_height = 800
            self.page.padding = 0
            self.page.bgcolor = "#f8fafc"
            self.page.theme_mode = ft.ThemeMode.LIGHT
            
            self.page.appbar = None
            self.page.clean()
            self.is_admin_mode = True
            self.main_content = None

            # 1. Admin Header (do not add yet)
            self.admin_header = self.create_admin_header()

            # 2. Tab bar (do not add yet)
            self.create_secondary_nav_bar()

            # 3. Build the persistent content wrapper with opacity=1
            self._content_wrapper = ft.Container(
                opacity=1,
                animate_opacity=ft.Animation(_FADE_MS, ft.AnimationCurve.EASE_IN_OUT),
                expand=True,
            )

            # 4. Load content, capture it into the wrapper
            content_loader()
            captured_content = self.main_content
            if captured_content and captured_content in self.page.controls:
                self.page.controls.remove(captured_content)
            
            if current_id != self._transition_id:
                return
                
            if self._content_wrapper:
                self._content_wrapper.content = captured_content

            self.create_admin_app_bar()
            
            # Now add everything to page in one go
            self.page.add(self.admin_header, self.secondary_nav)
            if self._content_wrapper:
                self.page.add(self._content_wrapper)
            elif captured_content:
                # Fallback if wrapper is missing
                self.page.add(captured_content)

            self.page.update()
        else:
            # ----- Subsequent tab switches -----
            if self._content_wrapper is None:
                # Safety: wrapper was lost somehow, rebuild
                self.is_admin_mode = False
                return self._swap_content(content_loader)

            # Fade out current content
            self._content_wrapper.opacity = 0
            self.page.update()
            time.sleep(_FADE_MS / 1000)

            # Abort if another navigation occurred during the sleep
            if current_id != self._transition_id:
                return

            # Update tab active states in-place
            self._update_tab_styles()

            # Remove any stray controls that screens may have added directly
            # (keep header at 0, tab bar at 1, wrapper at 2)
            while len(self.page.controls) > 3:
                self.page.controls.pop()

            # Load new content
            self.main_content = None
            content_loader()

            # Capture the new content into the wrapper
            captured_content = self.main_content
            if captured_content and captured_content in self.page.controls:
                self.page.controls.remove(captured_content)
                
            if current_id != self._transition_id:
                return

            if self._content_wrapper:
                self._content_wrapper.content = captured_content
            elif captured_content:
                self.page.add(captured_content)

            # Fade in
            if self._content_wrapper:
                self._content_wrapper.opacity = 1
            self.page.update()

    def navigate_to_users(self):
        """Navigate to Users tab"""
        self.current_tab = 0
        self._swap_content(lambda: admin_main(self.page, self))

    def navigate_to_analytics(self):
        """Navigate to Analytics tab"""
        self.current_tab = 1
        self._swap_content(lambda: analytics_main(self.page, self))

    def navigate_to_submissions(self):
        """Navigate to Submissions tab"""
        self.current_tab = 2
        self._swap_content(lambda: submissions_main(self.page, self))

    def navigate_to_settings_audit(self):
        """Navigate to Settings & Audit tab"""
        self.current_tab = 3
        self._swap_content(lambda: settings_audit_main(self.page, self))

    def navigate_to_account(self):
        """Navigate to account settings screen"""
        self._transition_id += 1
        self.current_tab = -1

        self.page.clean()
        self.page.appbar = None
        self.page.window_width = 1500
        self.page.window_height = 900
        self.page.padding = 0
        self.page.bgcolor = "#f8fafc"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.scroll = ft.ScrollMode.AUTO
        self.is_admin_mode = False
        self.app_bar = None
        self._content_wrapper = None
        account_main(self.page, self, role="admin")
        if self.main_content and self.main_content not in self.page.controls:
            self.page.add(self.main_content)
        self.page.update()

    def navigate_to_admin(self):
        """Navigate to admin panel (initial entry)"""
        self.navigate_to_users()

    def navigate_to_login(self):
        from screens.ui_login import main as login_main
        self._transition_id += 1
        
        # Smooth fade out before changing the screen
        if self.page.controls:
            for c in self.page.controls:
                c.animate_opacity = ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT)
                c.opacity = 0
            self.page.update()
            time.sleep(0.2)
            
        self.page.clean()
        self.page.appbar = None
        self.page.window_width = 900
        self.page.window_height = 780
        self.page.padding = 0
        self.page.bgcolor = "#0f1e30"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.is_evaluation_mode = False
        self.is_admin_mode = False
        self._content_wrapper = None
        # Don't call page.update() with empty page — login_main adds content and updates
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