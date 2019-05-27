try:
    import ssocr
    import subprocess
except ImportError:
    pass  # on windows

from .utils import to_base64


def run_ssocr(image):
    image = to_base64(image)
    path = '-'
    p = subprocess.run(["ssocr", "-T", path], input=image, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.stdout.rstrip().decode(), image
