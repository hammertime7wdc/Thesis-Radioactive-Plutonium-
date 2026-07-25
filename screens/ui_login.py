import sys

import os

import json

import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))



import math

import time

import threading

import flet as ft

from services.supabase_client import get_supabase_client, get_supabase_service_client

from datetime import datetime, timedelta



try:

    from screens.password_reset import main as reset_password_main

except ModuleNotFoundError:

    def reset_password_main(page, nav=None):

        page.clean()

        page.add(ft.Text("Reset password screen is unavailable."))





def validate_password(password: str) -> tuple[bool, str]:

    """

    Validate password against security requirements.

    

    Requirements:

    - Minimum 8 characters

    - At least 1 lowercase letter

    - At least 1 uppercase letter

    - At least 1 number

    - At least 1 special character

    

    Args:

        password: Password to validate

        

    Returns:

        Tuple of (is_valid, error_message)

    """

    if len(password) < 8:

        return False, "Password must be at least 8 characters long"

    

    if not re.search(r'[a-z]', password):

        return False, "Password must contain at least 1 lowercase letter"

    

    if not re.search(r'[A-Z]', password):

        return False, "Password must contain at least 1 uppercase letter"

    

    if not re.search(r'\d', password):

        return False, "Password must contain at least 1 number"

    

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):

        return False, "Password must contain at least 1 special character"

    

    return True, ""





