"""
Data layer for the admin users screen.

All Supabase reads/writes related to user profiles live here so the
screen module only has to deal with rendering and user interaction.
"""

from services.supabase_client import get_supabase_client


def fetch_users_with_evaluations() -> list[dict]:
    """Fetch every profile row plus its evaluation count and active flag.

    Returns an empty list (and logs) if the profiles fetch itself fails.
    A failure to fetch evaluation counts for an individual user degrades
    that user's count to 0 rather than failing the whole page.
    """
    users_data: list[dict] = []
    try:
        supabase = get_supabase_client()
        profiles_response = supabase.table("profiles").select("*").execute()
        users_data = profiles_response.data if profiles_response.data else []
    except Exception as e:
        print(f"Error fetching users: {e}")
        return []

    for user in users_data:
        try:
            supabase = get_supabase_client()
            eval_response = (
                supabase.table("evaluations")
                .select("id", count="exact")
                .eq("user_id", user["id"])
                .execute()
            )
            user["evaluations_count"] = eval_response.count if eval_response.count else 0
        except Exception:
            user["evaluations_count"] = 0

    # Default is_active for rows created before the column existed
    for user in users_data:
        if "is_active" not in user:
            user["is_active"] = True

    return users_data


def set_user_active_status(user_id: str, is_active: bool) -> bool:
    """Placeholder for user status toggle - not implemented yet"""
    print(f"Placeholder: Would toggle user {user_id} to {'active' if is_active else 'inactive'}")
    return True


def filter_users(users_list: list[dict], query: str = "", status_filter: str = "all") -> list[dict]:
    """Filter users by free-text search and an active/inactive tab.

    status_filter: "all" | "active" | "inactive"
    """
    q = (query or "").lower()
    filtered = []
    for u in users_list:
        matches_query = (
            not q
            or q in (u.get("name") or "").lower()
            or q in (u.get("email") or "").lower()
            or q in (u.get("department") or "").lower()
        )
        if not matches_query:
            continue

        is_active = u.get("is_active", True)
        if status_filter == "active" and not is_active:
            continue
        if status_filter == "inactive" and is_active:
            continue

        filtered.append(u)
    return filtered


def count_by_status(users_list: list[dict]) -> tuple[int, int, int]:
    """Return (total, active, inactive) counts for the filter pill labels."""
    total = len(users_list)
    active = sum(1 for u in users_list if u.get("is_active", True))
    inactive = total - active
    return total, active, inactive
