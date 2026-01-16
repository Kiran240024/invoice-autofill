from typing import List, Dict
from collections import defaultdict

def reconstruct_lines(
    words: List[Dict],
    y_threshold: int = 10
) -> List[Dict]:
    """
    Convert word-level OCR output into line-level text.

    Args:
        words: List of normalized OCR words with x, y, page, text
        y_threshold: Max vertical distance to consider words in same line

    Returns:
        List of reconstructed lines with text, page, y
    """

    if not words:
        return []

    # Group words by page
    pages = defaultdict(list)
    for w in words:
        pages[w["page"]].append(w)

    reconstructed_lines = []

    for page, page_words in pages.items():
        # Sort words top-to-bottom
        page_words.sort(key=lambda w: w["y"])

        current_line = []
        current_y = None

        for word in page_words:
            if current_y is None:
                current_line = [word]
                current_y = word["y"]
                continue

            # Same line if Y difference is small
            if abs(word["y"] - current_y) <= y_threshold:
                current_line.append(word)
            else:
                # Finish current line
                reconstructed_lines.append(
                    _finalize_line(current_line, page)
                )
                # Start new line
                current_line = [word]
                current_y = word["y"]

        # Add last line
        if current_line:
            reconstructed_lines.append(
                _finalize_line(current_line, page)
            )

    return reconstructed_lines


def _finalize_line(words: List[Dict], page: int) -> Dict:
    words.sort(key=lambda w: w["x"])
    raw_text = " ".join(w["text"] for w in words)
    clean_text = deduplicate_line_text(raw_text)

    avg_y = sum(w["y"] for w in words) // len(words)

    return {
        "page": page,
        "y": avg_y,
        "text": clean_text
    }

def deduplicate_line_text(text: str) -> str:
    tokens = text.split()
    if not tokens:
        return text

    cleaned = [tokens[0]]

    for token in tokens[1:]:
        if token != cleaned[-1]:
            cleaned.append(token)

    return " ".join(cleaned)

