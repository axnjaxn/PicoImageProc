PicoImageProc
=============

A set of image processing functions for converting images for use in the PICO-8

Dependencies
------------

The tools are written in Python 3, with opencv/numpy.

I recommend running `pip install opencv-python numpy` if you need to install them.


Usage
-----

```
python convert.py [options] imagefile.ext output.p8
--use-palette palette-filename: only use the palette listed in the file
                                (format is text, one color index per line)
--default-palette: use the normal palette and disable secret colors
--preview: preview results (3x scale, press any key to terminate)

Note that the software does not need to resize unless the image is bigger than 128x128.
```