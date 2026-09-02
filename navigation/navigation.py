import time
import threading
import flet as ft
from screens.ui_login import main as login_main
from screens.password_reset import main as reset_password_main
from screens.ui_short_answer import main as short_answer_main
from screens.ui_essay import main as essay_main
from screens.ui_code_report import main as code_report_main
from screens.ui_account import main as account_main
from screens.ui_dashboard import main as dashboard_main
from screens.studenta_result import main as studenta_result_main
from navigation.admin_navigation import AdminNavigation
from utils.utils import (
    BG_COLOR, CARD_BG_COLOR, PRIMARY_BLUE, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_TERTIARY, TEXT_WHITE,
    BUTTON_PRIMARY_BG, BUTTON_PRIMARY_TEXT, BORDER_COLOR
)
from services.session_manager import get_current_user, get_user_role, logout as session_logout

# Duration (ms) for the fade-out and fade-in halves of the transition.
_FADE_MS = 150


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
        self.evaluation_results = None  # Store evaluation results
        self.evaluation_prompt = None  # Store academic prompt
        self.evaluation_rubric = None  # Store rubric
        # Persistent wrapper that stays on the page; its content is swapped during navigation.
        self._content_wrapper = None
        # Transition ID to prevent race conditions during navigation
        self._transition_id = 0

    # ------------------------------------------------------------------
    # Loading overlay
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # App bar
    # ------------------------------------------------------------------
    def create_evaluation_app_bar(self):
        """Create shared app bar for evaluation screens matching the screenshot design"""
        # Get current user info
        user = get_current_user()
        user_name = "User"
        user_initials = "U"
        avatar_url = ""
        
        if user and user.user:
            email = user.user.email
            user_id = user.user.id
            # Extract name from email or use email as name
            user_name = email.split("@")[0].replace(".", " ").title()
            # Generate initials
            name_parts = user_name.split()
            if len(name_parts) >= 2:
                user_initials = (name_parts[0][0] + name_parts[1][0]).upper()
            else:
                user_initials = user_name[:2].upper()
            # Try to load avatar_url and name from profiles
            try:
                from services.supabase_client import get_supabase_client
                supabase = get_supabase_client()
                profile_resp = (
                    supabase.table("profiles")
                    .select("avatar_url, name")
                    .eq("id", user_id)
                    .single()
                    .execute()
                )
                if profile_resp.data:
                    avatar_url = profile_resp.data.get("avatar_url", "") or ""
                    db_name = profile_resp.data.get("name", "")
                    if db_name:
                        user_name = db_name
                        name_parts = user_name.split()
                        if len(name_parts) >= 2:
                            user_initials = (name_parts[0][0] + name_parts[1][0]).upper()
                        else:
                            user_initials = user_name[:2].upper()
            except Exception as _e:
                print(f"Could not fetch profile for evaluation app bar: {_e}")

        # Build avatar widget: photo if available, else initials circle with visible round border
        if avatar_url:
            avatar_widget = ft.Container(
                content=ft.Image(
                    src=avatar_url,
                    width=32,
                    height=32,
                    fit=ft.ImageFit.COVER,
                    border_radius=ft.border_radius.all(16),
                ),
                width=34,
                height=34,
                border_radius=17,
                border=ft.border.all(2, PRIMARY_BLUE),
                bgcolor="#eff6ff",
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                alignment=ft.alignment.center,
            )
        else:
            avatar_widget = ft.Container(
                content=ft.Text(user_initials, size=12, weight=ft.FontWeight.BOLD, color=PRIMARY_BLUE),
                width=34,
                height=34,
                border_radius=17,
                border=ft.border.all(2, PRIMARY_BLUE),
                bgcolor="#eff6ff",
                alignment=ft.alignment.center,
            )
        
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
                                    # Avatar with photo or initials with visible round border
                                    avatar_widget,
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
                            on_click=lambda e: self.logout()
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(width=16),
            ],
        )
        self.page.appbar = self.app_bar

    # ------------------------------------------------------------------
    # Auth screens (no transition animation – full page swap)
    # ------------------------------------------------------------------
    def logout(self):
        """Sign the user out of Supabase, clear the local session file,
        then navigate to the login screen."""
        session_logout()
        # Clear the stale auth-screen flag/controller left over from the
        # previous login screen. If left set, login_main()'s short-circuit
        # (`if page.data.get("auth_active") and "auth_controller" in
        # page.data`) calls the old switch_to_login() closure instead of
        # doing a full rebuild — but by then page.clean() has already
        # wiped the page, so that closure just reattaches stale, detached
        # controls (the sign-in form) with no left hero panel and no
        # correct window sizing. Clearing it here forces a real rebuild.
        if self.page.data:
            self.page.data["auth_active"] = False
            self.page.data.pop("auth_controller", None)
        self.navigate_to_login()

    def navigate_to_login(self):
        """Navigate to login screen"""
        self._transition_id += 1
        
        # Smooth fade out before changing the screen
        if self.page.controls:
            for c in self.page.controls:
                c.animate_opacity = ft.Animation(300, ft.AnimationCurve.EASE_OUT)
                c.opacity = 0
            self.page.update()
            time.sleep(0.3)
            
        if self.page.data is None:
            self.page.data = {}
        self.page.data["auth_active"] = False
        self.page.clean()
        self.page.appbar = None
        self.page.scroll = None
        self.page.window_width = 1180
        self.page.window_height = 760
        self.page.window_min_width = 960
        self.page.window_min_height = 640
        self.page.padding = 0
        self.page.bgcolor = BG_COLOR
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.is_evaluation_mode = False
        self.is_admin_mode = False
        self.app_bar = None
        self._content_wrapper = None
        # Don't call page.update() with empty page — login_main adds content and updates
        login_main(self.page, self)

    def navigate_to_reset_password(self):
        """Navigate to the reset password screen"""
        self._transition_id += 1
        if self.page.data and self.page.data.get("auth_active") and "auth_controller" in self.page.data:
            self.page.data["auth_controller"]["switch_to_reset_password"]()
            return

        if self.page.data is None:
            self.page.data = {}
        self.page.data["auth_active"] = False
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
        self._content_wrapper = None
        self.page.update()
        reset_password_main(self.page, self)

    # ------------------------------------------------------------------
    # App-bar button highlighting
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Core evaluator content swap with fade transition
    # ------------------------------------------------------------------
    def _swap_evaluator_content(self, content_loader):
        """Swap the main content area with a smooth fade transition."""
        self._transition_id += 1
        current_id = self._transition_id

        # If coming from admin mode, force a full rebuild
        coming_from_admin = self.admin_nav.is_admin_mode
        if coming_from_admin:
            self.admin_nav.is_admin_mode = False
            self.admin_nav.main_content = None
            self.admin_nav.secondary_nav = None
            self.admin_nav.admin_header = None
            self.admin_nav._content_wrapper = None
            self.is_evaluation_mode = False  # Force full rebuild

        if not self.is_evaluation_mode:
            # ----- First time entering evaluator mode -----
            
            # Smooth fade out before changing the screen
            if self.page.controls:
                for c in self.page.controls:
                    c.animate_opacity = ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT)
                    c.opacity = 0
                self.page.update()
                time.sleep(0.2)

            # Configure page properties
            self.page.window_width = 1200
            self.page.window_height = 800
            self.page.padding = 0
            self.page.scroll = None
            self.page.bgcolor = "#f8fafc"
            self.page.theme_mode = ft.ThemeMode.LIGHT
            self.page.appbar = None
            # Use controls.clear() instead of page.clean() to avoid auto-update
            self.page.controls.clear()
            self.is_evaluation_mode = True
            self.main_content = None

            # Build the persistent wrapper (starts fully visible)
            self._content_wrapper = ft.Container(
                opacity=1,
                animate_opacity=ft.Animation(_FADE_MS, ft.AnimationCurve.EASE_IN_OUT),
                expand=True,
            )

            # Load screen content – screen sets self.main_content but does NOT page.add()
            content_loader()
            captured_content = self.main_content
            # Safety: remove from page.controls if the screen added it anyway
            if captured_content and captured_content in self.page.controls:
                self.page.controls.remove(captured_content)
                
            if current_id != self._transition_id:
                return

            # Place content inside the wrapper
            if self._content_wrapper:
                self._content_wrapper.content = captured_content

            # Build the app bar (sets self.page.appbar)
            self.create_evaluation_app_bar()
            
            # Append wrapper to page controls (no auto-update)
            if self._content_wrapper:
                self.page.controls.append(self._content_wrapper)
            elif captured_content:
                self.page.controls.append(captured_content)

            # Single atomic update: bgcolor + appbar + content all rendered at once
            self.page.update()
        else:
            # ----- Subsequent switches (within evaluator mode) -----
            if self._content_wrapper is None:
                self.is_evaluation_mode = False
                return self._swap_evaluator_content(content_loader)

            # Fade out current content
            self._content_wrapper.opacity = 0
            self.page.update()
            time.sleep(_FADE_MS / 1000)

            if current_id != self._transition_id:
                return

            # Update nav button highlights
            self._update_appbar_buttons()

            # Remove any stray controls (keep only our wrapper)
            stray = [c for c in self.page.controls if c is not self._content_wrapper]
            for c in stray:
                self.page.controls.remove(c)

            # Load new content
            self.main_content = None
            content_loader()

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

    # ------------------------------------------------------------------
    # Public navigation methods
    # ------------------------------------------------------------------
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

    def navigate_to_new_evaluation(self):
        """Navigate to the evaluation selection screen"""
        self.current_view = "evaluation"
        self._swap_evaluator_content(lambda: short_answer_main(self.page, self))

    def navigate_to_account(self):
        """Navigate to evaluator account settings"""
        self._transition_id += 1
        self.current_view = "account"

        self.page.clean()
        self.page.appbar = None
        self.page.window_width = 1500
        self.page.window_height = 900
        self.page.padding = 0
        self.page.bgcolor = "#f8fafc"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.scroll = ft.ScrollMode.AUTO
        self.is_evaluation_mode = False
        self.app_bar = None
        self._content_wrapper = None
        account_main(self.page, self, role="evaluator")
        if self.main_content and self.main_content not in self.page.controls:
            self.page.add(self.main_content)
        self.page.update()

    def navigate_to_student_result(self, results=None, academic_prompt=None, rubric=None, output_type_label="Short Answer", theta1=None, theta2=None):
        """Navigate to student results screen"""
        # Store evaluation data
        self.evaluation_results = results
        self.evaluation_prompt = academic_prompt
        self.evaluation_rubric = rubric
        self.evaluation_output_type_label = output_type_label
        self.evaluation_theta1 = theta1
        self.evaluation_theta2 = theta2
        
        self.current_view = "evaluation"
        self._swap_evaluator_content(
            lambda: studenta_result_main(self.page, self, results, academic_prompt, rubric, output_type_label,
                                          theta1=theta1, theta2=theta2)
        )

    def navigate_to_admin(self):
        """Navigate to admin panel"""
        self._transition_id += 1
        # Fully reset evaluator state so admin gets a clean page
        self.is_evaluation_mode = False
        self.main_content = None
        self.app_bar = None
        self._content_wrapper = None
        self.admin_nav.is_admin_mode = False
        self.admin_nav.main_content = None
        self.admin_nav.secondary_nav = None
        self.admin_nav.admin_header = None
        self.admin_nav._content_wrapper = None
        self.admin_nav.navigate_to_admin()