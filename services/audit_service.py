from supabase import Client
from services.supabase_client import get_supabase_client, get_supabase_service_client


def log_audit_entry(actor_email: str, action: str, detail: dict = None) -> bool:
    """
    Log an audit entry to the database.
    
    Args:
        actor_email: Email of the user performing the action
        action: Description of the action performed
        detail: Optional JSONB detail dictionary
    
    Returns:
        True if successful, False otherwise
    """
    try:
        supabase = get_supabase_service_client()
        supabase.table('audit_logs').insert({
            'actor_email': actor_email,
            'action': action,
            'detail': detail or {}
        }).execute()
        return True
    except Exception as e:
        print(f"Error logging audit entry: {e}")
        return False


def get_audit_logs(limit: int = 50) -> list:
    """
    Fetch audit logs from the database.
    
    Args:
        limit: Maximum number of logs to return (default: 50)
    
    Returns:
        List of audit log dictionaries with keys: id, actor_email, action, detail, created_at
    """
    try:
        supabase = get_supabase_client()
        response = supabase.table('audit_logs').select('*').order('created_at', desc=True).limit(limit).execute()
        return response.data
    except Exception as e:
        print(f"Error fetching audit logs: {e}")
        return []


def format_audit_log_detail(detail: dict) -> str:
    """
    Format the detail JSONB field into a readable string.
    
    Args:
        detail: JSONB detail dictionary
    
    Returns:
        Formatted string representation
    """
    if not detail:
        return ""
    
    # Handle different detail formats
    if isinstance(detail, str):
        return detail
    
    # Format common detail structures
    if 'file_name' in detail and 'classification' in detail:
        return f"{detail['file_name']} → {detail['classification']}"
    elif 'user_email' in detail and 'role' in detail:
        return f"{detail['user_email']} ({detail['role']})"
    elif 'batch_name' in detail and 'count' in detail:
        return f"{detail['batch_name']} batch ({detail['count']} files)"
    else:
        # Generic fallback
        return str(detail)
