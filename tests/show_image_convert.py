"""
This script is used as a visualization test to check that converting
between cv2, PIL and base64 does not change the image.

matplotlib and pyqtgraph draw the image differently but we
only care that the image does not look different after converting it.
"""
import os

from ocr.utils import to_base64, to_cv2, to_pil


def show_matplotlib_plots():

    path = os.path.join(os.path.dirname(__file__), 'images', 'colour')
    for extn in ('.jpeg', '.png', '.bmp'):
        filename = path + extn
        basename = os.path.basename(filename)
        print(filename)

        plt.imshow(to_pil(filename))
        plt.title(basename + ' -> pil')
        plt.show()

        plt.imshow(to_pil(to_base64(filename)))
        plt.title(basename + ' -> base64 -> pil')
        plt.show()

        plt.imshow(to_pil(to_cv2(filename)))
        plt.title(basename + ' -> cv2 -> pil')
        plt.show()

        plt.imshow(to_pil(to_cv2(to_base64(filename))))
        plt.title(basename + ' -> base64 -> cv2 -> pil')
        plt.show()

        plt.imshow(to_pil(to_base64(to_cv2(filename))))
        plt.title(basename + ' -> cv2 -> base64 -> pil')
        plt.show()

        plt.imshow(to_cv2(filename))
        plt.title(basename + ' -> cv2')
        plt.show()

        plt.imshow(to_cv2(to_base64(filename)))
        plt.title(basename + ' -> base64 -> cv2')
        plt.show()

        plt.imshow(to_cv2(to_pil(filename)))
        plt.title(basename + ' -> pil -> cv2')
        plt.show()

        plt.imshow(to_cv2(to_pil(to_base64(filename))))
        plt.title(basename + ' -> base64 -> pil -> cv2')
        plt.show()

        plt.imshow(to_cv2(to_base64(to_pil(filename))))
        plt.title(basename + ' -> pil -> base64 -> cv2')
        plt.show()


def show_pyqtgraph_plots():

    # pyqtgraph requires a numpy array as the image data

    app = pg.mkQApp()

    path = os.path.join(os.path.dirname(__file__), 'images', 'colour')
    for extn in ('.jpeg', '.png', '.bmp'):
        filename = path + extn
        basename = os.path.basename(filename)
        print(filename)

        pg.image(to_cv2(filename), title=basename + ' -> cv2')
        app.exec()

        pg.image(to_cv2(to_base64(filename)), title=basename + ' -> base64 -> cv2')
        app.exec()

        pg.image(to_cv2(to_pil(filename)), title=basename + ' -> pil -> cv2')
        app.exec()

        pg.image(to_cv2(to_cv2(filename)), title=basename + ' -> cv2 -> cv2')
        app.exec()

        pg.image(to_cv2(to_pil(to_base64(filename))), title=basename + ' -> base64 -> pil -> cv2')
        app.exec()

        pg.image(to_cv2(to_base64(to_pil(filename))), title=basename + ' -> pil -> base64 -> cv2')
        app.exec()


if __name__ == '__main__':
    import pyqtgraph as pg
    import matplotlib.pyplot as plt

    show_matplotlib_plots()
    show_pyqtgraph_plots()
