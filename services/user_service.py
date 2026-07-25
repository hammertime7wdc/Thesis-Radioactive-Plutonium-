from supabase import Client
from services.supabase_client import get_supabase_client, get_supabase_service_client
from services.audit_service import log_audit_entry
from services.session_manager import get_current_user
from services.email_service import get_email_service
import uuid
import secrets
import random
import string
from datetime import datetime, timedelta


def generate_secure_password(length: int = 12) -> str:
    """
    Generate a secure password following auth.py rules:
    - Minimum 8 characters
    - At least 1 special character
    - At least 1 number
    - At least 1 uppercase letter
    """
    if length < 8:
        length = 8
    
    # Ensure at least one of each required character type
    uppercase = random.choice(string.ascii_uppercase)
    lowercase = random.choice(string.ascii_lowercase)
    digit = random.choice(string.digits)
    special = random.choice('!@#$%^&*(),.?":{}|<>')
    
    # Fill the rest with random characters from all types
    all_chars = string.ascii_letters + string.digits + '!@#$%^&*(),.?":{}|<>'
    remaining = length - 4
    random_chars = ''.join(random.choice(all_chars) for _ in range(remaining))
    
    # Combine and shuffle
    password = uppercase + lowercase + digit + special + random_chars
    password = ''.join(random.sample(password, len(password)))
    
    return password


def add_user(email: str, role: str = 'evaluator', name: str = None, department: str = None, institution: str = None, password: str = None, access_code: str = None) -> dict:
    """
    Add a new user to the system.
    
    Args:
        email: User's email address
        role: User role ('admin' or 'evaluator')
        name: User's full name
        department: User's department
        institution: User's institution
        password: Optional password (auto-generated if not provided)
        access_code: 6-digit access code for the user
    
    Returns:
        Dictionary with success status and message
    """
    try:
        # Use service client for admin operations
        supabase = get_supabase_service_client()
        
        # Check if user already exists in profiles
        existing_user = supabase.table('profiles').select('*').eq('email', email).execute()
        if existing_user.data:
            return {'success': False, 'message': f'User with email {email} already exists'}
        
        # Use provided password or generate a secure one following auth.py rules
        if password:
            temp_password = password
        else:
            temp_password = generate_secure_password(12)
        
        # Set access code expiration (30 minutes from now)
        access_code_expires_at = datetime.now() + timedelta(minutes=30)
        
        # Create user in Supabase Auth using admin API
        auth_response = supabase.auth.admin.create_user({
            'email': email,
            'password': temp_password,
            'email_confirm': True,
        })
        
        user_id = auth_response.user.id
        
        # Check if profile already exists (from previous failed attempt)
        existing_profile = supabase.table('profiles').select('*').eq('id', user_id).execute()
        if existing_profile.data:
            # Update existing profile instead of inserting
            user_data = {
                'email': email,
                'role': role,
                'name': name,
                'department': department,
                'institution': institution,
                'access_code': access_code,
                'access_code_expires_at': access_code_expires_at.isoformat()
            }
            # Remove None values
            user_data = {k: v for k, v in user_data.items() if v is not None}
            result = supabase.table('profiles').update(user_data).eq('id', user_id).execute()
        else:
            # Create new profile
            user_data = {
                'id': user_id,
                'email': email,
                'role': role,
                'name': name,
                'department': department,
                'institution': institution,
                'access_code': access_code,
                'access_code_expires_at': access_code_expires_at.isoformat()
            }
            # Remove None values
            user_data = {k: v for k, v in user_data.items() if v is not None}
            result = supabase.table('profiles').insert(user_data).execute()
        
        # Log audit entry
        current_user = get_current_user()
        if current_user and hasattr(current_user, 'user') and hasattr(current_user.user, 'email'):
            actor_email = current_user.user.email
        else:
            actor_email = 'admin@qualcheck.edu'
        log_audit_entry(
            actor_email=actor_email,
            action='Added user',
            detail={
                'user_email': email,
                'role': role,
                'name': name,
                'department': department,
                'institution': institution
            }
        )
        
        # Send welcome email with credentials
        try:
            email_service = get_email_service()
            user_display_name = name if name else email.split('@')[0]
            login_url = "http://localhost:8000"  # Adjust as needed
            
            email_service.send_welcome_email(
                to_email=email,
                user_name=user_display_name,
                temporary_password=temp_password,
                login_url=login_url,
                access_code=access_code
            )
            print(f"Welcome email sent to {email}")
        except Exception as email_error:
            print(f"Failed to send welcome email: {email_error}")
            # Continue even if email fails - user is still created
        
        return {
            'success': True, 
            'message': f'User {email} added successfully. Temporary password: {temp_password}', 
            'data': result.data[0],
            'temp_password': temp_password
        }
        
    except Exception as e:
        print(f"Error adding user: {e}")
        return {'success': False, 'message': f'Error adding user: {str(e)}'}


def get_all_users() -> list:
    """
    Fetch all users from the database.
    
    Returns:
        List of user dictionaries
    """
    try:
        supabase = get_supabase_client()
        response = supabase.table('profiles').select('*').order('created_at', desc=True).execute()
        return response.data
    except Exception as e:
        print(f"Error fetching users: {e}")
        return []
