import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import flet as ft
from services.supabase_client import get_supabase_client
from services.user_service import add_user
from utils.utils import (
    BG_COLOR, CARD_BG_COLOR, SECTION_BG_COLOR,
    PRIMARY_BLUE, PRIMARY_BLUE_DARK, PRIMARY_BLUE_LIGHT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_TERTIARY, TEXT_WHITE,
    BORDER_COLOR, BORDER_COLOR_DARK,
    BUTTON_PRIMARY_BG, BUTTON_PRIMARY_TEXT, BUTTON_SECONDARY_BG, BUTTON_SECONDARY_TEXT, BUTTON_SECONDARY_BORDER,
    INPUT_BG, INPUT_BORDER, INPUT_TEXT, INPUT_HINT,
    SUCCESS, WARNING, ERROR
)


def main(page: ft.Page, nav=None):
    page.title = "QualCheck Admin Panel"
    page.scroll = ft.ScrollMode.AUTO
    page.bgcolor = BG_COLOR

    # Fetch real users from profiles table
    users_data = []
    try:
        supabase = get_supabase_client()
        profiles_response = supabase.table("profiles").select("*").execute()
        users_data = profiles_response.data if profiles_response.data else []
    except Exception as e:
        print(f"Error fetching users: {e}")
        users_data = []

    # Fetch evaluation counts for each user
    for user in users_data:
        try:
            supabase = get_supabase_client()
            eval_response = supabase.table("evaluations").select("id", count="exact").eq("user_id", user["id"]).execute()
            user["evaluations_count"] = eval_response.count if eval_response.count else 0
        except Exception:
            user["evaluations_count"] = 0

    # Only create header if not using admin navigation (navigation handles it)
    if not nav:
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
    else:
        admin_header = None

    # Helpers for rendering table cells matching the screenshot
    def create_name_cell(avatar_text, full_name):
        return ft.DataCell(
            ft.Row(
                [
                    ft.Container(
                        content=ft.Text(avatar_text, size=11, weight=ft.FontWeight.BOLD, color=PRIMARY_BLUE),
                        width=24,
                        height=24,
                        border_radius=12,
                        bgcolor="#eff6ff",
                        alignment=ft.alignment.center,
                    ),
                    ft.Container(width=8),
                    ft.Text(full_name, size=13, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )

    def create_role_badge(role):
        if role == "Admin":
            return ft.DataCell(
                ft.Container(
                    content=ft.Text("Admin", size=12, color="#7e22ce", weight=ft.FontWeight.W_600),
                    bgcolor="#f3e8ff",
                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                    border_radius=12,
                )
            )
        else:
            return ft.DataCell(
                ft.Container(
                    content=ft.Text("Evaluator", size=12, color=PRIMARY_BLUE, weight=ft.FontWeight.W_600),
                    bgcolor="#eff6ff",
                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                    border_radius=12,
                )
            )

    def create_status_badge(status):
        if status == "Active":
            return ft.DataCell(
                ft.Container(
                    content=ft.Text("Active", size=12, color=SUCCESS, weight=ft.FontWeight.W_600),
                    bgcolor="#ecfdf5",
                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                    border_radius=12,
                )
            )
        else:
            return ft.DataCell(
                ft.Container(
                    content=ft.Text("Inactive", size=12, color=TEXT_SECONDARY, weight=ft.FontWeight.W_600),
                    bgcolor="#f1f5f9",
                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                    border_radius=12,
                )
            )

    # --- Users Table ---
    # Build dynamic rows from real user data
    table_rows = []
    for user in users_data:
        name = user.get("name", "Unknown")
        email = user.get("email", "")
        role = user.get("role", "evaluator")
        department = user.get("department", "N/A")
        evaluations_count = user.get("evaluations_count", 0)
        created_at = user.get("created_at", "")

        # Format created_at date
        if created_at:
            try:
                from datetime import datetime
                if isinstance(created_at, str):
                    created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                else:
                    created_date = str(created_at)[:10]
            except Exception:
                created_date = str(created_at)[:10] if created_at else "N/A"
        else:
            created_date = "N/A"

        # Get initials for avatar
        if name:
            initials = "".join([word[0].upper() for word in name.split() if word])[:2]
        else:
            initials = "U"
        if not initials:
            initials = "U"

        table_rows.append(
            ft.DataRow(
                cells=[
                    create_name_cell(initials, name),
                    ft.DataCell(ft.Text(email, size=13, color=TEXT_SECONDARY)),
                    create_role_badge(role.capitalize()),
                    ft.DataCell(ft.Text(department, size=13, color=TEXT_SECONDARY)),
                    ft.DataCell(ft.Text(str(evaluations_count), size=13, weight=ft.FontWeight.W_500, color=TEXT_PRIMARY)),
                    ft.DataCell(ft.Text(created_date, size=13, color=TEXT_SECONDARY)),
                    create_status_badge("Active"),
                ],
            )
        )

    users_table = ft.DataTable(
        columns=[
            ft.DataColumn(
                ft.Text("NAME", size=12, weight=ft.FontWeight.BOLD, color=TEXT_SECONDARY),
            ),
            ft.DataColumn(
                ft.Text("EMAIL", size=12, weight=ft.FontWeight.BOLD, color=TEXT_SECONDARY),
            ),
            ft.DataColumn(
                ft.Text("ROLE", size=12, weight=ft.FontWeight.BOLD, color=TEXT_SECONDARY),
            ),
            ft.DataColumn(
                ft.Text("SUBJECT", size=12, weight=ft.FontWeight.BOLD, color=TEXT_SECONDARY),
            ),
            ft.DataColumn(
                ft.Text("EVALUATIONS", size=12, weight=ft.FontWeight.BOLD, color=TEXT_SECONDARY),
            ),
            ft.DataColumn(
                ft.Text("JOINED", size=12, weight=ft.FontWeight.BOLD, color=TEXT_SECONDARY),
            ),
            ft.DataColumn(
                ft.Text("STATUS", size=12, weight=ft.FontWeight.BOLD, color=TEXT_SECONDARY),
            ),
        ],
        border=ft.border.all(1, BORDER_COLOR),
        border_radius=8,
        horizontal_lines=ft.border.BorderSide(1, BORDER_COLOR),
        vertical_lines=None,
        column_spacing=54,
        heading_row_color=SECTION_BG_COLOR,
        data_row_min_height=56,
        show_bottom_border=True,
        rows=table_rows if table_rows else [ft.DataRow(cells=[ft.DataCell(ft.Text("No users found", color=TEXT_SECONDARY))])],
    )

    # ------------------------------------------------------------------
    # --- Add User Dialog (redesigned) ---
    # ------------------------------------------------------------------
    def on_add_user(e):
        # Field style shared across all inputs for a consistent, quieter look
        def styled_field(**kwargs):
            return ft.TextField(
                border_color=INPUT_BORDER,
                focused_border_color=PRIMARY_BLUE,
                bgcolor=INPUT_BG,
                hint_style=ft.TextStyle(color=INPUT_HINT, size=13),
                text_style=ft.TextStyle(color=INPUT_TEXT, size=13),
                border_radius=8,
                content_padding=ft.padding.symmetric(horizontal=14, vertical=12),
                **kwargs,
            )

        name_field = styled_field(
            label="Full Name",
            hint_text="Juan Dela Cruz",
            prefix_icon=ft.Icons.PERSON_OUTLINE,
        )

        email_field = styled_field(
            label="Email Address",
            hint_text="juan@university.edu.ph",
            prefix_icon=ft.Icons.MAIL_OUTLINE,
            keyboard_type=ft.KeyboardType.EMAIL,
        )

        password_field = styled_field(
            label="Password",
            hint_text="Enter password (leave blank to auto-generate)",
            prefix_icon=ft.Icons.LOCK_OUTLINE,
            password=True,
            can_reveal_password=True,
        )

        # Password strength indicator
        password_strength_text = ft.Text("", size=11, color=TEXT_SECONDARY)
        password_requirements = ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=12, color=SUCCESS, visible=False),
                        ft.Container(width=6),
                        ft.Text("At least 8 characters", size=11, color=TEXT_TERTIARY),
                    ],
                ),
                ft.Row(
                    [
                        ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=12, color=SUCCESS, visible=False),
                        ft.Container(width=6),
                        ft.Text("At least 1 uppercase letter", size=11, color=TEXT_TERTIARY),
                    ],
                ),
                ft.Row(
                    [
                        ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=12, color=SUCCESS, visible=False),
                        ft.Container(width=6),
                        ft.Text("At least 1 number", size=11, color=TEXT_TERTIARY),
                    ],
                ),
                ft.Row(
                    [
                        ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=12, color=SUCCESS, visible=False),
                        ft.Container(width=6),
                        ft.Text("At least 1 special character", size=11, color=TEXT_TERTIARY),
                    ],
                ),
            ],
            spacing=4,
        )

        def check_password_strength(password: str):
            """Update password strength indicator in real-time"""
            if not password:
                password_strength_text.value = ""
                password_strength_text.color = TEXT_SECONDARY
                for row in password_requirements.controls:
                    row.controls[0].visible = False
                    row.controls[2].color = TEXT_TERTIARY
                dialog.update()
                return

            checks = [
                len(password) >= 8,
                any(c.isupper() for c in password),
                any(c.isdigit() for c in password),
                any(c in '!@#$%^&*(),.?":{}|<>' for c in password)
            ]

            all_passed = all(checks)
            passed_count = sum(checks)

            if all_passed:
                password_strength_text.value = "Strong password"
                password_strength_text.color = SUCCESS
            elif passed_count >= 2:
                password_strength_text.value = "Medium password"
                password_strength_text.color = WARNING
            elif passed_count >= 1:
                password_strength_text.value = "Weak password"
                password_strength_text.color = ERROR
            else:
                password_strength_text.value = "Too weak"
                password_strength_text.color = ERROR

            # Update requirement checkmarks
            for i, row in enumerate(password_requirements.controls):
                row.controls[0].visible = checks[i]
                row.controls[2].color = TEXT_PRIMARY if checks[i] else TEXT_TERTIARY

            dialog.update()

        password_field.on_change = lambda e: (check_password_strength(e.control.value), clear_field_errors(e))

        role_dropdown = ft.Dropdown(
            label="Role",
            options=[
                ft.dropdown.Option("evaluator", "Evaluator"),
                ft.dropdown.Option("admin", "Administrator"),
            ],
            value="evaluator",
            border_color=INPUT_BORDER,
            focused_border_color=PRIMARY_BLUE,
            bgcolor=INPUT_BG,
            border_radius=8,
            content_padding=ft.padding.symmetric(horizontal=14, vertical=12),
            expand=True,
        )

        department_field = styled_field(
            label="Department / Subject",
            hint_text="Computer Science",
            prefix_icon=ft.Icons.SCHOOL_OUTLINED,
            expand=True,
        )

        institution_field = styled_field(
            label="Institution",
            hint_text="e.g. Camarines Sur Polytechnic Colleges",
            prefix_icon=ft.Icons.APARTMENT_OUTLINED,
        )

        # Inline banner for top-level errors (e.g. failed insert), separate
        # from field-level error_text so both can be shown at once.
        form_error_banner = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.ERROR_OUTLINE, size=16, color=ERROR),
                    ft.Container(width=8),
                    ft.Text("", size=12, color=ERROR, expand=True),
                ],
            ),
            bgcolor="#fef2f2",
            border=ft.border.all(1, "#fecaca"),
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=12, vertical=10),
            visible=False,
        )

        def show_form_error(message: str):
            form_error_banner.content.controls[2].value = message
            form_error_banner.visible = True
            dialog.update()

        def clear_field_errors(*_):
            name_field.error_text = None
            email_field.error_text = None
            password_field.error_text = None
            form_error_banner.visible = False
            dialog.update()

        name_field.on_change = clear_field_errors
        email_field.on_change = clear_field_errors
        password_field.on_change = clear_field_errors

        submit_btn_text = ft.Text("Add User", size=13, weight=ft.FontWeight.W_600, color=TEXT_WHITE)
        submit_spinner = ft.ProgressRing(width=14, height=14, stroke_width=2, color=TEXT_WHITE, visible=False)

        def set_loading(is_loading: bool):
            submit_spinner.visible = is_loading
            submit_btn_text.value = "Adding..." if is_loading else "Add User"
            add_btn.disabled = is_loading
            cancel_btn.disabled = is_loading
            dialog.update()

        def on_submit(e):
            name = (name_field.value or "").strip()
            email = (email_field.value or "").strip()
            password = (password_field.value or "").strip()
            role = role_dropdown.value
            department = (department_field.value or "").strip()
            institution = (institution_field.value or "").strip()

            # Client-side validation, mirrored per-field
            has_error = False
            if not name:
                name_field.error_text = "Full name is required"
                has_error = True
            if not email:
                email_field.error_text = "Email is required"
                has_error = True
            elif "@" not in email or "." not in email.split("@")[-1]:
                email_field.error_text = "Enter a valid email address"
                has_error = True
            if password and len(password) < 8:
                password_field.error_text = "Password must be at least 8 characters"
                has_error = True
            elif password and not any(c.isupper() for c in password):
                password_field.error_text = "Password must contain at least 1 uppercase letter"
                has_error = True
            elif password and not any(c.isdigit() for c in password):
                password_field.error_text = "Password must contain at least 1 number"
                has_error = True
            elif password and not any(c in '!@#$%^&*(),.?":{}|<>' for c in password):
                password_field.error_text = "Password must contain at least 1 special character"
                has_error = True

            if has_error:
                dialog.update()
                return

            set_loading(True)
            try:
                result = add_user(email, role, name, department, institution, password)
            except Exception as ex:
                set_loading(False)
                show_form_error(f"Something went wrong: {ex}")
                return

            set_loading(False)

            if result.get('success'):
                page.close(dialog)
                page.snack_bar = ft.SnackBar(
                    ft.Text(result.get('message', 'User added successfully'), color=TEXT_WHITE),
                    bgcolor=SUCCESS,
                )
                page.snack_bar.open = True
                page.update()
                page.clean()
                main(page, nav)
            else:
                show_form_error(result.get('message', 'Failed to add user. Please try again.'))

        def on_cancel(e):
            page.close(dialog)

        cancel_btn = ft.OutlinedButton(
            "Cancel",
            on_click=on_cancel,
            style=ft.ButtonStyle(
                color=TEXT_SECONDARY,
                side=ft.BorderSide(1, BORDER_COLOR),
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
        )

        add_btn = ft.ElevatedButton(
            content=ft.Row(
                [submit_spinner, submit_btn_text],
                spacing=8,
                alignment=ft.MainAxisAlignment.CENTER,
                tight=True,
            ),
            on_click=on_submit,
            style=ft.ButtonStyle(
                bgcolor=PRIMARY_BLUE,
                color=TEXT_WHITE,
                shape=ft.RoundedRectangleBorder(radius=8),
                elevation=0,
                padding=ft.padding.symmetric(horizontal=20, vertical=14),
            ),
        )

        dialog_header = ft.Row(
            [
                ft.Container(
                    content=ft.Icon(ft.Icons.PERSON_ADD_ALT_1, size=18, color=PRIMARY_BLUE),
                    width=36,
                    height=36,
                    bgcolor="#eff6ff",
                    border_radius=8,
                    alignment=ft.alignment.center,
                ),
                ft.Container(width=12),
                ft.Column(
                    [
                        ft.Text("Add New User", size=17, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ft.Text("Create an account for an evaluator or administrator", size=12, color=TEXT_SECONDARY),
                    ],
                    spacing=2,
                ),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.CLOSE,
                    icon_size=18,
                    icon_color=TEXT_TERTIARY,
                    on_click=on_cancel,
                ),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        section_label_style = dict(size=11, weight=ft.FontWeight.BOLD, color=TEXT_TERTIARY)

        dialog_body = ft.Column(
            [
                dialog_header,
                ft.Container(height=20),
                form_error_banner,
                ft.Container(height=8),

                ft.Text("ACCOUNT DETAILS", **section_label_style),
                ft.Container(height=10),
                name_field,
                ft.Container(height=12),
                email_field,
                ft.Container(height=12),
                password_field,
                ft.Container(height=8),
                password_strength_text,
                ft.Container(height=8),
                password_requirements,

                ft.Container(height=20),
                ft.Divider(height=1, color=BORDER_COLOR),
                ft.Container(height=20),

                ft.Text("ROLE & AFFILIATION", **section_label_style),
                ft.Container(height=10),
                ft.Row(
                    [role_dropdown, ft.Container(width=12), department_field],
                ),
                ft.Container(height=12),
                institution_field,

                ft.Container(height=24),
                ft.Row(
                    [ft.Container(expand=True), cancel_btn, ft.Container(width=10), add_btn],
                ),
            ],
            tight=True,
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
        )

        dialog = ft.AlertDialog(
            modal=True,
            content=ft.Container(
                content=dialog_body,
                width=460,
                padding=ft.padding.all(4),
            ),
            shape=ft.RoundedRectangleBorder(radius=16),
            bgcolor=CARD_BG_COLOR,
            content_padding=ft.padding.all(24),
        )

        page.open(dialog)

    add_user_btn = ft.ElevatedButton(
        content=ft.Row(
            [ft.Icon(ft.Icons.ADD, size=18, color=TEXT_WHITE), ft.Text("Add User", size=13, weight=ft.FontWeight.W_600, color=TEXT_WHITE)],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=4,
        ),
        width=120,
        height=40,
        style=ft.ButtonStyle(
            bgcolor=PRIMARY_BLUE,
            shape=ft.RoundedRectangleBorder(radius=8),
            elevation=0,
        ),
        on_click=on_add_user,
    )

    # --- Users Section Header ---
    users_header = ft.Row(
        [
            ft.Text(f"{len(users_data)} accounts", size=13, color=TEXT_SECONDARY),
            ft.Container(expand=True),
            add_user_btn,
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    # --- Users Section ---
    users_section = ft.Container(
        content=ft.Column(
            [
                users_header,
                ft.Container(height=20),
                ft.Container(
                    content=users_table,
                    padding=ft.padding.all(0),
                ),
            ],
            spacing=0,
        ),
        padding=ft.padding.all(24),
        bgcolor=CARD_BG_COLOR,
        border_radius=12,
        border=ft.border.all(1, BORDER_COLOR),
    )

    # --- Main Content ---
    if admin_header:
        main_content = ft.Container(
            content=ft.Column(
                [
                    admin_header,
                    ft.Container(height=8),
                    ft.Container(
                        content=users_section,
                        padding=ft.padding.symmetric(horizontal=32),
                    ),
                    ft.Container(height=40),
                ],
                spacing=0,
            ),
        )
    else:
        main_content = ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=users_section,
                        padding=ft.padding.symmetric(horizontal=32),
                    ),
                    ft.Container(height=40),
                ],
                spacing=0,
            ),
        )

    # --- Page Layout ---
    page.add(main_content)
    if nav:
        nav.main_content = main_content


if __name__ == "__main__":
    ft.app(target=main)