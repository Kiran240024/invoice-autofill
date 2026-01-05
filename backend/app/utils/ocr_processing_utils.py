import cv2
import numpy as np

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

