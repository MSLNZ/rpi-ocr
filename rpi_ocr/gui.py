try:
    from matplotlib.widgets import RectangleSelector
    from matplotlib.widgets import Button
    import matplotlib.pyplot as plt
    from matplotlib.widgets import Slider
    from matplotlib.widgets import RadioButtons
    import matplotlib.animation as animation
except ImportError:
    pass  # on RPi

import numpy as np
import cv2

from .process_image import (
    apply_dilation,
    apply_erosion,
    apply_threshold,
)
from .utils import (
    to_cv2,
    to_base64,
)

DEFAULT_IMAGE_FORMAT = '.jpeg'


class Gui(object):

    def __init__(self, client):
        self._client = client
        self._image = np.zeros((1, 1))
        self._image_plt = None
        self._cropped_im = np.zeros((1, 1))
        self.undo_im = np.zeros((1, 1))
        self._crop_history = []
        self._crop_index = [0]
        self.language = 'eng'
        self.ocr_params = {}

        self.fig, self.current_ax = plt.subplots()
        plt.axis('off')
        self.b_reset = Button(plt.axes([0.15, 0.2, 0.15, 0.05]), 'RESET', color='white', hovercolor='red')
        self.s_erosion = Slider(plt.axes([0.15, 0.06, 0.5, 0.03]), 'Erosion', 0, 5, valinit=0, valstep=1)
        self.s_dilation = Slider(plt.axes([0.15, 0.09, 0.5, 0.03]), 'Dilation', 0, 5, valinit=0, valstep=1)
        self.s_threshold = Slider(plt.axes([0.15, 0.12, 0.5, 0.03]), 'Threshold', 0, 100, valinit=50)
        self.choose_ocr = RadioButtons(plt.axes([0.75, 0.03, 0.2, 0.15]), ['eng', 'letsgodigital', 'ssocr'], active=0,
                                       activecolor='blue')
        self.b_test_ocr = Button(plt.axes([0.55, 0.2, 0.15, 0.05]), 'Test OCR')
        self.b_undo_process = Button(plt.axes([0.35, 0.2, 0.15, 0.05]), 'Undo')
        self.b_done = Button(plt.axes([0.75, 0.2, 0.15, 0.05]), 'Done')
        self._range_selector = RectangleSelector(self.current_ax, self.crop_event, drawtype='box', minspanx=5,
                                                 minspany=5, useblit=False, button=[1, 3], spancoords='pixels',
                                                 interactive=True)

    def set_image(self, filename=None, as_grey_scale=True):
        if filename is None:
            pass
            self._image = self._client.capture()
            self._image = to_cv2(self._image)
        else:
            self._image = to_cv2(filename)
        if as_grey_scale:
            self._image = cv2.cvtColor(self._image, cv2.COLOR_BGR2GRAY)
        length, width = self._image.shape
        self._crop_history.append((0, 0, width, length))

    def stream(self):
        animation.FuncAnimation(self.current_ax, self._client.capture(), 25, interval=50)

    def show(self):
        # Define events for button, sliders and rectangle selector
        self.b_reset.on_clicked(self.reset)
        self.s_erosion.on_changed(self.update)
        self.s_dilation.on_changed(self.update)
        self.s_threshold.on_changed(self.threshold)
        self.b_test_ocr.on_clicked(self.test_ocr)
        self.b_undo_process.on_clicked(self.undo)
        self.b_done.on_clicked(self.save_params)
        handler = KeyPressHandler(self)

        plt.connect('key_press_event', handler.toggle_selector)

        plt.subplots_adjust(bottom=0.3)

        self._image_plt = self.current_ax.imshow(self._image, cmap='Greys_r')
        plt.show()

    def crop_event(self, eclick, erelease):
        # Event when area is selected to crop
        x = int(eclick.xdata)
        y = int(eclick.ydata)
        x2 = int(erelease.xdata)
        y2 = int(erelease.ydata)

        w = x2 - x
        h = y2 - y

        if self._crop_history:
            # If the image has already been cropped, apply transform to crop cropped image
            x_old, y_old, w_old, h_old = self._crop_history[-1]
            width = self._crop_history[0][2]
            length = self._crop_history[0][3]

            x_zoom = w_old / width
            y_zoom = h_old / length
            x = x_old + round(x_zoom * x)
            y = y_old + round(y_zoom * y)
            w = (x_old + round(x_zoom * x2)) - x
            h = (y_old + round(y_zoom * y2)) - y

        # Add current X,Y,W,H to crop history
        self._crop_history.append((x, y, w, h))
        self._crop_index.append(len(self._crop_history) - 1)

        # Save cropped image
        self._cropped_im = self._image[y:y + h, x:x + w]
        self.undo_im = self._cropped_im

        # Show cropped image
        self._image_plt.set_data(self._cropped_im)
        plt.draw()

    def reset(self, val):
        """
        Resets image to the original image (undoes all cropping and editing).
        """
        self._cropped_im = self._image * 1
        self._crop_history = [self._crop_history[0]]
        self._crop_index = [0]
        self._image_plt.set_data(self._cropped_im)

    def update(self, val):
        """
        Updates the image after changing the erosion or dilation.
        """
        self.undo_im = self._cropped_im
        self._cropped_im = apply_erosion(self._cropped_im, int(self.s_erosion.val))
        self._cropped_im = apply_dilation(self._cropped_im, int(self.s_dilation.val))
        self._image_plt.set_data(self._cropped_im)

    def threshold(self, val):
        """
        Updates the image after applying threshold.
        """
        self.undo_im = self._cropped_im
        self._cropped_im = apply_threshold(self._cropped_im, self.s_threshold.val)
        self._image_plt.set_data(self._cropped_im)

    def test_ocr(self, val):
        """
        Applies OCR to the image displayed, and displays the number it reads.
        """
        self.undo_im = self._cropped_im
        number, number_im = self._client.ocr(to_base64(self._cropped_im), language=self.choose_ocr.value_selected)
        self.current_ax.set_title('Number detected: {}'.format(number))

    def undo(self, val):
        """
        Undoes the latest change to the image.
        """
        self._image_plt.set_data(self.undo_im)
        self._cropped_im = self.undo_im

    def save_params(self, val):
        """
        Saves the ocr parameters, and closes the gui.
        """
        self.ocr_params['Crop'] = self._crop_history[-1]
        self.ocr_params['Threshold'] = self.s_threshold.val
        self.ocr_params['Erosion'] = self.s_erosion.val
        self.ocr_params['Dilation'] = self.s_dilation.val
        self.ocr_params['Language'] = self.choose_ocr.value_selected
        plt.close(self.fig)


