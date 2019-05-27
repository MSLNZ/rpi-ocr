import os
import matplotlib.pyplot as plt

from rpi_ocr.utils import to_base64, to_cv2, to_pil, save_as_jpeg


path = os.path.join(os.path.dirname(__file__), 'images', 'colour')
img_path = os.path.join(os.path.dirname(__file__), 'images')
png_path = os.path.join(os.path.dirname(__file__), 'images', 'ssocr_website.png')
jpg_path = os.path.join(os.path.dirname(__file__), 'images', 'tesseract_eng_numbers.jpg')
bmp_path = os.path.join(os.path.dirname(__file__), 'images', 'colour.bmp')

# for extn in ('.jpeg', '.png', '.bmp'):
#     filename = path + extn
#     print(filename)
#
#     img = to_base64(filename)
#
#     new_file = path + extn + 'new.jeg'
#
#     save_as_jpeg(img, new_file)

png = to_pil(png_path)
save_as_jpeg(png, os.path.join(img_path, 'png.jpeg'))
png_new = to_pil(os.path.join(img_path, 'png.jpeg'))
print(list(png_new.getdata())[20005:20100])
print(list(png.getdata())[20005:20100])

jpg = to_pil(jpg_path)
save_as_jpeg(jpg, os.path.join(img_path, 'jpg.jpeg'))
jpg_new = to_pil(os.path.join(img_path, 'jpg.jpeg'))
print(list(jpg_new.getdata())[10000])
print(list(jpg.getdata())[10000])

bmp = to_pil(bmp_path)
save_as_jpeg(bmp, os.path.join(img_path, 'bmp.jpeg'))
bmp_new = to_pil(os.path.join(img_path, 'bmp.jpeg'))
print(list(bmp_new.getdata())[10000])
print(list(bmp.getdata())[10000])


def show_plots():

    path = os.path.join(os.path.dirname(__file__), 'images', 'colour')
    for extn in ('.jpeg', '.png', '.bmp'):
        filename = path + extn
        print(filename)

        plt.imshow(to_pil(filename))
        plt.title(os.path.basename(filename) + ' -> pil')
        plt.show()

        plt.imshow(to_pil(to_base64(filename)))
        plt.title(os.path.basename(filename) + ' -> base64 -> pil')
        plt.show()

        plt.imshow(to_pil(to_cv2(filename)))
        plt.title(os.path.basename(filename) + ' -> cv2 -> pil')
        plt.show()

        plt.imshow(to_pil(to_cv2(to_base64(filename))))
        plt.title(os.path.basename(filename) + ' -> base64 -> cv2 -> pil')
        plt.show()

        plt.imshow(to_pil(to_base64(to_cv2(filename))))
        plt.title(os.path.basename(filename) + ' -> cv2 -> base64 -> pil')
        plt.show()

        plt.imshow(to_cv2(filename))
        plt.title(os.path.basename(filename) + ' -> cv2')
        plt.show()

        plt.imshow(to_cv2(to_base64(filename)))
        plt.title(os.path.basename(filename) + ' -> base64 -> cv2')
        plt.show()

        plt.imshow(to_cv2(to_pil(filename)))
        plt.title(os.path.basename(filename) + ' -> pil -> cv2')
        plt.show()

        plt.imshow(to_cv2(to_pil(to_base64(filename))))
        plt.title(os.path.basename(filename) + ' -> base64 -> pil -> cv2')
        plt.show()

        plt.imshow(to_cv2(to_base64(to_pil(filename))))
        plt.title(os.path.basename(filename) + ' -> pil -> base64 -> cv2')
        plt.show()

# show_plots()
