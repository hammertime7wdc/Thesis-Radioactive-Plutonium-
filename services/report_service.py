import csv
import os
from html import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def export_evaluations_to_csv(evaluations: list, file_path: str) -> bool:
    if not file_path:
        return False

    fieldnames = [
        "file_name",
        "output_type",
        "classification",
        "similarity_score_percent",
        "criterion_scores",
        "prompt",
        "created_at",
    ]

    try:
        with open(file_path, "w", newline="", encoding="utf-8-sig") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for evaluation in evaluations:
                criteria = evaluation.get("criterion_scores") or {}
                criterion_text = "; ".join(
                    f"{name}: {float(value) * 100:.1f}%"
                    for name, value in criteria.items()
                )
                similarity = evaluation.get("similarity_score")
                if similarity is not None:
                    similarity = float(similarity) * 100
                writer.writerow(
                    {
                        "file_name": evaluation.get("file_name") or "Untitled",
                        "output_type": evaluation.get("output_type") or "",
                        "classification": evaluation.get("classification") or "",
                        "similarity_score_percent": (
                            f"{similarity:.1f}" if similarity is not None else ""
                        ),
                        "criterion_scores": criterion_text,
                        "prompt": evaluation.get("prompt") or "",
                        "created_at": evaluation.get("created_at") or "",
                    }
                )
        return True
    except (OSError, TypeError, ValueError) as error:
        print(f"CSV export error: {error}")
        return False


def export_evaluation_to_pdf(evaluation: dict, file_path: str) -> bool:
    if not file_path:
        return False

    try:
        styles = getSampleStyleSheet()
        body_style = styles["BodyText"]
        body_style.leading = 14
        small_style = styles["BodyText"].clone("SmallBody")
        small_style.fontSize = 9
        small_style.leading = 11

        document = SimpleDocTemplate(
            file_path,
            pagesize=letter,
            rightMargin=0.65 * inch,
            leftMargin=0.65 * inch,
            topMargin=0.65 * inch,
            bottomMargin=0.65 * inch,
        )
        story = [
            Paragraph("QualCheck Evaluation Report", styles["Title"]),
            Spacer(1, 0.18 * inch),
        ]

        similarity = evaluation.get("similarity_score")
        score_text = f"{float(similarity) * 100:.1f}%" if similarity is not None else "N/A"
        story.append(
            Table(
                [
                    ["Submission", escape(str(evaluation.get("file_name") or "Untitled"))],
                    ["Output type", escape(str(evaluation.get("output_type") or "N/A"))],
                    ["Classification", escape(str(evaluation.get("classification") or "N/A"))],
                    ["Similarity score", score_text],
                    ["Evaluated", escape(str(evaluation.get("created_at") or "N/A"))],
                ],
                colWidths=[1.35 * inch, 5.85 * inch],
                style=TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
                        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                        ("PADDING", (0, 0), (-1, -1), 7),
                    ]
                ),
            )
        )
        story.extend([Spacer(1, 0.2 * inch), Paragraph("Question", styles["Heading2"])])
        story.append(Paragraph(escape(str(evaluation.get("prompt") or "No question saved.")), body_style))

        story.extend([Spacer(1, 0.18 * inch), Paragraph("Rubric and criterion scores", styles["Heading2"])])
        criteria = evaluation.get("criterion_scores") or {}
        rubric_details = evaluation.get("rubric_details") or []
        if isinstance(rubric_details, dict):
            rubric_details = [
                {"name": name, "description": description}
                for name, description in rubric_details.items()
            ]
        descriptions = {
            item.get("name"): item.get("description", "")
            for item in rubric_details
            if isinstance(item, dict)
        }
        criterion_rows = [["Criterion", "Score", "Description"]]
        for name, value in criteria.items():
            criterion_rows.append(
                [
                    escape(str(name)),
                    f"{float(value) * 100:.1f}%",
                    Paragraph(escape(str(descriptions.get(name) or "")), small_style),
                ]
            )
        if len(criterion_rows) == 1:
            criterion_rows.append(["No criterion scores saved.", "", ""])
        story.append(
            Table(
                criterion_rows,
                colWidths=[1.5 * inch, 0.8 * inch, 4.9 * inch],
                repeatRows=1,
                style=TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("PADDING", (0, 0), (-1, -1), 6),
                    ]
                ),
            )
        )
        document.build(story)
        return True
    except (OSError, TypeError, ValueError) as error:
        print(f"PDF export error: {error}")
        return False


