Trained languages that can be used for `Tesseract <https://github.com/tesseract-ocr/tesseract>`_.

The file must be copied to the ``tessdata`` directory before you can use the language.

To use one of these languages, you specify the name as the ``lang`` parameter, e.g.,

.. code-block:: python

   from ocr import tesseract
   text, image = tesseract('my-digits.png', lang='letsgodigital')

* `letsgodigital <https://github.com/arturaugusto/display_ocr>`_ - seven-segment font
