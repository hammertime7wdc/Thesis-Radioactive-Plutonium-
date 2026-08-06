import csv

def export_submissions_to_csv(submissions, file_path):
    """
    Exports submission list data to a specified CSV file path.
    """
    if not file_path:
        return False

    fieldnames = ["file", "score", "classification", "type", "evaluator", "date"]

    try:
        with open(file_path, mode="w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

            for item in submissions:
                row = item.copy()
                # Format classification list to comma-separated text if needed
                if isinstance(row.get("classification"), list):
                    row["classification"] = ", ".join(row["classification"])
                writer.writerow({k: row.get(k, "") for k in fieldnames})
        return True
    except Exception as err:
        print(f"CSV Export Error: {err}")
        return False