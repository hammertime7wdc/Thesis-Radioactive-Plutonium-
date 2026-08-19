import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import flet as ft
from services.supabase_client import get_supabase_client, verify_user_password
from services.session_manager import get_current_user, clear_session
from services.activity_logger import log_activity, get_recent_activities
from services.avatar_service import upload_avatar_image

try:
    from database.auth import (
        resend_password_reset_email,
        send_password_reset_email,
        reset_password_with_token,
    )
except ModuleNotFoundError:
    def send_password_reset_email(email: str):
        return False, "Database not available"
    def resend_password_reset_email(email: str):
        return False, "Database not available"
    def reset_password_with_token(token: str, new_password: str):
        return False, "Database not available"

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
from utils.resend_control import build_resend_code_control


def main(page: ft.Page, nav=None, role="evaluator"):
    page.title = "QualCheck - Account Settings"
    page.scroll = ft.ScrollMode.AUTO
    page.bgcolor = BG_COLOR
    page.theme_mode = ft.ThemeMode.LIGHT

    active_tab = {"value": "profile"}
    # "form" = enter current/new/confirm password; "verify" = enter emailed code
    security_step = {"value": "form"}
    pending_new_password = {"value": ""}

    # Load user profile from Supabase
    user = get_current_user()
    if not user:
        # If no session, redirect to login
        if nav and hasattr(nav, "navigate_to_login"):
            nav.navigate_to_login()
        return

    user_id = user.user.id
    user_email = user.user.email

    # Dictionary state to allow updating inside async thread and callbacks
    state = {
        "loading": True,
        "is_admin": role == "admin",
        "display_name": "User",
        "display_email": user_email,
        "display_department": "",
        "display_institution": "",
        "display_bio": "",
        "display_avatar_url": "",
        "evaluations_count": 0,
        "member_since": "Loading...",
        "activities": []
    }

    # Fetch user profile data synchronously to avoid loading spinner flash
    try:
        # 1. Fetch profile
        supabase = get_supabase_client()
        profile_response = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
        p_data = profile_response.data if profile_response.data else {}
        
        # 2. Fetch evaluations count
        eval_response = supabase.table("evaluations").select("id", count="exact").eq("user_id", user_id).execute()
        e_count = eval_response.count if eval_response.count else 0
        
        # 3. Fetch activities
        recent_acts = get_recent_activities(user_id, limit=3)
        
        # 4. Format date
        created_at = p_data.get("created_at", "")
        m_since = "N/A"
        if created_at:
            try:
                from datetime import datetime
                if isinstance(created_at, str):
                    m_since = datetime.fromisoformat(created_at.replace('Z', '+00:00')).strftime('%b %Y')
                else:
                    m_since = str(created_at)[:7]
            except:
                m_since = "N/A"

        # Update state dict
        state["profile_data"] = p_data
        state["is_admin"] = p_data.get("role", "evaluator") == "admin"
        state["display_name"] = p_data.get("name", "User")
        state["display_email"] = p_data.get("email", user_email)
        state["display_department"] = p_data.get("department", "")
        state["display_institution"] = p_data.get("institution", "")
        state["display_bio"] = p_data.get("bio", "")
        state["display_avatar_url"] = p_data.get("avatar_url", "")
        state["evaluations_count"] = e_count
        state["member_since"] = m_since
        state["activities"] = recent_acts
    except Exception as e:
        print(f"Profile load error: {e}")

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
        role_icon = ft.Icons.SHIELD_OUTLINED if state["is_admin"] else ft.Icons.MENU_BOOK_OUTLINED
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(role_icon, size=12, color=TEXT_SECONDARY),
                    ft.Container(width=4),
                    ft.Text("Admin" if state["is_admin"] else "Evaluator", size=11, weight=ft.FontWeight.W_600, color=TEXT_SECONDARY),
                ],
                spacing=0,
                tight=True,
            ),
            padding=ft.padding.symmetric(horizontal=8, vertical=3),
            bgcolor=SECTION_BG_COLOR,
            border=ft.border.all(1, BORDER_COLOR),
            border_radius=999,
        )

    # ── Security tab fields (persist across re-renders of this tab) ──
    def _security_field(hint, password=False, read_only=False):
        return ft.TextField(
            hint_text=hint,
            password=password,
            can_reveal_password=password,
            read_only=read_only,
            value=user_email if read_only else None,
            width=520,
            height=42,
            border_radius=8,
            bgcolor=INPUT_BG,
            border_color=INPUT_BORDER,
            focused_border_color=PRIMARY_BLUE,
            text_size=13,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=8),
        )

    reset_email_field = _security_field("Email address", read_only=True)
    current_password = _security_field("Current password", password=True)
    new_password = _security_field("Min. 8 chars: 1 lowercase, 1 uppercase, 1 number, 1 special", password=True)
    confirm_password = _security_field("Confirm new password", password=True)
    code_field = ft.TextField(
        hint_text="• • • • • •",
        width=520,
        height=48,
        border_radius=8,
        bgcolor=INPUT_BG,
        border_color=INPUT_BORDER,
        focused_border_color=PRIMARY_BLUE,
        text_size=16,
        text_align=ft.TextAlign.CENTER,
        content_padding=ft.padding.symmetric(horizontal=12, vertical=10),
        hint_style=ft.TextStyle(color=INPUT_HINT, letter_spacing=4),
        max_length=6,
        input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]"),
    )
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
        if state["is_admin"] and hasattr(nav, "navigate_to_admin"):
            nav.navigate_to_admin()
        elif hasattr(nav, "navigate_to_new_evaluation"):
            nav.navigate_to_new_evaluation()
        elif hasattr(nav, "navigate_to_short_answer"):
            nav.navigate_to_short_answer()

    def refresh_recent_activity():
        try:
            state["activities"] = get_recent_activities(user_id, limit=5)
        except Exception as ex:
            print(f"Activity refresh error: {ex}")
            state["activities"] = []

    def set_profile_save_button_loading(is_loading: bool):
        if not hasattr(profile_page_state, "save_button") or profile_page_state["save_button"] is None:
            return
        button = profile_page_state["save_button"]
        if is_loading:
            button.content = ft.Row(
                [
                    ft.ProgressRing(width=14, height=14, stroke_width=2, color=BUTTON_PRIMARY_TEXT),
                    ft.Text("Saving...", size=12, weight=ft.FontWeight.BOLD, color=BUTTON_PRIMARY_TEXT),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            )
        else:
            button.content = ft.Row(
                [
                    ft.Text("Save Changes", size=12, weight=ft.FontWeight.BOLD, color=BUTTON_PRIMARY_TEXT),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=0,
            )
        page.update()

    profile_page_state = {"save_button": None}

    def update_profile(e):
        # Get values from form fields (direct TextField references)
        new_name = name_field_ref.value if name_field_ref else state["display_name"]
        new_email = email_field_ref.value if email_field_ref else state["display_email"]
        new_department = department_field_ref.value if department_field_ref else state["display_department"]
        new_institution = institution_field_ref.value if institution_field_ref else state["display_institution"]
        new_bio = bio_field_ref.value if bio_field_ref else state["display_bio"]
        set_profile_save_button_loading(True)
        
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
            if state["display_avatar_url"]:
                update_data["avatar_url"] = state["display_avatar_url"]
            
            supabase.table("profiles").update(update_data).eq("id", user_id).execute()

            # Update display variables after successful save
            state["display_name"] = new_name
            state["display_email"] = new_email
            state["display_department"] = new_department
            state["display_institution"] = new_institution
            state["display_bio"] = new_bio

            log_activity(user_id, "profile_update", "Updated profile details")
            refresh_recent_activity()

            profile_message.value = "Profile changes saved."
            profile_message.visible = True
            profile_message.color = SUCCESS
            set_profile_save_button_loading(False)
            page.update()
        except Exception as ex:
            set_profile_save_button_loading(False)
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
        try:
            upload_progress.visible = True
            upload_message.value = "Uploading..."
            upload_message.visible = True
            page.update()

            avatar_url = upload_avatar_image(file_path, user_id)

            state["display_avatar_url"] = avatar_url
            avatar_image.src = avatar_url
            avatar_image.visible = True

            upload_progress.visible = False
            upload_message.value = "Avatar uploaded successfully!"
            upload_message.color = SUCCESS

            log_activity(user_id, "avatar_upload", "Updated profile avatar")
            refresh_recent_activity()

            # Re-render profile view to update avatar display
            render_content()
            page.update()

        except Exception as ex:
            upload_progress.visible = False
            error_msg = str(ex)
            print(f"Avatar upload error: {error_msg}")

            if "invalid signature" in error_msg.lower() or "authentication" in error_msg.lower():
                upload_message.value = "Invalid Cloudinary credentials. Check .env file."
            elif "not configured" in error_msg.lower():
                upload_message.value = error_msg
            else:
                upload_message.value = f"Upload failed: {error_msg}"

            upload_message.color = ft.Colors.RED_500
            page.update()

    # ── Step 1: verify current password + validate new password, then email a code ──
    def set_security_button_loading(is_loading: bool, label: str, button_ref):
        if button_ref is None:
            return
        if is_loading:
            button_ref.content = ft.Row(
                [
                    ft.ProgressRing(width=14, height=14, stroke_width=2, color=BUTTON_PRIMARY_TEXT),
                    ft.Text(label, size=12, weight=ft.FontWeight.BOLD, color=BUTTON_PRIMARY_TEXT),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            )
        else:
            button_ref.content = ft.Row(
                [
                    ft.Text(label, size=12, weight=ft.FontWeight.BOLD, color=BUTTON_PRIMARY_TEXT),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=0,
            )
        page.update()

    security_button_state = {"send_reset": None, "update_password": None}

    def send_verification_code(e):
        security_message.visible = False

        if not current_password.value or not new_password.value or not confirm_password.value:
            security_message.value = "Please fill in your current password and the new password fields."
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

        if security_button_state["send_reset"] is not None:
            set_security_button_loading(True, "Sending code...", security_button_state["send_reset"])

        from database.auth import validate_password as validate_account_password
        is_valid, password_error = validate_account_password(new_password.value)
        if not is_valid:
            security_message.value = password_error
            security_message.color = ft.Colors.RED_500
            security_message.visible = True
            if security_button_state["send_reset"] is not None:
                set_security_button_loading(False, "Send Reset Code", security_button_state["send_reset"])
            page.update()
            return

        if not verify_user_password(user_email, current_password.value):
            security_message.value = "Current password is incorrect."
            security_message.color = ft.Colors.RED_500
            security_message.visible = True
            if security_button_state["send_reset"] is not None:
                set_security_button_loading(False, "Send Reset Code", security_button_state["send_reset"])
            page.update()
            return

        success, resp = send_password_reset_email(reset_email_field.value or user_email)
        if success:
            pending_new_password["value"] = new_password.value
            security_step["value"] = "verify"
            security_message.value = "Verification code sent to your email."
            security_message.color = SUCCESS
            security_message.visible = True
            render_content()
        else:
            security_message.value = resp
            security_message.color = ft.Colors.RED_500
            security_message.visible = True
        if security_button_state["send_reset"] is not None:
            set_security_button_loading(False, "Send Reset Code", security_button_state["send_reset"])
        page.update()

    # ── Step 2: verify the emailed code, then finalize the password change ──
    def verify_and_update(e):
        security_message.visible = False

        if not code_field.value:
            security_message.value = "Please enter the verification code."
            security_message.color = ft.Colors.RED_500
            security_message.visible = True
            page.update()
            return
        if len(code_field.value.strip()) != 6:
            security_message.value = "Please enter the 6-digit verification code."
            security_message.color = ft.Colors.RED_500
            security_message.visible = True
            page.update()
            return

        password_to_set = pending_new_password["value"] or new_password.value
        if not password_to_set:
            security_message.value = "Please send a reset code first."
            security_message.color = ft.Colors.RED_500
            security_message.visible = True
            page.update()
            return

        if security_button_state["update_password"] is not None:
            set_security_button_loading(True, "Updating...", security_button_state["update_password"])

        ok, msg = reset_password_with_token(code_field.value, password_to_set)
        if ok:
            security_message.value = "Password updated successfully."
            security_message.color = SUCCESS
            log_activity(user_id, "password_change", "Changed account password")
            refresh_recent_activity()
            # Reset everything back to step 1, cleared
            current_password.value = ""
            new_password.value = ""
            confirm_password.value = ""
            code_field.value = ""
            pending_new_password["value"] = ""
            security_step["value"] = "form"
            render_content()
        else:
            security_message.value = msg
            security_message.color = ft.Colors.RED_500
        if security_button_state["update_password"] is not None:
            set_security_button_loading(False, "Update Password", security_button_state["update_password"])
        security_message.visible = True
        page.update()

    current_password.on_submit = send_verification_code
    new_password.on_submit = send_verification_code
    confirm_password.on_submit = send_verification_code
    code_field.on_submit = verify_and_update

    resend_processing = {"value": False}

    def resend_verification_code(e):
        if resend_processing["value"]:
            return
        resend_processing["value"] = True
        security_message.visible = False
        page.update()

        try:
            success, resp = resend_password_reset_email(reset_email_field.value or user_email)
            if success:
                security_message.value = "A new code was sent to your email."
                security_message.color = SUCCESS
                code_field.value = ""
            else:
                security_message.value = resp
                security_message.color = ft.Colors.RED_500
            security_message.visible = True
        finally:
            resend_processing["value"] = False
            page.update()

    def back_to_password_form(e):
        security_step["value"] = "form"
        security_message.visible = False
        code_field.value = ""
        render_content()
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

    def build_recent_activity_section():
        activities = state.get("activities", []) or []
        activity_items = [
            ft.Text("Recent Activity", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ft.Container(height=10),
        ]

        if activities:
            for activity in activities:
                icon_map = {
                    'profile_update': ft.Icons.EDIT_OUTLINED,
                    'avatar_upload': ft.Icons.CAMERA_ALT_OUTLINED,
                    'password_change': ft.Icons.LOCK_OUTLINED,
                    'default': ft.Icons.HISTORY_OUTLINED,
                }
                icon = icon_map.get(activity.get('activity_type'), icon_map['default'])
                description = activity.get('description', 'Unknown activity')
                activity_items.append(
                    ft.Row(
                        [
                            ft.Icon(icon, size=16, color=TEXT_SECONDARY),
                            ft.Container(width=10),
                            ft.Text(description, size=12, color=TEXT_PRIMARY),
                        ],
                        spacing=0,
                    )
                )
                activity_items.append(ft.Container(height=8))
        else:
            activity_items.append(ft.Text("No recent activity", size=12, color=TEXT_SECONDARY))

        return ft.Container(
            content=ft.Column(activity_items, spacing=0),
            padding=ft.padding.all(16),
            bgcolor=SECTION_BG_COLOR,
            border_radius=10,
            border=ft.border.all(1, BORDER_COLOR),
        )

    def profile_view():
        nonlocal avatar_image, name_field_ref, email_field_ref, department_field_ref, institution_field_ref, bio_field_ref
        
        # Set avatar image if URL exists
        if state["display_avatar_url"]:
            avatar_image.src = state["display_avatar_url"]
            avatar_image.visible = True
        else:
            avatar_image.visible = False
        
        # Avatar container with upload button
        avatar_container = ft.Stack(
            [
                ft.Container(
                    content=avatar_image if state["display_avatar_url"] else ft.Text(
                        state["display_name"][0].upper() if state["display_name"] else "A",
                        size=26,
                        weight=ft.FontWeight.BOLD,
                        color=TEXT_WHITE
                    ),
                    width=64,
                    height=64,
                    border_radius=32,
                    bgcolor=PRIMARY_BLUE if not state["display_avatar_url"] else None,
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
                        ft.Text(state["display_name"], size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ft.Text(state["display_email"], size=12, color=TEXT_SECONDARY),
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
 
        recent_activity = build_recent_activity_section()

        # Create TextField objects directly and store references
        name_field_ref = ft.TextField(
            value=state["display_name"],
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
            value=state["display_email"],
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
            value=state["display_department"],
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
            value=state["display_institution"],
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
            value=state["display_bio"],
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
        name_field_ref.on_submit = update_profile
        email_field_ref.on_submit = update_profile
        department_field_ref.on_submit = update_profile
        institution_field_ref.on_submit = update_profile
        bio_field_ref.on_submit = update_profile

        save_btn = ft.ElevatedButton(
            content=ft.Row(
                [ft.Text("Save Changes", size=12, weight=ft.FontWeight.BOLD, color=BUTTON_PRIMARY_TEXT)],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=0,
            ),
            width=130,
            height=38,
            bgcolor=BUTTON_PRIMARY_BG,
            color=BUTTON_PRIMARY_TEXT,
            style=ft.ButtonStyle(elevation=0, shadow_color=ft.Colors.TRANSPARENT),
            on_click=update_profile,
        )
        profile_page_state["save_button"] = save_btn

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
                ft.Container(height=8),
                ft.Row([
                    ft.Container(expand=True),
                    save_btn,
                ]),
                ft.Container(height=6),
                profile_message,
                ft.Container(height=18),
                recent_activity,
            ],
            spacing=0,
        )

    def security_view():
        if security_step["value"] == "form":
            send_reset_btn = ft.ElevatedButton(
                content=ft.Row(
                    [ft.Text("Send Reset Code", size=12, weight=ft.FontWeight.BOLD, color=BUTTON_PRIMARY_TEXT)],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=0,
                ),
                width=180,
                height=42,
                bgcolor=BUTTON_PRIMARY_BG,
                color=BUTTON_PRIMARY_TEXT,
                style=ft.ButtonStyle(elevation=0, shadow_color=ft.Colors.TRANSPARENT),
                on_click=send_verification_code,
            )
            security_button_state["send_reset"] = send_reset_btn
            return ft.Column(
                [
                    ft.Text("Change Password", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ft.Container(height=10),
                    ft.Text("We'll send a reset code to your email, then you can choose a new password.", size=12, color=TEXT_SECONDARY),
                    ft.Container(height=16),
                    ft.Text("Email Address", size=12, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                    ft.Container(height=4),
                    reset_email_field,
                    ft.Container(height=16),
                    ft.Text("Current Password", size=12, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                    ft.Container(height=4),
                    current_password,
                    ft.Container(height=16),
                    ft.Text("New Password", size=12, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                    ft.Container(height=4),
                    new_password,
                    ft.Container(height=16),
                    ft.Text("Confirm New Password", size=12, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                    ft.Container(height=4),
                    confirm_password,
                    ft.Container(height=16),
                    security_message,
                    ft.Container(height=8),
                    ft.Row(
                        [
                            ft.Container(expand=True),
                            send_reset_btn,
                        ]
                    ),
                ],
                spacing=0,
            )
        else:
            update_password_btn = ft.ElevatedButton(
                content=ft.Row(
                    [ft.Text("Update Password", size=12, weight=ft.FontWeight.BOLD, color=BUTTON_PRIMARY_TEXT)],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=0,
                ),
                width=160,
                height=42,
                bgcolor=BUTTON_PRIMARY_BG,
                color=BUTTON_PRIMARY_TEXT,
                style=ft.ButtonStyle(elevation=0, shadow_color=ft.Colors.TRANSPARENT),
                on_click=verify_and_update,
            )
            security_button_state["update_password"] = update_password_btn
            return ft.Column(
                [
                    ft.Text("Change Password", size=15, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ft.Container(height=10),
                    ft.Text(
                        f"We sent a 6-digit code to {reset_email_field.value or user_email}. Enter it below to confirm the change.",
                        size=12,
                        color=TEXT_SECONDARY,
                    ),
                    ft.Container(height=16),
                    ft.Text("Verification Code", size=12, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                    ft.Container(height=4),
                    code_field,
                    ft.Container(height=8),
                    ft.Container(
                        content=build_resend_code_control(
                            on_click=resend_verification_code,
                            label_color=TEXT_SECONDARY,
                            action_color=PRIMARY_BLUE,
                        ),
                        width=520,
                        alignment=ft.alignment.center_left,
                    ),
                    ft.Container(height=16),
                    security_message,
                    ft.Container(height=8),
                    ft.Row(
                        [
                            ft.TextButton(
                                "Back",
                                style=ft.ButtonStyle(color=TEXT_SECONDARY),
                                on_click=back_to_password_form,
                            ),
                            ft.Container(expand=True),
                            update_password_btn,
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
                        ft.Text(str(state["evaluations_count"]), size=14, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ft.Container(height=12),
                        ft.Row([ft.Icon(ft.Icons.SHIELD_OUTLINED if state["is_admin"] else ft.Icons.MENU_BOOK_OUTLINED, size=15, color=TEXT_TERTIARY), ft.Container(width=8), ft.Text("Role", size=12, color=TEXT_TERTIARY)], spacing=0),
                        ft.Text("Admin" if state["is_admin"] else "Evaluator", size=13, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                        ft.Container(height=12),
                        ft.Row([ft.Icon(ft.Icons.CALENDAR_MONTH_OUTLINED, size=15, color=TEXT_TERTIARY), ft.Container(width=8), ft.Text("Member since", size=12, color=TEXT_TERTIARY)], spacing=0),
                        ft.Text(state["member_since"], size=13, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
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
            "Back to admin" if state["is_admin"] else "Back to evaluation selection",
            icon=ft.Icons.ARROW_BACK,
            style=ft.ButtonStyle(color=TEXT_SECONDARY, padding=ft.padding.all(0)),
            on_click=go_back,
        )

    render_content()

    main_content = ft.Container(
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

    if nav:
        nav.main_content = main_content
    else:
        page.add(main_content)


if __name__ == "__main__":
    ft.app(target=main)