def export_evaluations_to_pdf(evaluations: list, file_path: str) -> bool:
    """Write all evaluation results into one compact PDF table."""
    if not file_path:
        return False

    try:
        styles = getSampleStyleSheet()
        body_style = styles["BodyText"].clone("ReportBody")
        body_style.fontSize = 9
        body_style.leading = 11
        table_style = styles["BodyText"].clone("ReportTable")
        table_style.fontSize = 8
        table_style.leading = 9
        document = SimpleDocTemplate(
            file_path,
            pagesize=landscape(letter),
            rightMargin=0.4 * inch,
            leftMargin=0.4 * inch,
            topMargin=0.4 * inch,
            bottomMargin=0.4 * inch,
        )
        story = [
            Paragraph("QualCheck Evaluation Results", styles["Heading1"]),
            Spacer(1, 0.08 * inch),
            Paragraph(f"Total submissions: {len(evaluations)}", body_style),
            Spacer(1, 0.08 * inch),
        ]

        prompt = evaluations[0].get("prompt") if evaluations else ""
        story.extend(
            [
                Paragraph("<b>Question:</b> " + escape(str(prompt or "N/A")), body_style),
                Spacer(1, 0.1 * inch),
            ]
        )

        criterion_names = []
        for evaluation in evaluations:
            for name in (evaluation.get("criterion_scores") or {}):
                if name not in criterion_names:
                    criterion_names.append(name)

        headers = ["#", "Submission", "Type", "Score", "Classification"]
        headers.extend(criterion_names)
        rows = [headers]
        for index, evaluation in enumerate(evaluations, 1):
            similarity = evaluation.get("similarity_score")
            score_text = f"{float(similarity) * 100:.1f}%" if similarity is not None else "N/A"
            criteria = evaluation.get("criterion_scores") or {}
            rows.append(
                [
                    str(index),
                    Paragraph(escape(str(evaluation.get("file_name") or "Untitled")), table_style),
                    Paragraph(escape(str(evaluation.get("output_type") or "N/A")), table_style),
                    score_text,
                    Paragraph(escape(str(evaluation.get("classification") or "N/A")), table_style),
                    *[
                        f"{float(criteria[name]) * 100:.1f}%"
                        if name in criteria
                        else "—"
                        for name in criterion_names
                    ],
                ]
            )
        if not rows[1:]:
            rows.append(["", "No evaluation results.", "", "", "", *("" for _ in criterion_names)])

        column_widths = [0.3 * inch, 2.15 * inch, 0.85 * inch, 0.65 * inch, 1.15 * inch]
        column_widths.extend([0.85 * inch] * len(criterion_names))
        story.append(
            Table(
                rows,
                colWidths=column_widths,
                repeatRows=1,
                hAlign="LEFT",
                style=TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ("PADDING", (0, 0), (-1, -1), 4),
                    ]
                ),
            )
        )

        document.build(story)
        return True
    except (OSError, TypeError, ValueError) as error:
        print(f"PDF batch export error: {error}")
        return False


def safe_export_name(value: str, suffix: str) -> str:
    cleaned = "".join(
        character if character.isalnum() or character in (" ", "-", "_") else "_"
        for character in (value or "evaluation")
    ).strip()
    return f"{cleaned or 'evaluation'}{suffix}"
