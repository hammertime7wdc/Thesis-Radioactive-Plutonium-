import sys
import os
import base64
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import flet as ft
from services.supabase_client import get_supabase_client
from services.session_manager import get_current_user, clear_session
from services.activity_logger import log_activity, get_recent_activities
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

# Configure Cloudinary
cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
api_key = os.getenv("CLOUDINARY_API_KEY")
api_secret = os.getenv("CLOUDINARY_API_SECRET")

if not all([cloud_name, api_key, api_secret]):
    print("WARNING: Cloudinary credentials not found in .env file")
    print("Required: CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET")

cloudinary.config(
    cloud_name=cloud_name,
    api_key=api_key,
    api_secret=api_secret
)

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

    # Fetch evaluations count
    evaluations_count = 0
    try:
        supabase = get_supabase_client()
        eval_response = supabase.table("evaluations").select("id", count="exact").eq("user_id", user_id).execute()
        evaluations_count = eval_response.count if eval_response.count else 0
    except Exception:
        evaluations_count = 0

    is_admin = profile_data.get("role", "evaluator") == "admin"
    display_name = profile_data.get("name", "User")
    display_email = profile_data.get("email", user_email)
    display_department = profile_data.get("department", "")
    display_institution = profile_data.get("institution", "")
    display_bio = profile_data.get("bio", "")
    display_avatar_url = profile_data.get("avatar_url", "")
    
    # Format member since date
    created_at = profile_data.get("created_at", "")
    if created_at:
        try:
            from datetime import datetime
            if isinstance(created_at, str):
                member_since = datetime.fromisoformat(created_at.replace('Z', '+00:00')).strftime('%b %Y')
            else:
                member_since = str(created_at)[:7]  # YYYY-MM format
        except:
            member_since = "N/A"
    else:
        member_since = "N/A"

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
        nonlocal display_name, display_email, display_department, display_institution, display_bio
        
        # Get values from form fields (direct TextField references)
        new_name = name_field_ref.value if name_field_ref else display_name
        new_email = email_field_ref.value if email_field_ref else display_email
        new_department = department_field_ref.value if department_field_ref else display_department
        new_institution = institution_field_ref.value if institution_field_ref else display_institution
        new_bio = bio_field_ref.value if bio_field_ref else display_bio
        
        try:
            supabase = get_supabase_client()
            update_data = {
                "name": new_name,
                "email": new_email,
                "department": new_department,
                "institution": new_institution,
                "bio": new_bio
            }
            
            # Include avatar URL if it was updated
            if display_avatar_url:
                update_data["avatar_url"] = display_avatar_url
            
            supabase.table("profiles").update(update_data).eq("id", user_id).execute()

            # Update display variables after successful save
            display_name = new_name
            display_email = new_email
            display_department = new_department
            display_institution = new_institution
            display_bio = new_bio

            # Log the activity (disabled - RLS errors)
            # log_activity(user_id, "profile_update", "Updated profile details")

            profile_message.value = "Profile changes saved."
            profile_message.visible = True
            profile_message.color = SUCCESS
            page.update()
        except Exception as ex:
            profile_message.value = f"Error saving profile: {str(ex)}"
            profile_message.visible = True
            profile_message.color = ft.Colors.RED_500
            page.update()

    def pick_avatar(e):
        def on_file_picked(result: ft.FilePickerResultEvent):
            if result.files and result.files[0]:
                file_path = result.files[0].path
                upload_avatar(file_path)
        
        picker = ft.FilePicker(on_result=on_file_picked)
        page.overlay.append(picker)
        page.update()
        picker.pick_files(allowed_extensions=["jpg", "jpeg", "png", "gif", "webp"])

    def upload_avatar(file_path):
        nonlocal display_avatar_url
        
        try:
            # Check if Cloudinary is configured
            if not all([cloud_name, api_key, api_secret]):
                upload_progress.visible = False
                upload_message.value = "Cloudinary not configured. Check .env file."
                upload_message.color = ft.Colors.RED_500
                upload_message.visible = True
                page.update()
                return
            
            upload_progress.visible = True
            upload_message.value = "Uploading..."
            upload_message.visible = True
            page.update()
            
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                file_path,
                folder="avatars",
                public_id=f"{user_id}_{uuid.uuid4().hex}",
                overwrite=True,
                resource_type="image",
                transformation=[
                    {"width": 200, "height": 200, "crop": "fill", "gravity": "face"}
                ]
            )
            
            avatar_url = upload_result.get("secure_url")
            if avatar_url:
                display_avatar_url = avatar_url
                avatar_image.src = avatar_url
                avatar_image.visible = True
                
                upload_progress.visible = False
                upload_message.value = "Avatar uploaded successfully!"
                upload_message.color = SUCCESS
                
                # Re-render profile view to update avatar display
                render_content()
                page.update()
                
                # Log the activity (disabled - RLS errors)
                # log_activity(user_id, "avatar_upload", "Updated profile avatar")
            else:
                raise Exception("No URL returned from Cloudinary")
            
        except Exception as ex:
            upload_progress.visible = False
            error_msg = str(ex)
            print(f"Cloudinary upload error: {error_msg}")
            
            if "invalid signature" in error_msg.lower() or "authentication" in error_msg.lower():
                upload_message.value = "Invalid Cloudinary credentials. Check .env file."
            else:
                upload_message.value = f"Upload failed: {error_msg}"
            
            upload_message.color = ft.Colors.RED_500
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

    # Store direct references to TextField objects
    name_field_ref = None
    email_field_ref = None
    department_field_ref = None
    institution_field_ref = None
    bio_field_ref = None
    avatar_image = ft.Image(width=64, height=64, fit=ft.ImageFit.COVER, border_radius=32)
    upload_progress = ft.ProgressBar(visible=False)
    upload_message = ft.Text("", size=11, color=TEXT_SECONDARY, visible=False)

    def profile_view():
        nonlocal avatar_image, name_field_ref, email_field_ref, department_field_ref, institution_field_ref, bio_field_ref
        
        # Set avatar image if URL exists
        if display_avatar_url:
            avatar_image.src = display_avatar_url
            avatar_image.visible = True
        else:
            avatar_image.visible = False
        
        # Avatar container with upload button
        avatar_container = ft.Stack(
            [
                ft.Container(
                    content=avatar_image if display_avatar_url else ft.Text(
                        display_name[0].upper() if display_name else "A",
                        size=26,
                        weight=ft.FontWeight.BOLD,
                        color=TEXT_WHITE
                    ),
                    width=64,
                    height=64,
                    border_radius=32,
                    bgcolor=PRIMARY_BLUE if not display_avatar_url else None,
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
                    on_click=pick_avatar,
                    ink=True,
                ),
            ],
            width=64,
            height=64,
        )

        info_row = ft.Row(
            [
                avatar_container,
                ft.Container(width=14),
                ft.Column(
                    [
                        ft.Text(display_name, size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ft.Text(display_email, size=12, color=TEXT_SECONDARY),
                        ft.Container(height=4),
                        role_pill(),
                        ft.Container(height=2),
                        upload_message,
                    ],
                    spacing=2,
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Fetch recent activities
        activities = get_recent_activities(user_id, limit=3)
        
        # Build activity list
        activity_items = []
        if activities:
            activity_items.append(ft.Text("Recent Activity", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY))
            activity_items.append(ft.Container(height=10))
            
            for activity in activities:
                # Map activity types to icons
                icon_map = {
                    'profile_update': ft.Icons.EDIT_OUTLINED,
                    'avatar_upload': ft.Icons.CAMERA_ALT_OUTLINED,
                    'password_change': ft.Icons.LOCK_OUTLINED,
                    'default': ft.Icons.HISTORY_OUTLINED
                }
                icon = icon_map.get(activity.get('activity_type'), icon_map['default'])
                
                description = activity.get('description', 'Unknown activity')
                activity_items.append(
                    ft.Row([ft.Icon(icon, size=16, color=TEXT_SECONDARY), ft.Container(width=10), ft.Text(description, size=12, color=TEXT_PRIMARY)], spacing=0)
                )
                activity_items.append(ft.Container(height=8))
        else:
            activity_items.append(ft.Text("Recent Activity", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY))
            activity_items.append(ft.Container(height=10))
            activity_items.append(ft.Text("No recent activity", size=12, color=TEXT_SECONDARY))
        
        recent_activity = ft.Container(
            content=ft.Column(activity_items, spacing=0),
            padding=ft.padding.all(16),
            bgcolor=SECTION_BG_COLOR,
            border_radius=10,
            border=ft.border.all(1, BORDER_COLOR),
        )

        # Create TextField objects directly and store references
        name_field_ref = ft.TextField(
            value=display_name,
            width=290,
            border_radius=8,
            bgcolor=INPUT_BG,
            border_color=INPUT_BORDER,
            focused_border_color=PRIMARY_BLUE,
            color=INPUT_TEXT,
            text_size=13,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=10),
        )
        
        email_field_ref = ft.TextField(
            value=display_email,
            width=290,
            border_radius=8,
            bgcolor=INPUT_BG,
            border_color=INPUT_BORDER,
            focused_border_color=PRIMARY_BLUE,
            color=INPUT_TEXT,
            text_size=13,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=10),
        )
        
        department_field_ref = ft.TextField(
            value=display_department,
            width=290,
            border_radius=8,
            bgcolor=INPUT_BG,
            border_color=INPUT_BORDER,
            focused_border_color=PRIMARY_BLUE,
            color=INPUT_TEXT,
            text_size=13,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=10),
        )
        
        institution_field_ref = ft.TextField(
            value=display_institution,
            width=290,
            border_radius=8,
            bgcolor=INPUT_BG,
            border_color=INPUT_BORDER,
            focused_border_color=PRIMARY_BLUE,
            color=INPUT_TEXT,
            text_size=13,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=10),
        )
        
        bio_field_ref = ft.TextField(
            value=display_bio,
            width=594,
            multiline=True,
            min_lines=2,
            max_lines=3,
            border_radius=8,
            bgcolor=INPUT_BG,
            border_color=INPUT_BORDER,
            focused_border_color=PRIMARY_BLUE,
            color=INPUT_TEXT,
            text_size=13,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=10),
        )

        return ft.Column(
            [
                ft.Text("Personal Information", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Container(height=12),
                info_row,
                ft.Container(height=18),
                ft.Row(
                    [
                        ft.Column([
                            ft.Text("Full Name", size=12, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                            ft.Container(height=4),
                            name_field_ref,
                        ], spacing=0),
                        ft.Column([
                            ft.Text("Email Address", size=12, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                            ft.Container(height=4),
                            email_field_ref,
                        ], spacing=0),
                    ],
                    spacing=14,
                ),
                ft.Container(height=12),
                ft.Row(
                    [
                        ft.Column([
                            ft.Text("Department", size=12, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                            ft.Container(height=4),
                            department_field_ref,
                        ], spacing=0),
                        ft.Column([
                            ft.Text("Institution", size=12, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                            ft.Container(height=4),
                            institution_field_ref,
                        ], spacing=0),
                    ],
                    spacing=14,
                ),
                ft.Container(height=12),
                ft.Column([
                    ft.Text("Bio", size=12, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                    ft.Container(height=4),
                    bio_field_ref,
                ], spacing=0),
                ft.Container(height=14),
                upload_progress,
                ft.Container(height=6),
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
                        ft.Text(str(evaluations_count), size=14, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ft.Container(height=12),
                        ft.Row([ft.Icon(ft.Icons.SHIELD_OUTLINED if is_admin else ft.Icons.MENU_BOOK_OUTLINED, size=15, color=TEXT_TERTIARY), ft.Container(width=8), ft.Text("Role", size=12, color=TEXT_TERTIARY)], spacing=0),
                        ft.Text("Admin" if is_admin else "Evaluator", size=13, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                        ft.Container(height=12),
                        ft.Row([ft.Icon(ft.Icons.CALENDAR_MONTH_OUTLINED, size=15, color=TEXT_TERTIARY), ft.Container(width=8), ft.Text("Member since", size=12, color=TEXT_TERTIARY)], spacing=0),
                        ft.Text(member_since, size=13, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
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