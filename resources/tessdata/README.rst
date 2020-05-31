Trained models that can be used for `Tesseract <https://github.com/tesseract-ocr/tesseract>`_.

These files must be copied to the ``tessdata`` directory before they can be used.

To use one of these languages, you specify the name of the language as the value to the
``language`` keyword argument, e.g.,

.. code-block:: python

   from ocr import tesseract
   text, image = tesseract('my-digits.png', language='7seg')

* `7seg <https://raw.githubusercontent.com/Shreeshrii/tessdata_ssd/master/7seg.traineddata>`_
* `letsgodigital <https://raw.githubusercontent.com/arturaugusto/display_ocr/master/letsgodigital/letsgodigital.traineddata>`_
* `ssd <https://raw.githubusercontent.com/Shreeshrii/tessdata_ssd/master/ssd.traineddata>`_
* `ssd_alphanum_plus <https://raw.githubusercontent.com/Shreeshrii/tessdata_ssd/master/ssd_alphanum_plus.traineddata>`_
* `ssd_int <https://raw.githubusercontent.com/Shreeshrii/tessdata_ssd/master/ssd_int.traineddata>`_
* `ssd_plus <https://raw.githubusercontent.com/Shreeshrii/tessdata_ssd/master/ssd_plus.traineddata>`_
