"""
Account registration business logic, extracted out of ui_login.py:
generating and emailing the signup verification code, and creating the
Supabase auth user + profiles row once that code is confirmed.
"""

import random
from datetime import datetime, timedelta

from services.supabase_client import get_supabase_service_client
from services.email_service import get_email_service


def generate_access_code() -> str:
    return str(random.randint(100000, 999999))


def send_signup_verification(
    email: str,
    full_name: str,
    temp_password: str,
    access_code: str,
    login_url: str = "http://localhost:8000",
):
    """
    Emails the verification code to a prospective new user.
    Raises Exception with a user-facing message on failure.
    """
    email_service = get_email_service()
    email_service.send_welcome_email(
        to_email=email,
        user_name=full_name,
        temporary_password=temp_password,
        login_url=login_url,
        access_code=access_code,
    )


def complete_registration(
    email: str,
    password: str,
    full_name: str,
    access_code: str,
    code_expiry_minutes: int = 30,
) -> str:
    """
    Creates the Supabase auth user (via the service role client) and
    upserts their profiles row. Returns the new user's id.
    Raises Exception with a user-facing message on failure.
    """
    supabase_admin = get_supabase_service_client()
    expires_at = datetime.now() + timedelta(minutes=code_expiry_minutes)

    auth_response = supabase_admin.auth.admin.create_user(
        {"email": email, "password": password, "email_confirm": True}
    )
    user_id = auth_response.user.id

    profile_payload = {
        "email": email,
        "name": full_name,
        "access_code": access_code,
        "access_code_expires_at": expires_at.isoformat(),
    }

    existing_profile = supabase_admin.table("profiles").select("id").eq("id", user_id).execute()
    if existing_profile.data:
        supabase_admin.table("profiles").update(profile_payload).eq("id", user_id).execute()
    else:
        profile_payload["id"] = user_id
        supabase_admin.table("profiles").insert(profile_payload).execute()

    return user_id
