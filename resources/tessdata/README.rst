Trained models that can be used for `Tesseract <https://github.com/tesseract-ocr/tesseract>`_.

These files must be copied to the ``tessdata`` directory before they can be used.

To use one of these languages, you specify the name of the language as the value to the
``language`` keyword argument, e.g.,

.. code-block:: python

   from ocr import tesseract
   text, image = tesseract('my-digits.png', language='letsgodigital')

* `letsgodigital <https://github.com/arturaugusto/display_ocr>`_ - seven-segment font
