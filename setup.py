import sys
import platform
from distutils.cmd import Command
from setuptools import setup


class ApiDocs(Command):
    """
    A custom command that calls sphinx-apidoc
    see: https://www.sphinx-doc.org/en/latest/man/sphinx-apidoc.html
    """
    description = 'builds the api documentation using sphinx-apidoc'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        command = [
            None,  # in Sphinx < 1.7.0 the first command-line argument was parsed, in 1.7.0 it became argv[1:]
            '--force',  # overwrite existing files
            '--module-first',  # put module documentation before submodule documentation
            '--separate',  # put documentation for each module on its own page
            '-o', './docs/_autosummary',  # where to save the output files
            'msl',  # the path to the Python package to document
        ]

        import sphinx
        if sphinx.version_info < (1, 7):
            from sphinx.apidoc import main
        else:
            from sphinx.ext.apidoc import main  # Sphinx also changed the location of apidoc.main
            command.pop(0)

        main(command)
        sys.exit(0)


class BuildDocs(Command):
    """
    A custom command that calls sphinx-build
    see: https://www.sphinx-doc.org/en/latest/man/sphinx-build.html
    """
    description = 'builds the documentation using sphinx-build'
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import sphinx

        command = [
            None,  # in Sphinx < 1.7.0 the first command-line argument was parsed, in 1.7.0 it became argv[1:]
            '-b', 'html',  # the builder to use, e.g., create a HTML version of the documentation
            '-a',  # generate output for all files
            '-E',  # ignore cached files, forces to re-read all source files from disk
            'docs',  # the source directory where the documentation files are located
            './docs/_build/html',  # where to save the output files
        ]

        if sphinx.version_info < (1, 7):
            from sphinx import build_main
        else:
            from sphinx.cmd.build import build_main  # Sphinx also changed the location of build_main
            command.pop(0)

        build_main(command)
        sys.exit(0)


install_requires = [
    'msl-network>=0.5',
    'msl-qt @ git+https://github.com/MSLNZ/msl-qt.git',
    'pillow',
    'opencv-python!=4.1.1.26',  # there's an issue with opencv-python 4.1.1.26 on the RPi
    'pyqtgraph>=0.11.0rc0',
]

on_rpi = platform.machine().startswith('arm')
if on_rpi:
    install_requires.extend(['picamera', 'pytesseract', 'msl-package-manager'])
else:
    # the rpi-setup.sh script installs PySide2 in the virtual environment
    install_requires.append('PySide2')

needs_sphinx = {'doc', 'docs', 'apidoc', 'apidocs', 'build_sphinx'}.intersection(sys.argv)
sphinx = ['sphinx', 'sphinx_rtd_theme'] + install_requires if needs_sphinx else []

testing = {'test', 'tests', 'pytest'}.intersection(sys.argv)
pytest_runner = ['pytest-runner'] if testing else []
tests_require = ['pytest', 'pytest-cov', 'matplotlib', 'pytesseract']

setup(
    name='ocr',
    version='0.1.0.dev0',
    author='Measurement Standards Laboratory of New Zealand',
    author_email='info@measurement.govt.nz',
    url='https://github.com/MSLNZ/rpi-ocr',
    description='Optical Character Recognition with a Raspberry Pi',
    long_description=open('README.rst').read().strip(),
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    setup_requires=sphinx + pytest_runner,
    tests_require=tests_require,
    install_requires=install_requires,
    packages=['ocr'],
    entry_points={
        'console_scripts': [
            'ocr = ocr:start_service_on_rpi',
        ],
    },
)
