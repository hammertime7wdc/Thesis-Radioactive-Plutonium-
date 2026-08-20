import os
import json
from services.supabase_client import get_supabase_client

SESSION_FILE = ".session.json"


def save_session(access_token, refresh_token, user_id):
    """Save session tokens to local storage"""
    session_data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user_id": user_id
    }
    
    session_path = os.path.join(os.path.dirname(__file__), "..", SESSION_FILE)
    with open(session_path, "w") as f:
        json.dump(session_data, f)


def load_session():
    """Load session from local storage and restore Supabase client"""
    session_path = os.path.join(os.path.dirname(__file__), "..", SESSION_FILE)
    
    if not os.path.exists(session_path):
        return None
    
    try:
        with open(session_path, "r") as f:
            session_data = json.load(f)
        
        supabase = get_supabase_client()
        
        # Restore session
        supabase.auth.set_session(
            access_token=session_data["access_token"],
            refresh_token=session_data["refresh_token"]
        )

        # Re-check is_active on every restore, not just at login time,
        # so a user banned mid-session is booted out on next launch
        profile_response = (
            supabase.table("profiles")
            .select("is_active")
            .eq("id", session_data["user_id"])
            .single()
            .execute()
        )
        is_active = profile_response.data.get("is_active", True) if profile_response.data else True

        if not is_active:
            try:
                supabase.auth.sign_out()
            except Exception:
                pass
            clear_session()
            return None

        return session_data
    except Exception as e:
        print(f"Error loading session: {e}")
        clear_session()
        return None


def refresh_session():
    """Refresh the current session using refresh token"""
    session_data = load_session()
    if not session_data:
        return False
    
    try:
        supabase = get_supabase_client()
        session = supabase.auth.refresh_session(session_data["refresh_token"])
        
        # Update saved session with new tokens
        save_session(
            session.access_token,
            session.refresh_token,
            session_data["user_id"]
        )
        
        return True
    except Exception as e:
        print(f"Error refreshing session: {e}")
        clear_session()
        return False


def clear_session():
    """Clear saved session from local storage"""
    session_path = os.path.join(os.path.dirname(__file__), "..", SESSION_FILE)
    if os.path.exists(session_path):
        os.remove(session_path)


def logout():
    """Fully sign the user out: invalidate the Supabase session and
    remove the locally persisted session file.

    This is the function UI logout buttons should call. Previously the
    logout buttons only swapped the screen back to the login page without
    ever calling this, so the Supabase client still held a valid session
    and .session.json was left on disk — meaning the app (or the next
    person to open it) would get silently logged back in as the same
    user on the next launch.
    """
    try:
        supabase = get_supabase_client()
        supabase.auth.sign_out()
    except Exception as e:
        print(f"Error signing out: {e}")
    finally:
        clear_session()


def get_current_user():
    """Get current authenticated user from session"""
    session_data = load_session()
    if not session_data:
        return None
    
    try:
        supabase = get_supabase_client()
        user = supabase.auth.get_user()
        return user
    except Exception as e:
        print(f"Error getting current user: {e}")
        clear_session()
        return None


def get_user_role():
    """Get current user's role from profiles table"""
    session_data = load_session()
    if not session_data:
        return None
    
    try:
        supabase = get_supabase_client()
        profile_response = supabase.table("profiles").select("role").eq("id", session_data["user_id"]).single().execute()
        return profile_response.data.get("role", "evaluator")
    except Exception as e:
        print(f"Error getting user role: {e}")
        return None