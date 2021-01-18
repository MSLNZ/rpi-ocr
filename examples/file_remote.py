"""
Apply OCR on a Raspberry Pi with an image file.
"""
import ocr

# the image to apply OCR to
path = '../tests/images/six_digits.png'

# the OCR settings
algorithm = 'ssocr'
tasks = [('greyscale',), ('threshold', 214)]

# the information required to connect to a Raspberry Pi
# optional: if you specify the password then you won't be prompted for it
host = '192.168.1.69'
rpi_password = ''
assert_hostname = False

# start the OCR service on a Raspberry Pi
service = ocr.service(host=host, rpi_password=rpi_password, assert_hostname=assert_hostname)

# apply OCR on the Raspberry Pi
text, image = service.apply(path, algorithm=algorithm, tasks=tasks)

# save the image with the OCR text included
ocr.save('six_digits_text.png', image, text=text)

# disconnect from (and shut down) the OCR service on the Raspberry Pi
service.disconnect()
