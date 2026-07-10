import os
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


def _get_service_client() -> Client | None:
    """
    Create a Supabase client using the SERVICE ROLE key.

    This bypasses Row Level Security (RLS), which is what we want here:
    log_activity() and get_recent_activities() are called from trusted
    backend code with an already-validated user_id, not directly from
    the browser. The service role key must NEVER be exposed client-side.
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_service_key:
        print("Supabase service role credentials not found for activity logging")
        return None

    return create_client(supabase_url, supabase_service_key)


def log_activity(user_id: str, activity_type: str, description: str, metadata: dict = None):
    """
    Log a user activity to the user_activities table.

    Args:
        user_id: The UUID of the user
        activity_type: Type of activity (e.g., 'profile_update', 'avatar_upload', 'password_change')
        description: Human-readable description of the activity
        metadata: Optional additional data as JSON
    """
    try:
        supabase = _get_service_client()
        if supabase is None:
            return

        activity_data = {
            "user_id": user_id,
            "activity_type": activity_type,
            "description": description,
            "metadata": metadata or {},
        }

        supabase.table("user_activities").insert(activity_data).execute()

    except Exception as e:
        print(f"Error logging activity: {e}")


def get_recent_activities(user_id: str, limit: int = 5):
    """
    Fetch recent activities for a user from user_activities table.

    Args:
        user_id: The UUID of the user
        limit: Maximum number of activities to return

    Returns:
        List of activity dictionaries
    """
    try:
        supabase = _get_service_client()
        if supabase is None:
            return []

        result = (
            supabase.table("user_activities")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        activities = []
        if result.data:
            for item in result.data:
                activities.append(
                    {
                        "activity_type": item.get("activity_type"),
                        "description": item.get("description", "Unknown activity"),
                        "created_at": item.get("created_at"),
                    }
                )

        return activities

    except Exception as e:
        print(f"Error fetching activities: {e}")
        return []