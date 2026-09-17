from services.supabase_client import get_supabase_client

TYPE_LABELS = {
    "short_answer": "Short Answer",
    "essay": "Essay",
    "code_report": "Code Report",
}


def fetch_submissions():
    """Pull real evaluations + evaluator name for the admin submissions table.

    Relies on RLS: only returns all rows when the current session belongs
    to an admin (per the "Admins can view all evaluations" policy). A
    non-admin session just gets their own rows back, not an error.
    """
    supabase = get_supabase_client()

    try:
        resp = (
            supabase.table("evaluations")
            .select("id, prompt, rubric_details, criterion_scores, file_name, similarity_score, classification, output_type, created_at, user_id, profiles(name)")
            .order("created_at", desc=True)
            .execute()
        )
    except Exception as e:
        print(f"[submissions] fetch failed: {e}")
        return []

    submissions = []
    for r in resp.data or []:
        evaluator_name = (r.get("profiles") or {}).get("name") or "Unknown"
        score = r.get("similarity_score")
        submissions.append({
            "file": r.get("file_name") or "untitled",
            "score": f"{float(score) * 100:.0f}%" if score is not None else "—",
            "classification": [r.get("classification") or "Unclassified"],
            "type": TYPE_LABELS.get(r.get("output_type"), r.get("output_type") or "—"),
            "evaluator": evaluator_name,
            "date": (r.get("created_at") or "")[:16].replace("T", " "),
            "prompt": r.get("prompt") or "",
            "rubric_details": r.get("rubric_details") or [],
            "criterion_scores": r.get("criterion_scores") or {},
        })
    return submissions