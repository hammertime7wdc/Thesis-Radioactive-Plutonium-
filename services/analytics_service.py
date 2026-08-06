from collections import defaultdict
from datetime import datetime, timedelta, timezone
from services.supabase_client import get_supabase_client


def fetch_analytics_summary(days: int = 30) -> dict:
    """Pull real stat-card, pie-chart, and per-criterion data for the admin
    analytics page. Scoped to the last `days` days, matching the
    "Last 30 days" header.
    """
    supabase = get_supabase_client()
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    since_week = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    try:
        window_resp = (
            supabase.table("evaluations")
            .select("similarity_score, classification, criterion_scores, output_type, created_at")
            .gte("created_at", since)
            .execute()
        )
        rows = window_resp.data or []

        week_resp = (
            supabase.table("evaluations")
            .select("id", count="exact")
            .gte("created_at", since_week)
            .execute()
        )
        week_count = week_resp.count or 0

    except Exception as e:
        print(f"[analytics] fetch failed: {e}")
        return _empty_summary()

    total = len(rows)

    scores = [float(r["similarity_score"]) for r in rows if r.get("similarity_score") is not None]
    avg_similarity = sum(scores) / len(scores) if scores else 0.0

    counts = {"Fully Relevant": 0, "Partially Relevant": 0, "Irrelevant": 0}
    for r in rows:
        label = r.get("classification")
        if label in counts:
            counts[label] += 1

    if total > 0:
        fully_pct = round(counts["Fully Relevant"] / total * 100)
        partial_pct = round(counts["Partially Relevant"] / total * 100)
        irrelevant_pct = 100 - fully_pct - partial_pct  # remainder, avoids rounding drift off 100
    else:
        fully_pct = partial_pct = irrelevant_pct = 0

    criterion_labels, criterion_values, criterion_ns = fetch_criterion_averages(rows)

    return {
        "total_evaluations": total,
        "evaluations_delta": f"+{week_count} this week",
        "avg_similarity_score": avg_similarity,
        "fully_pct": fully_pct,
        "partial_pct": partial_pct,
        "irrelevant_pct": irrelevant_pct,
        "criterion_labels": criterion_labels,
        "criterion_values": criterion_values,
        "criterion_ns": criterion_ns,
    }


# Presentation labels + fixed ordering for known criterion keys. Anything
# not in this map falls back to its raw key, title-cased.
_CRITERION_LABELS = {
    "content": "Content",
    "organization": "Organization",
    "language": "Language",
    "accuracy": "Accuracy",
    "key_concept": "Key Concept",
    "clarity": "Clarity",
    "constraint_adherence": "Constraint",
    "technical_terminology": "Terminology",
    "clarity_cohesion": "Clarity & Cohesion",
    "algorithmic_logic": "Logic",
}
_CRITERION_ORDER = [
    "content", "organization", "language", "accuracy", "key_concept",
    "clarity", "constraint_adherence", "technical_terminology",
    "clarity_cohesion", "algorithmic_logic",
]


def fetch_criterion_averages(rows: list[dict]):
    """Average each criterion key found in `criterion_scores` across every
    row that has it, skipping rows where the column is null (older rows
    predating the column, or code-report rows which don't persist at all
    yet). Returns (labels, values_0_to_100, sample_counts).

    NOTE (short answer): evaluate_combined() shares one similarity value
    across accuracy/key_concept/clarity by model design -- see its
    docstring in evaluation.py. Averaging still produces a real number,
    it just means those three bars will move together, not independently,
    for any short-answer-sourced rows. That's an accurate reflection of
    the model, not an aggregation bug.
    """
    sums = defaultdict(float)
    counts = defaultdict(int)

    for r in rows:
        cs = r.get("criterion_scores")
        if not cs:
            continue
        for key, val in cs.items():
            if val is None:
                continue
            sums[key] += float(val)
            counts[key] += 1

    if not counts:
        return [], [], []

    # Known keys first in fixed order, then any unrecognized keys appended
    ordered_keys = [k for k in _CRITERION_ORDER if k in counts]
    ordered_keys += [k for k in counts if k not in _CRITERION_ORDER]

    labels = [_CRITERION_LABELS.get(k, k.replace("_", " ").title()) for k in ordered_keys]
    values = [round((sums[k] / counts[k]) * 100, 1) for k in ordered_keys]
    ns = [counts[k] for k in ordered_keys]

    return labels, values, ns


def _empty_summary() -> dict:
    return {
        "total_evaluations": 0,
        "evaluations_delta": "+0 this week",
        "avg_similarity_score": 0.0,
        "fully_pct": 0,
        "partial_pct": 0,
        "irrelevant_pct": 0,
        "criterion_labels": [],
        "criterion_values": [],
        "criterion_ns": [],
    }