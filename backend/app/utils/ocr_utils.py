import pytesseract
import pandas as pd
import cv2

def extract_bounding_boxes(image_path):
    img=cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Failed to read image: {image_path}")

    df = pytesseract.image_to_data(
        img,
        output_type=pytesseract.Output.DATAFRAME,
        config="--oem 3 --psm 6" #recommended psm for invoices
    ) # Get OCR data as a DataFrame

    # Clean DataFrame: remove empty text entries
    df = df[df["text"].notna()] 
    df = df[df["text"].str.strip() != ""]

    # Ensure confidence is numeric before filtering
    if "conf" in df.columns:
        df["conf"] = pd.to_numeric(df["conf"], errors="coerce") # Convert conf to numeric, coercing errors to NaN
        df = df[df.conf >= 40]
    
    # Convert DataFrame → structured dicts
    ocr_results = []

    for _, row in df.iterrows():
        text = str(row["text"]).strip()
        if not text:
            continue

        ocr_results.append({
            "text": text,
            "x": int(row["left"]),
            "y": int(row["top"]),
            "width": int(row["width"]),
            "height": int(row["height"]),
            "confidence": int(row["conf"])
        })

    return ocr_results

def merge_ocr_results(raw,prep):
    """
    Merges OCR results from raw and preprocessed images
    using word-level confidence and bounding box overlap.
    """
    merged = []
    used_prep_indices = set()

    # Step 1: iterate through raw OCR words
    for r in raw:
        best_match = None
        best_match_index = None
        best_iou=0.0

        for idx, p in enumerate(prep):
            if idx in used_prep_indices:
                continue
            
            #check if the boxes belong to same line as preprocessing and raw may shift y a bit
            if(abs(r["y"] - p["y"]) > max(r["height"],p["height"])):
                continue
            current_iou=iou(
                (r["x"],r["y"],r["width"],r["height"]),
                (p["x"],p["y"],p["width"],p["height"])
            )

            #word-level IoU threshold
            if current_iou >=0.15 and current_iou > best_iou:
                best_iou=current_iou
                best_match=p
                best_match_index=idx

        if best_match:
            # pick higher-confidence word
            best = r if r["confidence"] >= best_match["confidence"] else best_match
            merged.append(best)
            used_prep_indices.add(best_match_index)
        else:
            # raw-only word
            merged.append(r)

    # Step 2: add prep-only words
    for idx, p in enumerate(prep):
        if idx not in used_prep_indices:
            merged.append(p)
    #Step 3: sort merged words top-to-bottom, left-to-right
    merged.sort(key=lambda w: (w["y"], w["x"]))

    return merged

def iou(box1, box2):
    """
    box format: (x, y, w, h)
    """
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2

    xa = max(x1, x2)
    ya = max(y1, y2)
    xb = min(x1 + w1, x2 + w2)
    yb = min(y1 + h1, y2 + h2)

    inter_width = max(0, xb - xa)
    inter_height = max(0, yb - ya)
    inter_area = inter_width * inter_height

    box1_area = w1 * h1
    box2_area = w2 * h2

    union_area = box1_area + box2_area - inter_area

    if union_area == 0:
        return 0.0

    return inter_area / union_area

def score(words):
    return (
        len(words) * 1.0 +
        sum(w["confidence"] for w in words) / max(len(words), 1)
    )

