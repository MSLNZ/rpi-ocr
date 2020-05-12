The contents of this directory allow executing `ssocr <https://www.unix-ag.uni-kl.de/~auerswal/ssocr/>`_
from a Windows command prompt. If you want to apply the ``ssocr`` algorithm on a Windows computer,
instead of having the Raspberry Pi perform it for you, then copy the ``ssocr-win64`` directory to your
hard drive and let Python know where the ``ssocr-win64`` directory is located,

.. code-block:: python

   import ocr
   ocr.set_ssocr_path('C:\\where\\you\\copied\\ssocr-win64')
   ocr.ssocr('six_digits.png', iter_threshold=True)

Alternatively, add ``C:\\where\\you\\copied\\ssocr-win64`` to your ``PATH`` environment variable.

The ``ssocr.exe`` file (located in the ``ssocr-win64\bin`` directory) was built using
`Cygwin <https://www.cygwin.com/>`_. It was compiled from the
`master <https://github.com/auerswal/ssocr>`_ branch
(commit: e65a5c87c8b90aa410fe2dc499c71f0cb3f8b0c1)

The following should be followed if one wanted to recompile ``ssocr`` to update
``ssocr-win64\bin\ssocr.exe`` so that an alternate version of ``ssocr`` is used.

1. Download ``setup-x86_64.exe`` from `here <https://cygwin.com/install.html>`_.

2. If you have admin rights then double-click on the executable to run the setup.
   If you do not have admin rights then open up a Command Prompt, go to the directory
   where ``setup-x86_64.exe`` is located and then run ``setup-x86_64.exe --no-admin``

3. Accept the default settings and pick a ``Download Site`` that is close to you.

4. Install these additional packages: ``make``, ``gcc-g++``, ``libImlib2-devel``

5. Open the ``Cygwin64 Terminal`` and execute the following

  .. code-block:: console

     git clone https://github.com/auerswal/ssocr.git
     cd ssocr
     make

6. Close the ``Cygwin64 Terminal``.

7. In Windows Explorer, copy ``C:\cygwin64\home\<USERNAME>\ssocr\ssocr.exe`` to
   ``..\ssocr-win64\bin`` and replace the existing file.

8. You *might* have to also update some of the DLL's in the ``ssocr-win64\bin`` folder.
   This will depend on the versions of ``Cygwin`` and ``Imlib2`` that were used to compile
   ``ssocr``.
