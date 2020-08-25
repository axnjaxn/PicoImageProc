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
python convert.py [options] imagefile.ext [output.p8]
--use-palette palette-filename: only use the palette listed in the file
                                (format is text, one color index per line)
--default-palette: use the normal palette and disable secret colors
--ban-color index: do not allow a color index to appear in recommendations
--dither percentage: enable Floyd-Steinberg dithering (0%-100%)
--ordered-dither percentage: use ordered dithering
--brighten percentage: adjust global image brightness
--contrast percentage: adjust global image contrast
--preview: preview results (3x scale, press any key to terminate)
--export filename: export an image of the result (at PICO-8 resolution)
--slower-recommend: take dithering settings into account when recommending (slower)
```

Note that the software does not need to resize unless the image is bigger than 128x128.