def main(page: ft.Page, nav=None):

    page.title = "QualCheck Login"

    page.window_width = 900

    page.window_height = 780

    page.window_min_width = 900

    page.window_min_height = 780

    page.window_resizable = True

    page.padding = 0

    page.bgcolor = "#0f1e30"

    page.theme_mode = ft.ThemeMode.DARK

    page.appbar = None  # Explicitly clear any existing app bar

    page.clean()



    blob1 = ft.Container(width=600, height=600, gradient=ft.RadialGradient(colors=[ft.Colors.with_opacity(0.12, ft.Colors.BLUE_400), ft.Colors.with_opacity(0.0, ft.Colors.BLUE_400)], stops=[0.0, 1.0]), left=-100, top=-100)

    blob2 = ft.Container(width=800, height=800, gradient=ft.RadialGradient(colors=[ft.Colors.with_opacity(0.08, ft.Colors.CYAN_400), ft.Colors.with_opacity(0.0, ft.Colors.CYAN_400)], stops=[0.0, 1.0]), right=-200, bottom=-200)

    blob3 = ft.Container(width=500, height=500, gradient=ft.RadialGradient(colors=[ft.Colors.with_opacity(0.10, ft.Colors.PURPLE_400), ft.Colors.with_opacity(0.0, ft.Colors.PURPLE_400)], stops=[0.0, 1.0]), left=100, bottom=-100)



    def animate_blobs():

        t = 0.0

        # Stop background animation thread once page title changes to clean up memory and prevent rogue update calls

        while page.title == "QualCheck Login":

            try:

                blob1.top = -100 + 80 * math.sin(t); blob1.left = -100 + 120 * math.cos(t * 0.8)

                blob2.bottom = -200 + 100 * math.cos(t * 0.9); blob2.right = -200 + 150 * math.sin(t * 0.7)

                blob3.bottom = -100 + 120 * math.sin(t * 1.1); blob3.left = 100 + 80 * math.cos(t * 0.6)

                page.update(); time.sleep(0.05); t += 0.05

            except Exception:

                break



    threading.Thread(target=animate_blobs, daemon=True).start()







    def brand_header():

        logo = ft.Container(content=ft.Text("Q", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), bgcolor=ft.Colors.BLUE_500, width=38, height=38, border_radius=8, alignment=ft.alignment.center, shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLUE_500, offset=ft.Offset(0, 0), spread_radius=2))

        brand = ft.Column([ft.Text("QualCheck", size=17, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), ft.Text("Semantic Evaluation System", size=11, color="#8b9bb4")], spacing=0)

        return ft.Row([logo, brand], spacing=12, alignment=ft.MainAxisAlignment.START)



    GOOGLE_LOGO_B64 = (

        "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA0OCA0OCI+"

        "PHBhdGggZmlsbD0iI0VBNDMzNSIgZD0iTTI0IDkuNWMzLjU0IDAgNi43MSAxLjIyIDkuMjEgMy42bDYu"

        "ODUtNi44NUMzNS45IDIuMzggMzAuNDcgMCAyNCAwIDE0LjYyIDAgNi41MSA1LjM4IDIuNTYgMTMuMjJs"

        "Ny45OCA2LjE5QzEyLjQzIDEzLjcyIDE3Ljc0IDkuNSAyNCA5LjV6Ii8+PHBhdGggZmlsbD0iIzQyODVG"

        "NCIgZD0iTTQ2Ljk4IDI0LjU1YzAtMS41Ny0uMTUtMy4wOS0uMzgtNC41NUgyNHY5LjAyaDEyLjk0Yy0u"

        "NTggMi45Ni0yLjI2IDUuNDgtNC43OCA3LjE4bDcuNzMgNmM0LjUxLTQuMTggNy4wOS0xMC4zNiA3LjA5"

        "LTE3LjY1eiIvPjxwYXRoIGZpbGw9IiNGQkJDMDUiIGQ9Ik0xMC41MyAyOC41OWMtLjQ4LTEuNDUtLjc2"

        "LTIuOTktLjc2LTQuNTlzLjI3LTMuMTQuNzYtNC41OWwtNy45OC02LjE5Qy45MiAxNi40NiAwIDIwLjEy"

        "IDAgMjRjMCAzLjg4LjkyIDcuNTQgMi41NiAxMC43OGw3Ljk3LTYuMTl6Ii8+PHBhdGggZmlsbD0iIzM0"

        "QTg1MyIgZD0iTTI0IDQ4YzYuNDggMCAxMS45My0yLjEzIDE1Ljg5LTUuODFsLTcuNzMtNmMtMi4xNSAx"

        "LjQ1LTQuOTIgMi4zLTguMTYgMi4zLTYuMjYgMC0xMS41Ny00LjIyLTEzLjQ3LTkuOTFsLTcuOTggNi4x"

        "OUM2LjUxIDQyLjYyIDE0LjYyIDQ4IDI0IDQ4eiIvPjwvc3ZnPg=="

    )



    def google_button(label):

        return ft.Container(

            content=ft.Row([ft.Image(src_base64=GOOGLE_LOGO_B64, width=18, height=18), ft.Text(label, size=14, weight=ft.FontWeight.W_500, color="#1a1a1a")], alignment=ft.MainAxisAlignment.CENTER, spacing=10),

            bgcolor=ft.Colors.WHITE, border_radius=8, height=44, width=400, alignment=ft.alignment.center, border=ft.border.all(1, "#d1d5db"), ink=True, on_click=lambda e: None,

        )



    def or_divider():

        line = ft.Container(height=1, bgcolor="#2a3b54", expand=True)

        return ft.Row([line, ft.Text("or", size=12, color="#4a5b75"), line], spacing=12, width=400, vertical_alignment=ft.CrossAxisAlignment.CENTER)



    def text_field(hint="", password=False, reveal=False, read_only=False, value=""):

        return ft.TextField(

            hint_text=hint, password=password, can_reveal_password=reveal, read_only=read_only, value=value,

            width=400, height=44, bgcolor="#1e2f46", border_color="#2e4060",

            focused_border_color=ft.Colors.BLUE_400, text_size=14,

            content_padding=ft.padding.symmetric(horizontal=14, vertical=10),

            hint_style=ft.TextStyle(color="#4a5b75"), color=ft.Colors.WHITE, border_radius=8,

        )



    def action_button(label, icon, on_click):

        return ft.Container(

            content=ft.Row([ft.Icon(icon, size=16, color=ft.Colors.WHITE), ft.Text(label, size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)], alignment=ft.MainAxisAlignment.CENTER, spacing=8),

            width=400, height=46, bgcolor=ft.Colors.BLUE_600, border_radius=8, alignment=ft.alignment.center, ink=True, on_click=on_click,

        )



    # --- Error banners ---

    error_text = ft.Text("", size=12, color=ft.Colors.RED_400, visible=False)

    ca_error   = ft.Text("", size=12, color=ft.Colors.RED_400, visible=False)



    # =========================================================

    #  SIGN IN FORM

    # =========================================================

    si_email    = text_field(hint="you@university.edu")

    si_password = text_field(password=True, reveal=True)



    sign_in_btn_content = ft.Row([ft.Icon(ft.Icons.LOGIN_ROUNDED, size=16, color=ft.Colors.WHITE), ft.Text("Sign in", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)], alignment=ft.MainAxisAlignment.CENTER, spacing=8)



    sign_in_btn = ft.Container(

        content=sign_in_btn_content,

        width=400, height=46, bgcolor=ft.Colors.BLUE_600, border_radius=8, alignment=ft.alignment.center, ink=True,

    )



    def on_login(e):

        if sign_in_btn.disabled:

            return



        if not si_email.value or not si_password.value:

            error_text.value = "Please enter email and password."

            error_text.visible = True; page.update(); return



        error_text.visible = False

        sign_in_btn.disabled = True

        sign_in_btn.content = ft.Row([

            ft.ProgressRing(width=16, height=16, stroke_width=2, color=ft.Colors.WHITE),

            ft.Text("Signing in...", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)

        ], alignment=ft.MainAxisAlignment.CENTER, spacing=8)

        page.update()



        def login_thread():

            try:

                import asyncio

                try:

                    asyncio.get_event_loop()

                except RuntimeError:

                    asyncio.set_event_loop(asyncio.new_event_loop())



                supabase = get_supabase_client()

                auth_response = supabase.auth.sign_in_with_password({

                    "email": si_email.value.strip(),

                    "password": si_password.value

                })

                

                supabase.auth.set_session(

                    access_token=auth_response.session.access_token,

                    refresh_token=auth_response.session.refresh_token

                )

                # Check is_active BEFORE persisting the session to disk

                profile_response = supabase.table("profiles").select("role, is_active").eq("id", auth_response.user.id).single().execute()

                role = profile_response.data.get("role", "evaluator") if profile_response.data else "evaluator"

                is_active = profile_response.data.get("is_active", True) if profile_response.data else True

                if not is_active:

                    try:

                        supabase.auth.sign_out()

                    except Exception:

                        pass

                    error_text.value = "Your account has been disabled. Please contact an administrator."

                    error_text.visible = True

                    sign_in_btn.disabled = False

                    sign_in_btn.content = sign_in_btn_content

                    page.update()

                    return

                # Only now persist the session - user is confirmed active

                session_data = {

                    "access_token": auth_response.session.access_token,

                    "refresh_token": auth_response.session.refresh_token,

                    "user_id": auth_response.user.id

                }

                session_file = os.path.join(os.path.dirname(__file__), "..", ".session.json")

                with open(session_file, "w") as f:

                    json.dump(session_data, f)

                if nav:

                    if role == "admin":

                        nav.navigate_to_admin()

                    elif role == "evaluator":

                        nav.navigate_to_short_answer()

                    else:

                        error_text.value = "Invalid user role."

                        error_text.visible = True

                        sign_in_btn.disabled = False

                        sign_in_btn.content = sign_in_btn_content

                        page.update()

            except Exception as ex:

                error_text.value = f"Login failed: {str(ex)}"

                error_text.visible = True

                sign_in_btn.disabled = False

                sign_in_btn.content = sign_in_btn_content

                page.update()



        threading.Thread(target=login_thread, daemon=True).start()



    sign_in_btn.on_click = on_login



    def on_forgot_password(e):

        reset_password_main(page, nav)



    sign_in_form = ft.Column([

        brand_header(),

        ft.Container(height=8),

        ft.Text("Welcome back", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),

        ft.Text("Sign in to continue evaluating responses", size=13, color="#8b9bb4"),

        ft.Container(height=12),

        google_button("Continue with Google"),

        ft.Container(height=10),

        or_divider(),

        ft.Container(height=10),

        ft.Text("Email", size=13, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE),

        ft.Container(height=4),

        si_email,

        ft.Container(height=8),

        ft.Row([

            ft.Text("Password", size=13, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE),

            ft.TextButton("Forgot password?", style=ft.ButtonStyle(color=ft.Colors.BLUE_400, padding=ft.padding.all(0)), on_click=on_forgot_password),

        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, width=400),

        ft.Container(height=4),

        si_password,

        error_text,

        ft.Container(height=14),

        sign_in_btn,

        ft.Container(height=16),

        ft.Row([

            ft.Text("Don't have an account?", size=13, color="#4a5b75"),

            ft.TextButton("Create one", style=ft.ButtonStyle(color=ft.Colors.BLUE_400, padding=ft.padding.all(0)), on_click=lambda e: switch_tab(1)),

        ], alignment=ft.MainAxisAlignment.CENTER, spacing=4),

    ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.START)



    # =========================================================

    #  CREATE ACCOUNT FORM

    # =========================================================

    ca_fullname = text_field(hint="Prof. Maria Santos")

    ca_email    = text_field(hint="you@university.edu")

    ca_password = text_field(hint="Min. 8 chars: 1 uppercase, 1 number, 1 special", password=True, reveal=True)

    ca_confirm  = text_field(password=True, reveal=True)

    

    # 6-digit access code field (hidden initially)

    ca_code_field = text_field(hint="Enter the 6-digit code sent to your email", read_only=False, value="")

    

    class SignupState:

        step = 1

        access_code = None

    

    signup_state = SignupState()



    def on_create_account(e):

        if signup_state.step == 1:

            if not ca_fullname.value or not ca_email.value or not ca_password.value or not ca_confirm.value:

                ca_error.value = "Please fill in all fields."; ca_error.visible = True; ca_error.color = ft.Colors.RED_400; page.update(); return

            if ca_password.value != ca_confirm.value:

                ca_error.value = "Passwords do not match."; ca_error.visible = True; ca_error.color = ft.Colors.RED_400; page.update(); return

            

            is_valid, password_error = validate_password(ca_password.value)

            if not is_valid:

                ca_error.value = password_error; ca_error.visible = True; ca_error.color = ft.Colors.RED_400; page.update(); return

            

            # Generate 6-digit access code on submission

            import random

            signup_state.access_code = str(random.randint(100000, 999999))

            

            # Send welcome email with access code first

            try:

                from services.email_service import get_email_service

                email_service = get_email_service()

                login_url = "http://localhost:8000"

                

                email_service.send_welcome_email(

                    to_email=ca_email.value,

                    user_name=ca_fullname.value,

                    temporary_password=ca_password.value,

                    login_url=login_url,

                    access_code=signup_state.access_code

                )

                

                # Switch to step 2

                signup_state.step = 2

                ca_step1.visible = False

                ca_step2.visible = True

                ca_action_button_container.content = action_button("Verify & Complete", ft.Icons.CHECK_CIRCLE_OUTLINE, on_create_account)

                ca_error.value = "Verification code sent to your email."

                ca_error.color = ft.Colors.GREEN_400

                ca_error.visible = True

                page.update()

            except Exception as email_error:

                ca_error.value = f"Failed to send email: {email_error}"

                ca_error.color = ft.Colors.RED_400

                ca_error.visible = True

                page.update()

        else:

            # Step 2: Verify the code

            if not ca_code_field.value:

                ca_error.value = "Please enter the verification code."; ca_error.visible = True; ca_error.color = ft.Colors.RED_400; page.update(); return

            

            if ca_code_field.value != signup_state.access_code:

                ca_error.value = "Invalid verification code."; ca_error.visible = True; ca_error.color = ft.Colors.RED_400; page.update(); return

                

            ca_code_expires_at = datetime.now() + timedelta(minutes=30)

            

            try:

                supabase = get_supabase_client()

                supabase_admin = get_supabase_service_client()

                auth_response = supabase_admin.auth.admin.create_user({

                    "email": ca_email.value,

                    "password": ca_password.value,

                    "email_confirm": True,

                })

                user_id = auth_response.user.id

                

                profile_payload = {

                    "email": ca_email.value,

                    "name": ca_fullname.value,

                    "access_code": signup_state.access_code,

                    "access_code_expires_at": ca_code_expires_at.isoformat()

                }



                existing_profile = supabase_admin.table("profiles").select("id").eq("id", user_id).execute()

                if existing_profile.data:

                    supabase_admin.table("profiles").update(profile_payload).eq("id", user_id).execute()

                else:

                    profile_payload["id"] = user_id

                    supabase_admin.table("profiles").insert(profile_payload).execute()

                

                ca_error.visible = False

                # Switch to sign in tab after successful registration

                switch_tab(0)

                si_email.value = ca_email.value

                si_password.value = ""

                

                # Reset state

                signup_state.step = 1

                signup_state.access_code = None

                ca_step1.disabled = False

                ca_step2.visible = False

                ca_fullname.value = ""

                ca_email.value = ""

                ca_password.value = ""

                ca_confirm.value = ""

                ca_code_field.value = ""

                ca_action_button_container.content = action_button("Create Account", ft.Icons.PERSON_ADD_ROUNDED, on_create_account)

                

                page.update()

            except Exception as ex:

                error_msg = str(ex).lower()

                if "rate limit" in error_msg or "too many requests" in error_msg:

                    ca_error.value = "Too many registration attempts. Please wait a few minutes and try again."

                else:

                    ca_error.value = f"Registration failed: {str(ex)}"

                ca_error.color = ft.Colors.RED_400

                ca_error.visible = True; page.update()





    ca_step1 = ft.Column([

        ft.Text("Full Name", size=13, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE),

        ft.Container(height=4),

        ca_fullname,

        ft.Container(height=8),

        ft.Text("Email", size=13, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE),

        ft.Container(height=4),

        ca_email,

        ft.Container(height=8),

        ft.Text("Password", size=13, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE),

        ft.Container(height=4),

        ca_password,

        ft.Container(height=8),

        ft.Text("Confirm Password", size=13, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE),

        ft.Container(height=4),

        ca_confirm,

        ft.Container(height=8),

    ], spacing=0, visible=True)



    ca_step2 = ft.Column([

        ft.Text("6-Digit Verification Code", size=13, weight=ft.FontWeight.W_500, color=ft.Colors.WHITE),

        ft.Container(height=4),

        ca_code_field,

        ft.Container(height=8),

    ], spacing=0, visible=False)



    ca_action_button_container = ft.Container(content=action_button("Create Account", ft.Icons.PERSON_ADD_ROUNDED, on_create_account))



    create_account_form = ft.Column([

        brand_header(),

        ft.Container(height=8),

        ft.Text("Create your account", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),

        ft.Text("Join QualCheck as an evaluator", size=13, color="#8b9bb4"),

        ft.Container(height=12),

        google_button("Sign up with Google"),

        ft.Container(height=10),

        or_divider(),

        ft.Container(height=10),

        ca_step1,

        ca_step2,

        ca_error,

        ft.Container(height=14),

        ca_action_button_container,

        ft.Container(height=16),

        ft.Row([

            ft.Text("Already have an account?", size=13, color="#4a5b75"),

            ft.TextButton("Sign in", style=ft.ButtonStyle(color=ft.Colors.BLUE_400, padding=ft.padding.all(0)), on_click=lambda e: switch_tab(0)),

        ], alignment=ft.MainAxisAlignment.CENTER, spacing=4),

    ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.START)



    # =========================================================

    #  TAB SWITCHER

    # =========================================================

    tab_signin  = ft.Container(content=ft.Text("Sign In", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER), padding=ft.padding.symmetric(horizontal=24, vertical=14), bgcolor="#1c2c44", expand=True, alignment=ft.alignment.center, border_radius=ft.border_radius.only(top_left=16), on_click=lambda e: switch_tab(0), ink=True)

    tab_create  = ft.Container(content=ft.Text("Create Account", size=14, weight=ft.FontWeight.W_500, color="#6b7f99", text_align=ft.TextAlign.CENTER), padding=ft.padding.symmetric(horizontal=24, vertical=14), bgcolor="#161f2e", expand=True, alignment=ft.alignment.center, border_radius=ft.border_radius.only(top_right=16), on_click=lambda e: switch_tab(1), ink=True)

    ind_signin  = ft.Container(height=2, bgcolor=ft.Colors.BLUE_500, expand=True)

    ind_create  = ft.Container(height=2, bgcolor="transparent", expand=True)



    tab_row = ft.Row([ft.Column([tab_signin, ind_signin], spacing=0, expand=True), ft.Column([tab_create, ind_create], spacing=0, expand=True)], spacing=0, expand=True)



    form_container = ft.Container(content=sign_in_form, padding=ft.padding.symmetric(horizontal=40, vertical=30))



    card = ft.Container(

        content=ft.Column([

            tab_row,

            ft.Container(height=1, bgcolor="#1e2f46"),

            form_container,

        ], spacing=0),

        bgcolor="#1c2c44", border_radius=16, width=480,

        border=ft.border.all(1, "#243447"),

        shadow=ft.BoxShadow(blur_radius=40, color="#070f1a", offset=ft.Offset(0, 12), spread_radius=0),

    )



    def switch_tab(index):

        if index == 0:

            tab_signin.bgcolor = "#1c2c44"; tab_signin.content.color = ft.Colors.WHITE; tab_signin.content.weight = ft.FontWeight.BOLD

            tab_create.bgcolor = "#161f2e"; tab_create.content.color = "#6b7f99"; tab_create.content.weight = ft.FontWeight.W_500

            ind_signin.bgcolor = ft.Colors.BLUE_500; ind_create.bgcolor = "transparent"

            form_container.content = sign_in_form; error_text.visible = False

        else:

            tab_create.bgcolor = "#1c2c44"; tab_create.content.color = ft.Colors.WHITE; tab_create.content.weight = ft.FontWeight.BOLD

            tab_signin.bgcolor = "#161f2e"; tab_signin.content.color = "#6b7f99"; tab_signin.content.weight = ft.FontWeight.W_500

            ind_create.bgcolor = ft.Colors.BLUE_500; ind_signin.bgcolor = "transparent"

            form_container.content = create_account_form; ca_error.visible = False

        page.update()



    bottom_links = ft.Row([

        ft.Column([ft.Text("BERT",   color=ft.Colors.BLUE_400, size=12, weight=ft.FontWeight.BOLD), ft.Text("Embeddings", color="#4a5b75", size=11)], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),

        ft.Container(width=24),

        ft.Column([ft.Text("Cosine", color=ft.Colors.BLUE_400, size=12, weight=ft.FontWeight.BOLD), ft.Text("Similarity", color="#4a5b75", size=11)], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),

        ft.Container(width=24),

        ft.Column([ft.Text("Rubric", color=ft.Colors.BLUE_400, size=12, weight=ft.FontWeight.BOLD), ft.Text("Guided",     color="#4a5b75", size=11)], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),

    ], alignment=ft.MainAxisAlignment.CENTER)



    page.add(ft.Stack([

        blob1, blob2, blob3,

        ft.Column(

            [

                ft.Container(height=60),

                card,

                ft.Container(height=28),

                bottom_links,

                ft.Container(height=40),

            ],

            horizontal_alignment=ft.CrossAxisAlignment.CENTER,

            scroll=ft.ScrollMode.AUTO,

            expand=True,

        ),

    ], expand=True))





if __name__ == "__main__":

    ft.app(target=main)