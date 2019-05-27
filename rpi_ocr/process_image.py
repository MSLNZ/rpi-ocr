import cv2
import numpy as np
from PIL import Image

# Functions used to process the image, will have options for both PIL and cv2


def apply_threshold(im, threshold):
    """Apply a threshold to the image.

    Parameters
    ----------
    im : np.ndarray or Image.Image
        The image object.
    threshold : int
        The threshold to apply.

    Returns
    -------
    np.ndarray or Image.Image
        The image object after applying the threshold.

    """
    if isinstance(im, np.ndarray):
        lower_lim = int(255 * threshold / 100)
        ret, edited_im = cv2.threshold(im, lower_lim, 255, cv2.THRESH_BINARY)
        return edited_im

    elif isinstance(im, Image.Image):
        # Do threshold using PIL
        pass


def apply_erosion(im, erosion):
    """Apply erosion to the image.

        Parameters
        ----------
        im : np.ndarray or Image.Image
            The image object.
        erosion : int
            The number of times to apply erosion.

        Returns
        -------
        np.ndarray or Image.Image
            The image object after applying erosion.

    """
    if isinstance(im, np.ndarray):
        kernel = np.ones((5, 5), np.uint8)
        edited_im = cv2.erode(im, kernel, iterations=erosion)
        return edited_im

    elif isinstance(im, Image.Image):
        # Do erosion using PIL
        pass


def apply_dilation(im, dilation):
    """Apply dilation to the image.

        Parameters
        ----------
        im : np.ndarray or Image.Image
            The image object.
        dilation : int
            The number of times to apply dilation.

        Returns
        -------
        np.ndarray or Image.Image
            The image object after applying dilation.

    """
    if isinstance(im, np.ndarray):
        kernel = np.ones((5, 5), np.uint8)
        edited_im = cv2.dilate(im, kernel, iterations=dilation)
        return edited_im

    elif isinstance(im, Image.Image):
        # Do dilation using PIL
        pass
