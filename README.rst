What is it
==========

This originally comes from Greg Lavino, and then "Image Processing for Electronic Publications" and was intended to crop images quickly.

Now it can be used to generate map coordinate rectangles for use with the zoned cleaning function for Xiaomi roborock v1/v2 robots. Simply run the program on a navmap PPM file and draw the zones that you want coordinates for. Then copy the output into your software of choice (hassio, miiocli, etc)


Old Readme
==========

This is a copy of Greg Lavino's awesome `photo_splitter.py`, with some
minor adjustments by myself.

Greg published his original code in a `ubunutuforums.org thread
<http://ubuntuforums.org/showthread.php?t=1429439&p=8975597#post8975597>`_.

`photo_splitter.py` is very useful if you need to crop a large amount
of images very quickly.  Simply select the areas in the image that you
want to crop, click "Go" and photo_splitter will create one image file
for each crop area for you, in the same folder as the original image.

Here's a screenshot from the `StackOverflow question
<http://askubuntu.com/questions/31250/fast-image-cropping>`_ which
features `photo_splitter.py` as the solution:

.. image:: http://i.stack.imgur.com/CS2io.png

CropperTktoPDF

.. image:: https://raw.githubusercontent.com/zvezdochiot/python-cropper-tk/master/croppertktopdf-sample.jpg

Installation
============

Before you can run `croppertk.py`, you'll need to install these
libraries::

  sudo apt-get install python-tk python-pil python-imaging-tk python-reportlab

Run
===

An example::

  ./croppertk.py navmap.ppm

or::

  ./croppertk.py

Make a for loop to process a bunch of images::

  for img in ~/images/*; do ./croppertk.py $img; done
