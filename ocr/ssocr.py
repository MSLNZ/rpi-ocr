"""
The `ssocr <https://www.unix-ag.uni-kl.de/~auerswal/ssocr/>`_ algorithm.
"""
import os
import sys
import subprocess
from enum import Enum

from .utils import (
    to_bytes,
    logger,
)

ssocr_exe = 'ssocr'


class SSOCREnum(Enum):
    """Base enum class."""

    @classmethod
    def get_value(cls, name):
        if isinstance(name, str):
            try:
                return cls[name.upper()].value
            except KeyError:
                raise ValueError('{} does not contain a {!r} member'.format(cls, name)) from None
        elif isinstance(name, Enum):
            return name.value
        else:
            raise TypeError('invalid type {} for SSOCREnum'.format(type(name)))


class Luminance(SSOCREnum):
    """Options for computing the luminance."""
    REC601 = 'rec601'    #: use gamma corrected RGB values according to ITU-R Rec. BT.601-4
    REC709 = 'rec709'    #: use linear RGB values according to ITU-R Rec. BT.709
    LINEAR = 'linear'    #: use (R+G+B)/3 as done by cvtool 0.0.1
    MINIMUM = 'minimum'  #: use min(R,G,B) as done by GNU Ocrad 0.14
    MAXIMUM = 'maximum'  #: use max(R,G,B)
    RED = 'red'          #: use R value
    GREEN = 'green'      #: use G value
    BLUE = 'blue'        #: use B value


class Charset(SSOCREnum):
    """Options for the character set."""
    DIGITS = 'digits'    #: 0123456789
    DECIMAL = 'decimal'  #: 0123456789.-
    HEX = 'hex'          #: 0123456789.-abcdef
    FULL = 'full'        #: 0123456789.-abcdefhlnprtu


class Colour(SSOCREnum):
    """Options for the foreground/background colour."""
    BLACK = 'black'
    WHITE = 'white'


def set_ssocr_path(path):
    """Set the path to the ``ssocr`` executable.

    Parameters
    ----------
    path : :class:`str`
        The full path to the ``ssocr`` executable or a top-level
        directory that contains the executable.
    """
    global ssocr_exe

    # allows for specifying '~' in the path and de-references symbolic links
    path = os.path.realpath(os.path.expanduser(path))
    filename = 'ssocr' + '.exe' if sys.platform == 'win32' else ''

    if os.path.isfile(path):
        if os.path.basename(path) != filename:
            raise FileNotFoundError('Invalid ssocr path')
    elif os.path.isdir(path):
        found_it = False
        for root, _, _ in os.walk(path):
            url = os.path.join(root, filename)
            if os.path.isfile(url):
                path = url
                found_it = True
                break
        if not found_it:
            raise FileNotFoundError('Cannot find the ssocr executable')
    else:
        raise FileNotFoundError('The path is not a valid file or directory')

    logger.debug('set ssocr executable to {!r}'.format(path))
    ssocr_exe = path


def version(include_copyright=False):
    """Get the version number of ssocr.

    Equivalent of running: ``ssocr --version``

    Parameters
    ----------
    include_copyright : :class:`bool`, optional
        Whether to include the copyright information.

    Returns
    -------
    :class:`str`
        The version number (and possibly copyright information).
    """
    out = _run([ssocr_exe, '--version'])
    if include_copyright:
        return out
    return out.splitlines()[0].split()[-1]


# Options:
#   -h, --help               print this message
#   -v, --verbose            talk about program execution
#   -V, --version            print version information
#   -t, --threshold=THRESH   use THRESH (in percent) to distinguish black from white
#   -a, --absolute-threshold don't adjust threshold to image
#   -T, --iter-threshold     use iterative thresholding method
#   -n, --number-pixels=#    number of pixels needed to recognize a segment
#   -i, --ignore-pixels=#    number of pixels ignored when searching digit boundaries
#   -d, --number-digits=#    number of digits in image (-1 for auto)
#   -r, --one-ratio=#        height/width ratio to recognize a 'one'
#   -m, --minus-ratio=#      width/height ratio to recognize a minus sign
#   -o, --output-image=FILE  write processed image to FILE
#   -O, --output-format=FMT  use output format FMT (Imlib2 formats)
#   -p, --process-only       do image processing only, no OCR
#   -D, --debug-image[=FILE] write a debug image to FILE or testbild.png
#   -P, --debug-output       print debug information
#   -f, --foreground=COLOR   set foreground color (black or white)
#   -b, --background=COLOR   set background color (black or white)
#   -I, --print-info         print image dimensions and used lum values
#   -g, --adjust-gray        use T1 and T2 from gray_stretch as percentages of used values
#   -l, --luminance=KEYWORD  compute luminance using formula KEYWORD use -l help for list of KEYWORDS
#   -S, --ascii-art-segments print recognized segments a ASCII art
#   -X, --print-as-hex       change output format to hexadecimal
#   -C, --omit-decimal-point omit decimal points from output
#   -c, --charset=KEYWORD    select recognized characters use -c help for list of KEYWORDS


