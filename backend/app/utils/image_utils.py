import cv2
import numpy as np
from pathlib import Path

def image_preprocessing(image_path, preprocessed_path:Path):
    img=cv2.imread(str(image_path))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    median_filtered = cv2.medianBlur(gray, 3) 
    binary = cv2.adaptiveThreshold(
    median_filtered, 255,
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY, 25, 2
    )
    kernel_bg = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    clean_bg = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_bg)
    deskewed=deskew(clean_bg)
    rescaled = rescale_for_ocr(deskewed)
    preprocessed_path.parent.mkdir(parents=True, exist_ok=True)
    success=cv2.imwrite(str(preprocessed_path), rescaled)
    return success

def deskew(binary_img):
    # binary_img: black text (0), white background (255)

    # Invert so text becomes white (required for angle detection)
    inv = cv2.bitwise_not(binary_img)

    # Get coordinates of white pixels (text)
    coords = np.column_stack(np.where(inv > 0))

    # If no text detected, return original
    if coords.size == 0:
        return binary_img

    # Compute angle of minimum-area bounding box
    angle = cv2.minAreaRect(coords)[-1]

    # Angle correction logic
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    # Rotate image
    (h, w) = binary_img.shape
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    deskewed = cv2.warpAffine(
        binary_img, M, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )

    return deskewed
import cv2


def rescale_for_ocr(image):
    """
    Rescale deskewed image using OpenCV for OCR.
    """

    height, width = image.shape[:2]

    # OCR sweet spot
    TARGET_WIDTH = 3000
    MIN_WIDTH = 2000
    MAX_WIDTH = 4000

    # Upscale
    if width < MIN_WIDTH:
        scale = TARGET_WIDTH / width
        new_size = (int(width * scale), int(height * scale))
        image = cv2.resize(image, new_size, interpolation=cv2.INTER_CUBIC)

    # Downscale
    elif width > MAX_WIDTH:
        scale = MAX_WIDTH / width
        new_size = (int(width * scale), int(height * scale))
        image = cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)

    return image
