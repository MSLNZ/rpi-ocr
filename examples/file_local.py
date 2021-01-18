"""
Apply OCR on the local computer with an image file.
"""
import ocr

# let Python know where the ssocr executable is located
ocr.set_ssocr_path('../resources/ssocr-win64')

# the image to apply OCR to
path = '../tests/images/six_digits.png'

# the OCR settings
algorithm = 'ssocr'
tasks = [('greyscale',), ('threshold', 214)]

# apply OCR
text, image = ocr.apply(path, algorithm=algorithm, tasks=tasks)

# save the image with the OCR text included
ocr.save('six_digits_text.png', image, text=text)