def ssocr(image, *,
          threshold=50.0,
          absolute_threshold=False,
          iter_threshold=False,
          needed_pixels=1,
          ignored_pixels=0,
          num_digits=-1,
          one_ratio=3,
          minus_ratio=2,
          debug=False,
          foreground=Colour.BLACK,
          background=Colour.WHITE,
          luminance=Luminance.REC709,
          as_hex=False,
          omit_decimal_point=False,
          charset=Charset.FULL,
          ):
    """Apply the `ssocr <https://www.unix-ag.uni-kl.de/~auerswal/ssocr/>`_ algorithm.

    None of the image-process commands in ssocr are currently supported.
    Use the image-processing functions in :mod:`.utils` to modify the image.

    Parameters
    ----------
    image
        The image to apply the ssocr algorithm to. See :func:`.to_bytes` for
        valid image data types.
    threshold : :class:`float`, optional
        The threshold (in percent) to distinguish black from white.
    absolute_threshold : :class:`bool`, optional
        If enabled then don't adjust threshold to image.
    iter_threshold : :class:`bool`, optional
        Whether to use iterative thresholding method.
    needed_pixels : :class:`int`, optional
        Number of pixels needed to recognize a segment.
    ignored_pixels : :class:`int`, optional
        Number of pixels ignored when searching digit boundaries.
    num_digits : :class:`int`, optional
        Number of digits in image (-1 for auto).
    one_ratio : :class:`int`, optional
        Minimum height/width ratio to recognize the number `one`.
    minus_ratio : :class:`int`, optional
        Minimum width/height ratio to recognize a minus sign.
    debug : :class:`bool`, optional
        Whether to include the debug messages in the output text.
    foreground : :class:`str` or :class:`Color`, optional
        Set foreground color (black or white).
    background : :class:`str` or :class:`Color`, optional
        Set background color (black or white).
    luminance : :class:`str` or :class:`Luminance`, optional
        Compute luminance using this formula.
    as_hex : :class:`bool`, optional
        Whether to change the output text to hexadecimal.
    omit_decimal_point : :class:`bool`, optional
        Whether to omit decimal points from the output text.
    charset : :class:`str` or :class:`Charset`, optional
        The character set to use.

    Returns
    -------
    :class:`str`
        The text.
    """
    command = [
        ssocr_exe,
        '-t{}'.format(threshold),
        '-n{}'.format(needed_pixels),
        '-i{}'.format(ignored_pixels),
        '-d{}'.format(num_digits),
        '-r{}'.format(one_ratio),
        '-m{}'.format(minus_ratio),
        '-f{}'.format(Colour.get_value(foreground)),
        '-b{}'.format(Colour.get_value(background)),
        '-l{}'.format(Luminance.get_value(luminance)),
        '-c{}'.format(Charset.get_value(charset)),
    ]

    if absolute_threshold:
        command.append('-a')

    if iter_threshold:
        command.append('-T')

    if debug:
        command.append('-P')

    if as_hex:
        command.append('-X')

    if omit_decimal_point:
        command.append('-C')

    if isinstance(image, str) and os.path.isfile(image):
        command.append(image)
        data = None
    else:
        # load the image from stdin
        command.append('-')
        data = to_bytes(image)

    return _run(command, stdin=data, debug=debug)


def _run(command, stdin=None, debug=False):
    # runs the ssocr command
    logger.debug('ssocr command: {}'.format(' '.join(command)))
    try:
        p = subprocess.run(command, input=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        raise FileNotFoundError(
            'You must set the location to the ssocr executable.\n'
            'Call ocr.set_ssocr_path() or add the directory of the ssocr executable to PATH'
        ) from None

    if debug:
        return p.stderr.decode() + p.stdout.decode()

    if p.stderr:
        # ssocr uses imlib2 which can write warnings to stderr if a TIFF image is loaded, e.g.
        #  TIFFReadDirectory: Warning, Unknown field with tag 20624 (0x5090) encountered.
        # We can ignore these TIFF warnings.
        for line in p.stderr.splitlines():
            if not line.startswith(b'TIFFReadDirectory: Warning'):
                raise RuntimeError(p.stderr.decode())

    return p.stdout.rstrip().decode('ascii')
