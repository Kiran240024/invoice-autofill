import cv2
import numpy as np
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def image_preprocessing(image_path, preprocessed_path: Path) -> bool:
    """
    Preprocess an invoice image through multiple stages.
    
    Args:
        image_path: Path to the input image
        preprocessed_path: Path to save the preprocessed image
        
    Returns:
        bool: True if preprocessing succeeded, False otherwise
        
    Raises:
        ValueError: If critical preprocessing steps fail
    """
    try:
        # Load image
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"Failed to read image: {image_path}")
        
        logger.debug(f"Loaded image: {image_path}, shape: {img.shape}")
        
        # Critical step: Grayscale conversion
        img = _apply_critical_step(img, to_grayscale, "Grayscale conversion")
        
        # Optional steps with graceful degradation
        img = _apply_optional_step(img, _deskew_image, "Deskewing")
        img = _apply_optional_step(img, _resize_image, "Image resizing")
        img = _apply_optional_step(img, _remove_noise, "Noise removal")
        img = _apply_optional_step(img, _normalize_background, "Background normalization")
        img = _apply_optional_step(img, _enhance_contrast, "Contrast enhancement")
        img = _apply_optional_step(img, _binarize_image, "Binarization")
        
        # Critical step: Save image
        if not cv2.imwrite(str(preprocessed_path), img):
            raise ValueError(f"Failed to write image to {preprocessed_path}")
        
        logger.info(f"Successfully preprocessed image: {preprocessed_path}")
        return True
        
    except ValueError as e:
        logger.error(f"Critical error in image preprocessing: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in image preprocessing: {e}", exc_info=True)
        raise ValueError(f"Image preprocessing failed: {e}")


def _apply_critical_step(img, step_func, step_name: str):
    """Apply a critical preprocessing step that must succeed."""
    try:
        return step_func(img)
    except Exception as e:
        raise ValueError(f"{step_name} failed: {e}")


def _apply_optional_step(img, step_func, step_name: str):
    """Apply an optional preprocessing step with graceful failure."""
    try:
        return step_func(img)
    except Exception as e:
        logger.warning(f"{step_name} failed (continuing): {e}")
        return img


def _resize_image(img):
    """Handle image resizing based on dimensions."""
    h, w = img.shape[:2]

    if h < 1500:
        img = cv2.resize(img, None, fx=2, fy=2)
        h, w = img.shape[:2]
        logger.debug(f"Upscaled image to {w}x{h}")

    if h > 4500:
        scale = 3500 / h
        img = cv2.resize(
            img,
            (int(w * scale), int(h * scale)),
            interpolation=cv2.INTER_AREA
        )
        logger.debug(f"Downscaled image to {img.shape[1]}x{img.shape[0]}")
    
    return img


def _deskew_image(img):
    """Deskew the image if skew angle is significant."""
    angle = find_skew_angle(img)
    if abs(angle) > 1.0:
        img = deskew(img, angle)
        logger.debug(f"Deskewed image by {angle:.2f} degrees")
    return img


def _remove_noise(img):
    """Apply noise removal if image variance is high."""
    if img.std() > 60:
        img = cv2.GaussianBlur(img, (3, 3), 0)
        logger.debug("Applied Gaussian blur for noise removal")
    return img


def _normalize_background(img):
    """Normalize uneven background."""
    if background_is_uneven(img):
        img = normalize_background(img)
        logger.debug("Normalized background")
    return img


def _enhance_contrast(img):
    """Enhance contrast if it's too low."""
    if contrast_is_low(img):
        img = enhance_contrast(img)
        logger.debug("Enhanced contrast")
    return img


def _binarize_image(img):
    """Apply binarization as last resort for very low contrast."""
    if needs_binarisation(img):
        img = binarise(img)
        logger.debug("Applied adaptive binarization")
    return img


def find_skew_angle(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    _, bw = cv2.threshold(
        gray, 0, 255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    coords = np.column_stack(np.where(bw > 0))
    if coords.shape[0]<50:
        return 0.0  # Not enough text to determine skew
    angle = cv2.minAreaRect(coords)[-1]

    if angle < -45:
        angle = 90 + angle

    return angle


def deskew(image, angle):
    h, w = image.shape[:2]
    center = (w // 2, h // 2)

    M = cv2.getRotationMatrix2D(center, -angle, 1.0)

    return cv2.warpAffine(
        image,
        M,
        (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )


def to_grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def background_is_uneven(gray, threshold=15):
    blurred = cv2.GaussianBlur(gray, (31, 31), 0)
    diff = cv2.absdiff(gray, blurred)
    return diff.mean() > threshold


def normalize_background(gray):
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
    bg = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)
    norm = cv2.subtract(gray, bg)
    return cv2.normalize(norm, None, 0, 255, cv2.NORM_MINMAX)


def contrast_is_low(gray, threshold=120):
    return (gray.max() - gray.min()) < threshold


def enhance_contrast(gray):
    clahe = cv2.createCLAHE(2.0, (8, 8))
    return clahe.apply(gray)


def needs_binarisation(gray):
    return (gray.max() - gray.min()) < 100


def binarise(gray):
    return cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31, 10
    )
