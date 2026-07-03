import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import flet as ft
from services.supabase_client import get_supabase_client
from services.session_manager import get_current_user, clear_session

from utils.utils import (
    BG_COLOR,
    CARD_BG_COLOR,
    SECTION_BG_COLOR,
    PRIMARY_BLUE,
    PRIMARY_BLUE_DARK,
    PRIMARY_BLUE_LIGHT,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_TERTIARY,
    TEXT_WHITE,
    BORDER_COLOR,
    BORDER_COLOR_DARK,
    BUTTON_PRIMARY_BG,
    BUTTON_PRIMARY_TEXT,
    BUTTON_SECONDARY_BG,
    BUTTON_SECONDARY_TEXT,
    BUTTON_SECONDARY_BORDER,
    INPUT_BG,
    INPUT_BORDER,
    INPUT_TEXT,
    INPUT_HINT,
    SUCCESS,
)


def main(page: ft.Page, nav=None, role="evaluator"):
    page.title = "QualCheck - Account Settings"
    page.scroll = ft.ScrollMode.AUTO
    page.bgcolor = BG_COLOR
    page.theme_mode = ft.ThemeMode.LIGHT

    active_tab = {"value": "profile"}

    # Load user profile from Supabase
    user = get_current_user()
    if not user:
        # If no session, redirect to login
        if nav and hasattr(nav, "navigate_to_login"):
            nav.navigate_to_login()
        return

    user_id = user.user.id
    user_email = user.user.email

    try:
        supabase = get_supabase_client()
        profile_response = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
        profile_data = profile_response.data
    except Exception:
        profile_data = {}

    is_admin = profile_data.get("role", "evaluator") == "admin"
    display_name = profile_data.get("name", "User")
    display_email = profile_data.get("email", user_email)
    display_department = profile_data.get("department", "")
    display_institution = profile_data.get("institution", "")
    display_bio = profile_data.get("bio", "")

    # ---------- compact building blocks ----------

    def section_card(content):
        # Flat card: no shadow, just a subtle border. Muted, not floating.
        return ft.Container(
            content=content,
            bgcolor=CARD_BG_COLOR,
            border_radius=10,
            border=ft.border.all(1, BORDER_COLOR),
            padding=ft.padding.all(18),
        )

    def text_field(label, value="", width=290, password=False, multiline=False, hint=None):
        field = ft.TextField(
            value=value,
            password=password,
            can_reveal_password=password,
            multiline=multiline,
            min_lines=2 if multiline else 1,
            max_lines=3 if multiline else 1,
            width=width,
            border_radius=8,
            bgcolor=INPUT_BG,
            border_color=INPUT_BORDER,
            focused_border_color=PRIMARY_BLUE,
            color=INPUT_TEXT,
            text_size=13,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=10),
            hint_text=hint,
            hint_style=ft.TextStyle(color=INPUT_HINT),
        )
        return ft.Column([
            ft.Text(label, size=12, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
            ft.Container(height=4),
            field,
        ], spacing=0)

    def sidebar_button(label, icon, key):
        is_active = active_tab["value"] == key
        # Muted active state: soft tint background + border instead of solid saturated blue block.
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icon, size=16, color=PRIMARY_BLUE if is_active else TEXT_SECONDARY),
                    ft.Container(width=8),
                    ft.Text(label, size=13, weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.W_500, color=PRIMARY_BLUE if is_active else TEXT_PRIMARY),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            width=200,
            padding=ft.padding.symmetric(horizontal=14, vertical=9),
            bgcolor="#eef2f7" if is_active else "transparent",
            border_radius=8,
            ink=True,
            on_click=lambda e, tab=key: set_tab(tab),
        )

    def role_pill():
        role_icon = ft.Icons.SHIELD_OUTLINED if is_admin else ft.Icons.MENU_BOOK_OUTLINED
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(role_icon, size=12, color=TEXT_SECONDARY),
                    ft.Container(width=4),
                    ft.Text("Admin" if is_admin else "Evaluator", size=11, weight=ft.FontWeight.W_600, color=TEXT_SECONDARY),
                ],
                spacing=0,
                tight=True,
            ),
            padding=ft.padding.symmetric(horizontal=8, vertical=3),
            bgcolor=SECTION_BG_COLOR,
            border=ft.border.all(1, BORDER_COLOR),
            border_radius=999,
        )

    current_password = ft.TextField(hint_text="Current password", password=True, can_reveal_password=True, width=520, height=42, border_radius=8, bgcolor=INPUT_BG, border_color=INPUT_BORDER, focused_border_color=PRIMARY_BLUE, text_size=13, content_padding=ft.padding.symmetric(horizontal=12, vertical=8))
    new_password = ft.TextField(hint_text="Min. 6 characters", password=True, can_reveal_password=True, width=520, height=42, border_radius=8, bgcolor=INPUT_BG, border_color=INPUT_BORDER, focused_border_color=PRIMARY_BLUE, text_size=13, content_padding=ft.padding.symmetric(horizontal=12, vertical=8))
    confirm_password = ft.TextField(hint_text="Confirm new password", password=True, can_reveal_password=True, width=520, height=42, border_radius=8, bgcolor=INPUT_BG, border_color=INPUT_BORDER, focused_border_color=PRIMARY_BLUE, text_size=13, content_padding=ft.padding.symmetric(horizontal=12, vertical=8))
    security_message = ft.Text("", size=12, color=SUCCESS, visible=False)

    notifications_email = ft.Switch(value=True, active_color=PRIMARY_BLUE)
    notifications_system = ft.Switch(value=True, active_color=PRIMARY_BLUE)
    notifications_marketing = ft.Switch(value=False, active_color=PRIMARY_BLUE)

    def set_tab(tab):
        active_tab["value"] = tab
        render_content()
        page.update()

    def go_back(e):
        if not nav:
            return
        if is_admin and hasattr(nav, "navigate_to_admin"):
            nav.navigate_to_admin()
        elif hasattr(nav, "navigate_to_short_answer"):
            nav.navigate_to_short_answer()

    def update_profile(e):
        try:
            supabase = get_supabase_client()
            supabase.table("profiles").update({
                "name": display_name,
                "email": display_email,
                "department": display_department,
                "institution": display_institution,
                "bio": display_bio
            }).eq("id", user_id).execute()

            profile_message.value = "Profile changes saved."
            profile_message.visible = True
            profile_message.color = SUCCESS
            page.update()
        except Exception as ex:
            profile_message.value = f"Error saving profile: {str(ex)}"
            profile_message.visible = True
            profile_message.color = ft.Colors.RED_500
            page.update()

    def update_password(e):
        if not current_password.value or not new_password.value or not confirm_password.value:
            security_message.value = "Please fill in all password fields."
            security_message.color = ft.Colors.RED_500
            security_message.visible = True
            page.update()
            return
        if new_password.value != confirm_password.value:
            security_message.value = "New passwords do not match."
            security_message.color = ft.Colors.RED_500
            security_message.visible = True
            page.update()
            return
        if len(new_password.value) < 6:
            security_message.value = "Password must be at least 6 characters."
            security_message.color = ft.Colors.RED_500
            security_message.visible = True
            page.update()
            return

        try:
            supabase = get_supabase_client()
            supabase.auth.update_user({
                "password": new_password.value
            })

            security_message.value = "Password updated successfully."
            security_message.color = SUCCESS
            security_message.visible = True
            page.update()
        except Exception as ex:
            security_message.value = f"Error updating password: {str(ex)}"
            security_message.color = ft.Colors.RED_500
            security_message.visible = True
            page.update()

    profile_message = ft.Text("", size=12, color=SUCCESS, visible=False)

    def profile_view():
        # Flat avatar: no shadow, just a solid fill circle.
        avatar = ft.Stack(
            [
                ft.Container(
                    content=ft.Text("A", size=26, weight=ft.FontWeight.BOLD, color=TEXT_WHITE),
                    width=64,
                    height=64,
                    border_radius=32,
                    bgcolor=PRIMARY_BLUE,
                    alignment=ft.alignment.center,
                ),
                ft.Container(
                    content=ft.Icon(ft.Icons.CAMERA_ALT_OUTLINED, size=12, color=TEXT_SECONDARY),
                    width=22,
                    height=22,
                    border_radius=11,
                    bgcolor=CARD_BG_COLOR,
                    border=ft.border.all(1, BORDER_COLOR),
                    alignment=ft.alignment.center,
                    right=0,
                    bottom=0,
                ),
            ],
            width=64,
            height=64,
        )

        info_row = ft.Row(
            [
                avatar,
                ft.Container(width=14),
                ft.Column(
                    [
                        ft.Text(display_name, size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ft.Text(display_email, size=12, color=TEXT_SECONDARY),
                        ft.Container(height=4),
                        role_pill(),
                    ],
                    spacing=2,
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        recent_activity = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Recent Activity", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ft.Container(height=10),
                    ft.Row([ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, size=16, color=TEXT_SECONDARY), ft.Container(width=10), ft.Text("Evaluated 12 uploaded PDFs", size=12, color=TEXT_PRIMARY)], spacing=0),
                    ft.Container(height=8),
                    ft.Row([ft.Icon(ft.Icons.UPLOAD_FILE, size=16, color=TEXT_SECONDARY), ft.Container(width=10), ft.Text("Submitted a batch review", size=12, color=TEXT_PRIMARY)], spacing=0),
                    ft.Container(height=8),
                    ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=16, color=TEXT_SECONDARY), ft.Container(width=10), ft.Text("Updated profile details", size=12, color=TEXT_PRIMARY)], spacing=0),
                ],
                spacing=0,
            ),
            padding=ft.padding.all(16),
            bgcolor=SECTION_BG_COLOR,
            border_radius=10,
            border=ft.border.all(1, BORDER_COLOR),
        )

        return ft.Column(
            [
                ft.Text("Personal Information", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(height=12),
                info_row,
                ft.Container(height=18),
                ft.Row(
                    [
                        text_field("Full Name", value=display_name),
                        text_field("Email Address", value=display_email),
                    ],
                    spacing=14,
                ),
                ft.Container(height=12),
                ft.Row(
                    [
                        text_field("Department", value=display_department),
                        text_field("Institution", value=display_institution),
                    ],
                    spacing=14,
                ),
                ft.Container(height=12),
                text_field(
                    "Bio",
                    value=display_bio,
                    width=594,
                    multiline=True,
                ),
                ft.Container(height=14),
                ft.Row([
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        "Save Changes",
                        width=130,
                        height=38,
                        bgcolor=BUTTON_PRIMARY_BG,
                        color=BUTTON_PRIMARY_TEXT,
                        style=ft.ButtonStyle(elevation=0, shadow_color=ft.Colors.TRANSPARENT),
                        on_click=update_profile,
                    ),
                ]),
                ft.Container(height=6),
                profile_message,
                ft.Container(height=18),
                recent_activity,
            ],
            spacing=0,
        )

    def security_view():
        return ft.Column(
            [
                ft.Text("Change Password", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(height=16),
                ft.Text("Current Password", size=12, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                ft.Container(height=4),
                current_password,
                ft.Container(height=12),
                ft.Text("New Password", size=12, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                ft.Container(height=4),
                new_password,
                ft.Container(height=12),
                ft.Text("Confirm New Password", size=12, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                ft.Container(height=4),
                confirm_password,
                ft.Container(height=12),
                security_message,
                ft.Container(height=14),
                ft.Row(
                    [
                        ft.Container(expand=True),
                        ft.ElevatedButton(
                            "Update Password",
                            width=150,
                            height=38,
                            bgcolor=BUTTON_PRIMARY_BG,
                            color=BUTTON_PRIMARY_TEXT,
                            style=ft.ButtonStyle(elevation=0, shadow_color=ft.Colors.TRANSPARENT),
                            on_click=update_password,
                        ),
                    ]
                ),
            ],
            spacing=0,
        )

    def notifications_view():
        return ft.Column(
            [
                ft.Text("Notification Preferences", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(height=6),
                ft.Text("Choose which updates QualCheck should send you.", size=12, color=TEXT_SECONDARY),
                ft.Container(height=14),
                ft.Row([ft.Text("Email alerts", size=13, color=TEXT_PRIMARY), ft.Container(expand=True), notifications_email]),
                ft.Container(height=8),
                ft.Row([ft.Text("System updates", size=13, color=TEXT_PRIMARY), ft.Container(expand=True), notifications_system]),
                ft.Container(height=8),
                ft.Row([ft.Text("Product news", size=13, color=TEXT_PRIMARY), ft.Container(expand=True), notifications_marketing]),
            ],
            spacing=0,
        )

    content_holder = ft.Container(expand=True)
    left_nav_holder = ft.Container()

    def build_left_nav():
        return ft.Column(
            [
                sidebar_button("Profile", ft.Icons.PERSON_OUTLINE, "profile"),
                ft.Container(height=6),
                sidebar_button("Security", ft.Icons.LOCK_OUTLINE, "security"),
                ft.Container(height=6),
                sidebar_button("Notifications", ft.Icons.NOTIFICATIONS_NONE_OUTLINED, "notifications"),
                ft.Container(height=14),
                ft.Divider(color=BORDER_COLOR),
                ft.Container(height=12),
                ft.Column(
                    [
                        ft.Row([ft.Icon(ft.Icons.BOOKMARK_BORDER, size=15, color=TEXT_TERTIARY), ft.Container(width=8), ft.Text("Evaluations", size=12, color=TEXT_TERTIARY)], spacing=0),
                        ft.Text("81", size=14, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ft.Container(height=12),
                        ft.Row([ft.Icon(ft.Icons.SHIELD_OUTLINED if is_admin else ft.Icons.MENU_BOOK_OUTLINED, size=15, color=TEXT_TERTIARY), ft.Container(width=8), ft.Text("Role", size=12, color=TEXT_TERTIARY)], spacing=0),
                        ft.Text("Admin" if is_admin else "Evaluator", size=13, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                        ft.Container(height=12),
                        ft.Row([ft.Icon(ft.Icons.CALENDAR_MONTH_OUTLINED, size=15, color=TEXT_TERTIARY), ft.Container(width=8), ft.Text("Member since", size=12, color=TEXT_TERTIARY)], spacing=0),
                        ft.Text("Jun 2025", size=13, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                    ],
                    spacing=0,
                ),
            ],
            spacing=0,
        )

    def render_content():
        if active_tab["value"] == "profile":
            content_holder.content = section_card(profile_view())
        elif active_tab["value"] == "security":
            content_holder.content = section_card(security_view())
        else:
            content_holder.content = section_card(notifications_view())
        left_nav_holder.content = build_left_nav()

    top_header = ft.Column(
        [
            ft.Text("Profile Settings", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ft.Text("Manage your account details and preferences", size=12, color=TEXT_SECONDARY),
        ],
        spacing=2,
    )

    card = ft.Container(
        content=ft.Row(
            [
                ft.Container(width=200, content=left_nav_holder),
                ft.Container(width=20),
                content_holder,
            ],
            vertical_alignment=ft.CrossAxisAlignment.START,
        ),
        padding=ft.padding.symmetric(horizontal=0, vertical=0),
        bgcolor=BG_COLOR,
    )

    def back_button():
        return ft.TextButton(
            "Back to admin" if is_admin else "Back to dashboard",
            icon=ft.Icons.ARROW_BACK,
            style=ft.ButtonStyle(color=TEXT_SECONDARY, padding=ft.padding.all(0)),
            on_click=go_back,
        )

    render_content()

    page.add(
        ft.Container(
            content=ft.Column(
                [
                    ft.Container(height=16),
                    ft.Row([top_header, ft.Container(expand=True), back_button()], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Container(height=8),
                    card,
                    ft.Container(height=24),
                ],
                spacing=0,
            ),
            padding=ft.padding.symmetric(horizontal=32, vertical=0),
        )
    )


if __name__ == "__main__":
    ft.app(target=main)