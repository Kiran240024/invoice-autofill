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
        page_words.sort(key=lambda w: (w["y"]))

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
                current_line.sort(key=lambda w: w["x"])
                current_line=deduplicate_words(current_line)
                #columns=split_into_columns(current_line)
                avg_y = sum(w["y"] for w in current_line) // len(current_line)
                

                reconstructed_lines.append({
                    "page": page,
                    "y": avg_y,
                    "words":[{"text":w["text"], "role":w.get("role")} for w in current_line],
                })

                current_line = [word]
                current_y = word["y"]

        # Add last line
        if current_line:
            current_line.sort(key=lambda w: w["x"])
            current_line=deduplicate_words(current_line)
            #columns=split_into_columns(current_line)
            
            avg_y = sum(w["y"] for w in current_line) // len(current_line)
                

            reconstructed_lines.append({
                    "page": page,
                    "y": avg_y,
                    "words":[{"text":w["text"], "role":w.get("role")} for w in current_line],
                })
    role_spans=[]
    for line in reconstructed_lines:
        spans=split_line_into_role_spans(line)
        role_spans.extend(spans)
    return role_spans

def deduplicate_words(words: List[Dict],x_tol=2) -> List[Dict]:
    #remove duplicate words based on x coordinate proximity
    # words is assumed to be sorted by x
    unique_words=[]
    seen=set()
    for w in words:
        key=(round(w["x"]/x_tol),w["text"].strip().lower())
        if key not in seen:
            unique_words.append(w)
            seen.add(key)
    return unique_words

from typing import List, Dict

def split_line_into_role_spans(line: Dict) -> List[Dict]:
    """
    Split a reconstructed line into role-homogeneous spans.

    Input:
      line = {
        "page": int,
        "y": int,
        "words": [{text, role, x, y, ...}]
      }

    Output:
      [
        { page, y, role, text, words[] },
        ...
      ]
    """

    spans = []
    current_words = []
    current_role = None

    for w in line["words"]:
        role = w.get("role", "UNKNOWN")

        if current_role is None:
            current_role = role
            current_words = [w]
            continue

        if role == current_role:
            current_words.append(w)
        else:
            spans.append({
                "page": line["page"],
                "y": line["y"],
                "role": current_role,
                "text": " ".join(x["text"] for x in current_words),
                "words": current_words
            })
            current_role = role
            current_words = [w]

    if current_words:
        spans.append({
            "page": line["page"],
            "y": line["y"],
            "role": current_role,
            "text": " ".join(x["text"] for x in current_words),
            "words": current_words
        })

    return spans
