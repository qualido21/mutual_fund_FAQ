"""
HTML Parser — Phase 1
Cleans raw HTML from AMC/AMFI/SEBI pages into plain readable text.

Rules:
- Strip: nav, header, footer, scripts, styles, cookie banners, ads
- Keep: headings, paragraphs, tables, lists
- Tables → converted to markdown format for LLM readability
- Output is UTF-8 plain text with preserved structure
"""

import re
from bs4 import BeautifulSoup, Tag


# Tags to remove entirely (with their children)
REMOVE_TAGS = {
    "script", "style", "noscript", "iframe",
    "nav", "header", "footer", "aside",
    "form", "button", "input", "select", "textarea",
    "svg", "canvas", "figure",
}

# CSS class/id substrings that indicate boilerplate to remove
REMOVE_CLASS_PATTERNS = [
    "cookie", "banner", "popup", "modal", "overlay", "toast",
    "advertisement", "ads", "ad-", "-ad", "promo", "sidebar",
    "social", "share", "newsletter", "subscribe", "disclaimer-bar",
    "sticky", "breadcrumb", "pagination", "search-bar",
]


def _should_remove_by_class(tag: Tag) -> bool:
    if not tag.attrs:
        return False
    classes = " ".join(tag.get("class", []))
    tag_id = tag.get("id", "")
    combined = (classes + " " + tag_id).lower()
    return any(pat in combined for pat in REMOVE_CLASS_PATTERNS)


def _table_to_markdown(table: Tag) -> str:
    """Convert an HTML table to a markdown-style text table."""
    rows = []
    for tr in table.find_all("tr"):
        cells = []
        for cell in tr.find_all(["td", "th"]):
            text = cell.get_text(separator=" ", strip=True)
            text = re.sub(r"\s+", " ", text)
            cells.append(text)
        if cells:
            rows.append(" | ".join(cells))

    if not rows:
        return ""

    # Insert a separator after the first row (header row)
    if len(rows) > 1:
        header = rows[0]
        separator = " | ".join(["---"] * len(rows[0].split(" | ")))
        rows = [header, separator] + rows[1:]

    return "\n".join(rows)


def _extract_text_from_tag(tag: Tag) -> str:
    """Recursively extract clean text from a tag, applying table conversion."""
    if tag.name == "table":
        return _table_to_markdown(tag) + "\n"

    parts = []
    for child in tag.children:
        if isinstance(child, str):
            text = child.strip()
            if text:
                parts.append(text)
        elif isinstance(child, Tag):
            if child.name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
                heading_text = child.get_text(separator=" ", strip=True)
                level = int(child.name[1])
                parts.append("\n" + "#" * level + " " + heading_text + "\n")
            elif child.name == "table":
                parts.append("\n" + _table_to_markdown(child) + "\n")
            elif child.name in {"p", "div", "section", "article", "main"}:
                inner = _extract_text_from_tag(child).strip()
                if inner:
                    parts.append(inner + "\n")
            elif child.name in {"li"}:
                inner = child.get_text(separator=" ", strip=True)
                if inner:
                    parts.append("- " + inner)
            elif child.name in {"ul", "ol"}:
                inner = _extract_text_from_tag(child).strip()
                if inner:
                    parts.append(inner + "\n")
            elif child.name in {"br"}:
                parts.append("\n")
            elif child.name in {"span", "a", "strong", "b", "em", "i", "label"}:
                text = child.get_text(separator=" ", strip=True)
                if text:
                    parts.append(text)
            else:
                inner = _extract_text_from_tag(child).strip()
                if inner:
                    parts.append(inner)

    return " ".join(parts)


def parse_html(html_content: str, _source_url: str = "") -> str:
    """
    Parse raw HTML and return cleaned plain text.

    Args:
        html_content: Raw HTML string
        source_url: Used for logging context only

    Returns:
        Cleaned plain text string suitable for embedding
    """
    soup = BeautifulSoup(html_content, "lxml")

    # Remove unwanted tags outright
    for tag_name in REMOVE_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # Remove elements matching boilerplate class/id patterns
    for tag in soup.find_all(True):
        if _should_remove_by_class(tag):
            tag.decompose()

    # Find the main content area; fallback to body
    main = (
        soup.find("main")
        or soup.find("article")
        or soup.find(id=re.compile(r"(content|main|body)", re.I))
        or soup.find(class_=re.compile(r"(content|main|body)", re.I))
        or soup.find("body")
        or soup
    )

    raw_text = _extract_text_from_tag(main)

    # Normalize whitespace
    lines = []
    for line in raw_text.splitlines():
        stripped = line.strip()
        if stripped:
            lines.append(stripped)
        else:
            # Preserve single blank lines as paragraph separators
            if lines and lines[-1] != "":
                lines.append("")

    cleaned = "\n".join(lines).strip()

    # Collapse 3+ consecutive blank lines to 2
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned


if __name__ == "__main__":
    # Quick smoke test with a minimal HTML snippet
    sample = """
    <html>
      <head><title>Test</title></head>
      <body>
        <nav>Nav menu here</nav>
        <header>Site header</header>
        <main>
          <h1>Expense Ratio</h1>
          <p>The expense ratio of this fund is 0.54% per annum for the Direct Plan.</p>
          <h2>Exit Load</h2>
          <p>1% exit load if redeemed within 365 days.</p>
          <table>
            <tr><th>Plan</th><th>Expense Ratio</th></tr>
            <tr><td>Direct</td><td>0.54%</td></tr>
            <tr><td>Regular</td><td>1.62%</td></tr>
          </table>
        </main>
        <footer>Footer content</footer>
        <script>alert('ad')</script>
      </body>
    </html>
    """
    result = parse_html(sample, _source_url="https://example.com")
    print(result)
