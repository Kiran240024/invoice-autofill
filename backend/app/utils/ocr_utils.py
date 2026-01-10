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
        config="--oem 3 --psm 6"
    ) # Get OCR data as a DataFrame

    df = df.dropna() # Remove rows with NaN values
    # Ensure confidence is numeric before filtering
    if "conf" in df.columns:
        df["conf"] = pd.to_numeric(df["conf"], errors="coerce") # Convert conf to numeric, coercing errors to NaN
        df = df[df.conf > 50]
    
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