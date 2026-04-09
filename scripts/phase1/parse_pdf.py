"""
PDF Parser — Phase 1
Extracts text from mutual fund KIM/SID PDFs using pdfplumber.

Rules:
- Extract text page by page
- Preserve tables as markdown (critical for KIM fact sheets)
- Skip image-only pages and flag them in the log
- Return cleaned text + a list of flagged page numbers
"""

import re
import io
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class PDFParseResult:
    text: str
    total_pages: int
    extracted_pages: int
    image_only_pages: list[int] = field(default_factory=list)
    has_tables: bool = False


def _table_to_markdown(table: list[list[Optional[str]]]) -> str:
    """
    Convert a pdfplumber table (list of rows, each row is list of cell strings)
    into a markdown text table.
    """
    if not table:
        return ""

    # Normalize cells — replace None with empty string
    normalized = []
    for row in table:
        normalized.append([cell.strip() if cell else "" for cell in row])

    # Find the max columns
    max_cols = max(len(row) for row in normalized)

    lines = []
    for i, row in enumerate(normalized):
        # Pad row to max_cols
        padded = row + [""] * (max_cols - len(row))
        lines.append(" | ".join(padded))
        if i == 0:
            lines.append(" | ".join(["---"] * max_cols))

    return "\n".join(lines)


def _clean_text(text: str) -> str:
    """Normalize extracted PDF text."""
    # Remove excessive whitespace while preserving paragraph breaks
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove common PDF artifacts: page numbers at start/end of lines
    text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)
    # Remove repeated dashes/underscores used as visual separators
    text = re.sub(r"[-_]{4,}", "---", text)
    return text.strip()


def parse_pdf(pdf_bytes: bytes, source_url: str = "") -> PDFParseResult:
    """
    Parse a PDF file from raw bytes and return extracted text.

    Args:
        pdf_bytes: Raw PDF content as bytes
        source_url: Used for logging context only

    Returns:
        PDFParseResult with cleaned text and metadata
    """
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("pdfplumber is required: pip install pdfplumber")

    all_parts: list[str] = []
    image_only_pages: list[int] = []
    has_tables = False

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        total_pages = len(pdf.pages)

        for page_num, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text(x_tolerance=3, y_tolerance=3) or ""
            page_tables = page.extract_tables()

            # Detect image-only pages: no text and no tables
            if not page_text.strip() and not page_tables:
                image_only_pages.append(page_num)
                continue

            # Start with a page header for traceability
            all_parts.append(f"\n--- Page {page_num} ---\n")

            # Process tables first (they have positional context)
            if page_tables:
                has_tables = True
                table_texts = []
                for table in page_tables:
                    md_table = _table_to_markdown(table)
                    if md_table:
                        table_texts.append(md_table)

                # Add page prose text
                if page_text.strip():
                    all_parts.append(page_text.strip())

                # Append tables after prose
                for t in table_texts:
                    all_parts.append("\n[TABLE]\n" + t + "\n[/TABLE]\n")
            else:
                if page_text.strip():
                    all_parts.append(page_text.strip())

    raw_combined = "\n".join(all_parts)
    cleaned = _clean_text(raw_combined)

    extracted_pages = total_pages - len(image_only_pages)

    if image_only_pages:
        print(
            f"  [PDF] {source_url}: {len(image_only_pages)} image-only page(s) skipped: {image_only_pages}"
        )

    return PDFParseResult(
        text=cleaned,
        total_pages=total_pages,
        extracted_pages=extracted_pages,
        image_only_pages=image_only_pages,
        has_tables=has_tables,
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python parse_pdf.py <path-to-pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    result = parse_pdf(pdf_bytes, source_url=pdf_path)
    print(f"Pages: {result.extracted_pages}/{result.total_pages} extracted")
    print(f"Image-only pages: {result.image_only_pages}")
    print(f"Contains tables: {result.has_tables}")
    print("\n--- Extracted Text (first 2000 chars) ---\n")
    print(result.text[:2000])
