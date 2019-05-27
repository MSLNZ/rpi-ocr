try:
    import pytesseract
except ImportError:
    pass  # on Windows

from .utils import to_base64, to_pil


def run_tesseract(image, lang="eng"):
    image = to_pil(image)
    number = pytesseract.image_to_string(image, lang=lang, config='tessedit_char_whitelist=,.1234567890')
    image = to_base64(image)
    return number, image
