"""
Supabase Authentication Helper Functions
This file contains functions for user authentication using Supabase.
"""

from database.models import supabase, supabase_admin, User
from typing import Optional, Dict, Any
import bcrypt
import re
import secrets
import hashlib
from datetime import datetime, timedelta, timezone


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


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password as a string
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against a bcrypt hash.
    
    Args:
        password: Plain text password to verify
        hashed_password: Stored bcrypt hash
        
    Returns:
        True if password matches, False otherwise
    """
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


def authenticate_user(email: str, password: str) -> Optional[User]:
    """
    Authenticate user with email and password using Supabase Auth and bcrypt verification.
    
    Args:
        email: User's email address
        password: User's password
        
    Returns:
        User object if authentication successful, None otherwise
    """
    try:
        # Get user from users table first to check password hash
        users_table = supabase_admin.table('users')
        user_record = users_table.select("*").eq('email', email).execute()
        
        if not user_record.data:
            return None
        
        user_dict = user_record.data[0]
        
        # Verify password using bcrypt if password_hash exists
        if 'password_hash' in user_dict and user_dict['password_hash']:
            if not verify_password(password, user_dict['password_hash']):
                return None

        # Block disabled/banned accounts
        if user_dict.get('is_active') is False:
            return None

        # Sign in with Supabase Auth for session management
        auth_response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        # Return user object from database
        return User.from_dict(user_dict)
        
    except Exception as e:
        print(f"Authentication error: {e}")
        return None


def get_user_by_email(email: str) -> Optional[User]:
    """
    Get user by email from Supabase.
    
    Args:
        email: User's email address
        
    Returns:
        User object if found, None otherwise
    """
    try:
        users_table = supabase_admin.table('profiles')
        result = users_table.select("*").eq('email', email).execute()
        
        if result.data:
            return User.from_dict(result.data[0])
        return None
        
    except Exception as e:
        print(f"Error fetching user: {e}")
        return None


def get_auth_user_id_by_email(email: str) -> Optional[str]:
    """
    Resolve a Supabase Auth user id by email.

    Falls back to scanning admin users when the profile row is missing.
    """
    try:
        auth_admin = supabase_admin.auth.admin

        if hasattr(auth_admin, "get_user_by_email"):
            auth_user = auth_admin.get_user_by_email(email)
            if auth_user and getattr(auth_user, "user", None):
                return auth_user.user.id

        if hasattr(auth_admin, "list_users"):
            users_response = auth_admin.list_users()
            users = getattr(users_response, "users", None)
            if users is None:
                users = getattr(users_response, "data", None)
            if users:
                for auth_user in users:
                    if getattr(auth_user, "email", None) == email:
                        return auth_user.id
    except Exception as e:
        print(f"Error resolving auth user id: {e}")

    return None


def create_user(email: str, password: str, role: str = "evaluator") -> tuple[Optional[User], str]:
    """
    Create a new user in Supabase using admin client for privileged operations.
    Password is validated and hashed with bcrypt before storage (if password_hash column exists).
    
    Args:
        email: User's email address
        password: User's password
        role: User's role ('admin' or 'evaluator')
        
    Returns:
        Tuple of (User object if creation successful, None otherwise, error_message)
    """
    # Validate password
    is_valid, error_msg = validate_password(password)
    if not is_valid:
        return None, error_msg
    
    try:
        # Hash password with bcrypt
        hashed_password = hash_password(password)
        
        # Create user in Supabase Auth using admin client
        auth_response = supabase_admin.auth.sign_up({
            "email": email,
            "password": password
        })
        
        # Create user record in users table using admin client
        users_table = supabase_admin.table('users')
        
        # Use upsert to handle the case where the trigger already created a record
        try:
            user_record = users_table.upsert({
                "email": email,
                "password_hash": hashed_password,
                "role": role
            }, on_conflict="email").execute()
        except Exception as insert_error:
            # If password_hash column doesn't exist, upsert without it
            if "password_hash" in str(insert_error):
                user_record = users_table.upsert({
                    "email": email,
                    "role": role
                }, on_conflict="email").execute()
            else:
                raise insert_error
        
        if user_record.data:
            return User.from_dict(user_record.data[0]), ""
        
        return None, "Failed to create user record"
        
    except Exception as e:
        error_str = str(e)
        print(f"Error creating user: {e}")
        # If it's a "User already registered" error from Supabase Auth, return a clear message
        if "already registered" in error_str.lower():
            return None, "Email already registered"
        # If it's a duplicate key error from the database
        if "duplicate key" in error_str.lower() or "unique constraint" in error_str.lower():
            return None, "Email already registered"
        return None, error_str


def logout_user():
    """
    Logout current user from Supabase Auth.
    """
    try:
        supabase.auth.sign_out()
        return True
    except Exception as e:
        print(f"Logout error: {e}")
        return False


def generate_reset_token() -> str:
    """
    Generate a 6-digit password reset token.
    
    Returns:
        6-digit token
    """
    import random
    return str(random.randint(100000, 999999))


def store_reset_token(email: str, token: str, expires_minutes: int = 5) -> bool:
    """
    Store password reset token in database.
    
    Args:
        email: User's email address
        token: Reset token
        expires_minutes: Token expiration time in minutes
    
    Returns:
        True if token stored successfully
    """
    try:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
        
        # Store token in password_resets table
        reset_table = supabase_admin.table('password_resets')
        reset_table.insert({
            "email": email,
            "token": token,
            "expires_at": expires_at.isoformat(),
            "used": False
        }).execute()
        
        return True
    except Exception as e:
        print(f"Error storing reset token: {e}")
        return False


def verify_reset_token(token: str) -> tuple[bool, str, Optional[str]]:
    """
    Verify password reset token and return associated email.
    
    Args:
        token: Reset token to verify
    
    Returns:
        Tuple of (is_valid, message, email)
    """
    try:
        reset_table = supabase_admin.table('password_resets')
        result = reset_table.select("*").eq('token', token).eq('used', False).execute()
        
        if not result.data:
            return False, "Invalid or expired reset token", None
        
        reset_record = result.data[0]
        
        # Check if token is expired
        expires_raw = reset_record['expires_at']
        expires_at = datetime.fromisoformat(expires_raw.replace('Z', '+00:00'))
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if datetime.now(timezone.utc) > expires_at:
            return False, "Reset token has expired", None
        
        return True, "", reset_record['email']
        
    except Exception as e:
        print(f"Error verifying reset token: {e}")
        return False, "Error verifying token", None


def mark_token_used(token: str) -> bool:
    """
    Mark reset token as used.
    
    Args:
        token: Reset token to mark as used
    
    Returns:
        True if token marked successfully
    """
    try:
        reset_table = supabase_admin.table('password_resets')
        reset_table.update({"used": True}).eq('token', token).execute()
        return True
    except Exception as e:
        print(f"Error marking token as used: {e}")
        return False


def send_password_reset_email(email: str) -> tuple[bool, str]:
    """
    Request a password reset email for the given address using custom SMTP.
    
    Args:
        email: User's email address
    
    Returns:
        Tuple of (success, message)
    """
    try:
        user = get_user_by_email(email)
        user_name = user.email.split('@')[0] if user else email.split('@')[0]
        
        # Generate reset token
        token = generate_reset_token()
        
        # Store token in database
        if not store_reset_token(email, token):
            return False, "Failed to generate reset token"
        
        # Create reset link (adjust URL as needed)
        reset_link = f"http://localhost:8000/reset-password?token={token}"
        
        # Send email using custom SMTP service
        from services.email_service import get_email_service
        email_service = get_email_service()
        
        if email_service.send_password_reset(email, reset_link, user_name=user_name, reset_code=token):
            return True, "If an account exists for that email, a reset message has been sent."
        else:
            return False, "Failed to send reset email"
            
    except Exception as e:
        error_message = str(e)
        print(f"Password reset error: {e}")
        return False, error_message


def resend_password_reset_email(email: str) -> tuple[bool, str]:
    """Send a fresh five-minute password reset code."""
    return send_password_reset_email(email)


def reset_password_with_token(token: str, new_password: str) -> tuple[bool, str]:
    """
    Reset user password using reset token.
    
    Args:
        token: Password reset token
        new_password: New password to set
    
    Returns:
        Tuple of (success, message)
    """
    try:
        # Verify token
        is_valid, message, email = verify_reset_token(token)
        if not is_valid:
            return False, message
        
        # Validate new password
        is_valid, error_msg = validate_password(new_password)
        if not is_valid:
            return False, error_msg
        
        # Hash new password (optional, kept for compatibility if needed)
        hashed_password = hash_password(new_password)
        
        # Update Supabase Auth password
        try:
            user = get_user_by_email(email)
            if user:
                supabase_admin.auth.admin.update_user_by_id(
                    user.id,
                    {"password": new_password}
                )
            else:
                auth_user_id = get_auth_user_id_by_email(email)
                if auth_user_id:
                    supabase_admin.auth.admin.update_user_by_id(
                        auth_user_id,
                        {"password": new_password}
                    )
                else:
                    return False, "User not found"
        except Exception as auth_error:
            print(f"Supabase auth update error: {auth_error}")
            return False, "Failed to update auth password"
        
        # Mark token as used
        mark_token_used(token)
        
        return True, "Password reset successfully"
        
    except Exception as e:
        error_message = str(e)
        print(f"Password reset error: {e}")
        return False, error_message


def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Get currently authenticated user from Supabase Auth.
    
    Returns:
        User data dictionary if authenticated, None otherwise
    """
    try:
        user = supabase.auth.get_user()
        return user.user if user else None
    except Exception as e:
        print(f"Error getting current user: {e}")
        return None


def validate_access_code(user_email: str, access_code: str) -> tuple[bool, str]:
    """
    Validate access code and check if it's expired.
    
    Args:
        user_email: User's email address
        access_code: Access code to validate
    
    Returns:
        Tuple of (is_valid, message)
    """
    try:
        # Get user profile
        users_table = supabase_admin.table('profiles')
        result = users_table.select("*").eq('email', user_email).execute()
        
        if not result.data:
            return False, "User not found"
        
        user_data = result.data[0]
        
        # Check if access code matches
        if user_data.get('access_code') != access_code:
            return False, "Invalid access code"
        
        # Check if access code is expired
        if 'access_code_expires_at' in user_data and user_data['access_code_expires_at']:
            expires_at = datetime.fromisoformat(user_data['access_code_expires_at'])
            if datetime.now() > expires_at:
                return False, "Access code has expired"
        
        return True, ""
        
    except Exception as e:
        print(f"Error validating access code: {e}")
        return False, "Error validating access code"