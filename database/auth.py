"""
Supabase Authentication Helper Functions
This file contains functions for user authentication using Supabase.
"""

from database.models import supabase, supabase_admin, User
from typing import Optional, Dict, Any
import bcrypt
import re


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password against security requirements.
    
    Requirements:
    - Minimum 8 characters
    - At least 1 special character
    - At least 1 number
    - At least 1 uppercase letter
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
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
        users_table = supabase.table('users')
        result = users_table.select("*").eq('email', email).execute()
        
        if result.data:
            return User.from_dict(result.data[0])
        return None
        
    except Exception as e:
        print(f"Error fetching user: {e}")
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


def send_password_reset_email(email: str) -> tuple[bool, str]:
    """
    Request a password reset email for the given address.

    Args:
        email: User's email address

    Returns:
        Tuple of (success, message)
    """
    try:
        supabase.auth.reset_password_for_email(email)
        return True, "If an account exists for that email, a reset message has been sent."
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