class KeyPressHandler(object):

    def __init__(self, gui):
        self._gui = gui

    def toggle_selector(self, event):
        """
        Define events to undo and redo cropping, and to move up/down/left/right a little bit
        """
        if event.key in ['ctrl+z', 'ctrl+Z']:
            # Define event to undo most recent crop
            ind = self._gui._crop_index[-1] - 1
            if ind >= 0:
                x, y, w, h = self._gui._crop_history[ind]
                self._gui._crop_index.append(ind)
                self._gui._cropped_im = self._gui._image[y:y + h, x:x + w]
                self._gui._image_plt.set_data(self._gui._cropped_im)
                plt.draw()
            elif ind == -1:
                self._gui._image_plt.set_data(self._gui._image)
                plt.draw()

        elif event.key in ['ctrl+y', 'ctrl+Y']:
            # Define event to redo crop if it was undone
            ind = self._gui._crop_index[-1] + 1
            if max(self._gui._crop_index) >= ind:
                x, y, w, h = self._gui._crop_history[ind]
                self._gui._crop_index.append(ind)
                self._gui._cropped_im = self._gui._image[y:y + h, x:x + w]
                self._gui._image_plt.set_data(self._gui._cropped_im)
                plt.draw()

        elif event.key in ['up', 'down', 'left', 'right']:
            x, y, w, h = self._gui._crop_history[self._gui._crop_index[-1]]

            if event.key == 'up':
                # Move cropped area up slightly
                y -= 1

            elif event.key == 'down':
                # Move cropped area down slightly
                y += 1

            elif event.key == 'right':
                # Move cropped area right slightly
                x += 1

            elif event.key == 'left':
                # Move cropped area left slightly
                x -= 1

            self._gui._crop_history.append((x, y, w, h))
            self._gui._crop_index.append(len(self._gui._crop_history) - 1)
            self._gui._cropped_im = self._gui._image[y:y + h, x:x + w]
            self._gui.undo_im = self._gui._cropped_im
            self._gui._image_plt.set_data(self._gui._cropped_im)
            plt.draw()
