# pdf_extractor.py
# Extracts raw text from a PDF file using pdfplumber.
# Handles multi-page PDFs, strips excessive whitespace, and returns clean text.

import io
import pdfplumber


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract all text from a PDF given its raw bytes.
    Returns clean, concatenated text from all pages.
    Falls back gracefully if a page fails to parse.
    """
    extracted_pages = []

    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for i, page in enumerate(pdf.pages):
                try:
                    text = page.extract_text(x_tolerance=3, y_tolerance=3)
                    if text:
                        extracted_pages.append(text.strip())
                except Exception as e:
                    # Skip individual pages that fail, don't crash the whole extraction
                    extracted_pages.append(f"[Page {i+1} could not be parsed]")

    except Exception as e:
        raise ValueError(f"Failed to open or parse PDF: {str(e)}")

    if not extracted_pages:
        raise ValueError("No text could be extracted from the PDF. It may be image-only or corrupted.")

    full_text = "\n\n".join(extracted_pages)

    # Clean up excessive whitespace while preserving structure
    lines = full_text.splitlines()
    cleaned_lines = []
    prev_blank = False
    for line in lines:
        stripped = line.strip()
        if stripped:
            cleaned_lines.append(stripped)
            prev_blank = False
        elif not prev_blank:
            cleaned_lines.append("")
            prev_blank = True

    return "\n".join(cleaned_lines).strip()


def extract_text_from_string(text: str) -> str:
    """
    Pass-through for plain text resumes (not PDF).
    Cleans up formatting.
    """
    lines = text.splitlines()
    cleaned = [line.strip() for line in lines if line.strip()]
    return "\n".join(cleaned)
