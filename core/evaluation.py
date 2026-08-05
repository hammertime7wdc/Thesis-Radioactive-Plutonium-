"""
Evaluation module for QualCheck
Cosine similarity scoring and theta1/theta2 threshold classification,
calibrated per Chapter 3 methodology.
"""

import json
import numpy as np
from typing import Dict, List


class Evaluator:
    """Evaluate student responses against rubric criteria."""

    def __init__(self, embedding_generator, meta_path: str = "qualcheck_short_answers_final_meta.json"):
        """
        Args:
            embedding_generator: Instance of EmbeddingGenerator
            meta_path: Path to qualcheck_short_answers_final_meta.json (theta1/theta2 live here)
        """
        self.embedding_generator = embedding_generator

        with open(meta_path, "r") as f:
            meta = json.load(f)

        self.theta1 = meta["theta1"]  # >= theta1  -> Fully Relevant
        self.theta2 = meta["theta2"]  # >= theta2  -> Partially Relevant, else Irrelevant

    def cosine_similarity(self, vec1: list, vec2: list) -> float:
        """Calculate cosine similarity between two vectors."""
        v1, v2 = np.array(vec1, dtype=np.float64), np.array(vec2, dtype=np.float64)
        denom = np.linalg.norm(v1) * np.linalg.norm(v2)
        if denom == 0:
            return 0.0
        return float(np.dot(v1, v2) / denom)

    def classify(self, similarity: float) -> str:
        """Map a raw cosine similarity to Fully/Partially/Irrelevant using theta1/theta2."""
        if similarity >= self.theta1:
            return "Fully Relevant"
        elif similarity >= self.theta2:
            return "Partially Relevant"
        else:
            return "Irrelevant"

    def evaluate_combined(
        self,
        question: str,
        student_response: str,
        rubric_criteria: Dict[str, str],
    ) -> Dict[str, dict]:
        """
        Short-answer evaluation — architecturally different from evaluate_response()/essay.
        The short-answer training notebook concatenates ALL rubric criteria into
        ONE full_rubric string (e.g. "Accuracy of Answer: ... Key Concept: ...
        Clarity: ...") and pair-encodes it with the question as a SINGLE P input.
        There is no per-criterion similarity in this model — only one overall
        similarity per response. This method returns that same overall result
        under each criterion key (rather than 3 independent scores) so the
        existing per-criterion UI rendering still works without a redesign —
        but the number is genuinely shared, not independently computed per
        criterion. Order of rubric_criteria matters: pass it in the same
        Accuracy of Answer / Key Concept / Clarity order the UI collects it in.

        Args:
            question: The academic prompt (prompt_field.value in the UI).
            student_response: Student's response text.
            rubric_criteria: {criterion_name: criterion_description}, in
                              display order — gets concatenated into one
                              full_rubric string.

        Returns:
            {criterion_name: {"similarity": float, "label": str}} — same
            similarity/label repeated for every criterion key.
        """
        full_rubric = " ".join(
            f"{name}: {(desc or '').strip()}" for name, desc in rubric_criteria.items()
        )

        p_embedding = self.embedding_generator.encode_pair(question, full_rubric)
        r_embedding = self.embedding_generator.encode_single(student_response)

        similarity = self.cosine_similarity(p_embedding, r_embedding)
        label = self.classify(similarity)

        return {name: {"similarity": similarity, "label": label} for name in rubric_criteria}

    def evaluate_response(
        self,
        question: str,
        student_response: str,
        rubric_criteria: Dict[str, str],
    ) -> Dict[str, dict]:
        """
        Evaluate a student response against rubric criteria.
        Matches evaluate_essay() / _single_criterion_similarity_essay() from
        the training notebook exactly:
          P = [CLS] question [SEP] full_rubric [SEP]   (pair-encoded, CLS pooled)
          R = [CLS] response [SEP]                      (single-encoded, CLS pooled)
          similarity = cosine(P, R)

        Args:
            question: The academic prompt (prompt_field.value in the UI).
                      Required — the model was trained with this as half of
                      the P-side input, so omitting it produces meaningless
                      near-constant similarities regardless of response content.
            student_response: Student's response text (already PDF-extracted + preprocessed)
            rubric_criteria: {criterion_name: criterion_description} — the
                              professor's typed rubric text. Gets wrapped as
                              "{criterion_name}. {description}" to match
                              full_rubric construction in training.

        Returns:
            {criterion_name: {"similarity": float, "label": str}}
        """
        results = {}
        for criterion_name, criterion_description in rubric_criteria.items():
            full_rubric = f"{criterion_name}. {(criterion_description or '').strip()}"

            p_embedding = self.embedding_generator.encode_pair(question, full_rubric)
            r_embedding = self.embedding_generator.encode_single(student_response)

            similarity = self.cosine_similarity(p_embedding, r_embedding)
            results[criterion_name] = {
                "similarity": similarity,
                "label": self.classify(similarity),
            }
        return results

    def evaluate_batch(
        self,
        question: str,
        student_responses: List[str],
        rubric_criteria: Dict[str, str],
    ) -> List[Dict[str, dict]]:
        """Evaluate multiple student responses against the same rubric + question."""
        return [self.evaluate_response(question, r, rubric_criteria) for r in student_responses]

    def calculate_overall_score(self, criterion_scores: Dict[str, dict], method: str = "mean") -> float:
        """
        Calculate overall similarity from per-criterion scores.

        Args:
            criterion_scores: Output of evaluate_response()
            method: "mean" (default) or "min" (weakest-link, matches your
                    code report / essay notebooks — switch to this if you want
                    short answer to use the same aggregation rule)
        """
        if not criterion_scores:
            return 0.0
        sims = [v["similarity"] for v in criterion_scores.values()]
        return min(sims) if method == "min" else sum(sims) / len(sims)