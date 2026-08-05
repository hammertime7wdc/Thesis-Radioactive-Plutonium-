"""
PDF processing module for QualCheck
Extracts and preprocesses text from student-submitted PDFs.
"""

from typing import List
from pypdf import PdfReader


class PDFProcessor:
    """Process PDF files and extract text."""

    def extract_text(self, pdf_path: str) -> str:
        """
        Extract text from a PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Preprocessed extracted text as string
        """
        reader = PdfReader(pdf_path)
        raw = ""
        for page in reader.pages:
            raw += (page.extract_text() or "") + "\n"
        return self.preprocess_text(raw)

    def extract_text_batch(self, pdf_paths: List[str]) -> List[str]:
        """
        Extract text from multiple PDF files.

        Args:
            pdf_paths: List of PDF file paths

        Returns:
            List of extracted texts, same order as input
        """
        return [self.extract_text(path) for path in pdf_paths]

    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text for embedding generation: strip, collapse
        newlines/whitespace. No NLTK/spaCy steps — WordPiece tokenization
        handles the rest (per Chapter 3 methodology).

        Args:
            text: Raw extracted text

        Returns:
            Cleaned single-line text
        """
        text = text.strip()
        text = text.replace("\r", " ").replace("\n", " ")
        text = " ".join(text.split())
        return text