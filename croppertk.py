#!/usr/bin/env python
'''
photo_spliter.py - Provides a simple method to split a single image containing
multiple images into individual files.

Created by Greg Lavino
03.16.2010


Note the following packages are required:
 python-tk
 python-imaging
 python-imaging-tk
'''

from PIL import Image, ImageTk
try:
    # for Python2
    import Tkinter as tk
except ImportError:
    # for Python3
    import tkinter as tk
import tkFileDialog
import sys
import os

PROGNAME = 'Cropper-Tk'
VERSION = '0.20180524'

thumbsize = 1024,1024
thumboffset = 16

class CreateToolTip(object):
    """
    create a tooltip for a given widget
    """
    def __init__(self, widget, text='widget info'):
        self.waittime = 500     #miliseconds
        self.wraplength = 180   #pixels
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # creates a toplevel window
        self.tw = tk.Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='left',
                       background="#ffffff", relief='solid', borderwidth=1,
                       wraplength = self.wraplength)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw= None
        if tw:
            tw.destroy()

class Application(tk.Frame):
    def __init__(self, master=None, filename=None):

        tk.Frame.__init__(self, master)
        self.grid()
        self.createWidgets()
        self.croprect_start = None
        self.croprect_end = None
        self.crop_count = 0
        self.canvas_rects = []
        self.crop_rects = []
        self.current_rect = None
        self.zoommode = False
        self.w = 1
        self.h = 1
        self.x0 = 0
        self.y0 = 0
        self.n = 0

        if not(filename):
            filenames = tkFileDialog.askopenfilenames(master=self,
                          defaultextension='.ppm', multiple=1, parent=self,
                          filetypes=(
                              (('Image Files'),
                               '.ppm .PPM .jpg .JPG .jpeg .JPEG .png .PNG .tif .TIF .tiff .TIFF'),
                              (('PPM Image Files'),
                               '.ppm .PPM'),
                              (('JPEG Image Files'),
                               '.jpg .JPG .jpeg .JPEG'),
                              (('PNG Image Files'),
                               '.png .PNG'),
                              (('TIFF Image Files'),
                               '.tif .TIF .tiff .TIFF'),
                              (('All files'), '*'),
                          ),
                          title=('Select images to crop'))
            if filenames:
                filename = filenames[0]

        if filename:
            self.filename = filename
            self.loadimage()

    def createWidgets(self):
        self.canvas = tk.Canvas(
            self, height=1, width=1, relief=tk.SUNKEN)
        self.canvas.bind('<Button-1>', self.canvas_mouse1_callback)
        self.canvas.bind('<ButtonRelease-1>', self.canvas_mouseup1_callback)
        self.canvas.bind('<B1-Motion>', self.canvas_mouseb1move_callback)

        self.resetButton = tk.Button(self, text='Reset',
                                          activebackground='#F00', command=self.reset)
        self.resetButton_ttp = CreateToolTip(self.resetButton, "Reset all rectangles")

        self.undoButton = tk.Button(self, text='Undo',
                                         activebackground='#FF0', command=self.undo_last)
        self.undoButton_ttp = CreateToolTip(self.undoButton, "Undo last rectangle")

        self.zoomButton = tk.Checkbutton(self, text='Zoom',
                                              command=self.zoom_mode)
        self.zoomButton_ttp = CreateToolTip(self.zoomButton, "On/Off Zoom mode")

        self.unzoomButton = tk.Button(self, text='<-|->',
                                           activebackground='#00F', command=self.unzoom_image)
        self.unzoomButton_ttp = CreateToolTip(self.unzoomButton, "Unzoom, view all image")

        self.plusButton = tk.Button(self, text='+', command=self.plus_box)
        self.plusButton_ttp = CreateToolTip(self.plusButton, "Plus box, extent rectangle")

        self.goButton = tk.Button(self, text='Crops',
                                       activebackground='#0F0', command=self.start_cropping)
        self.goButton_ttp = CreateToolTip(self.goButton, "Go, begin cropping")

        self.quitButton = tk.Button(self, text='Quit',
                                         activebackground='#F00', command=self.quit)
        self.quitButton_ttp = CreateToolTip(self.quitButton, "Exit")

        self.canvas.grid(row=0, columnspan=7)
        self.resetButton.grid(row=1, column=0)
        self.undoButton.grid(row=1, column=1)
        self.zoomButton.grid(row=1, column=2)
        self.unzoomButton.grid(row=1, column=3)
        self.plusButton.grid(row=1, column=4)
        self.goButton.grid(row=1, column=5)
        self.quitButton.grid(row=1, column=6)

    def canvas_mouse1_callback(self, event):
        self.croprect_start = (event.x, event.y)

    def canvas_mouseb1move_callback(self, event):
        if self.current_rect:
            self.canvas.delete(self.current_rect)
        x1 = self.croprect_start[0]
        y1 = self.croprect_start[1]
        x2 = event.x
        y2 = event.y
        bbox = (x1, y1, x2, y2)
        cr = self.canvas.create_rectangle(bbox)
        self.current_rect = cr

    def canvas_mouseup1_callback(self, event):
        self.croprect_end = (event.x, event.y)
        self.set_crop_area()
        self.canvas.delete(self.current_rect)
        self.current_rect = None

    def set_crop_area(self):
        r = Rect(self.croprect_start, self.croprect_end)

        # adjust dimensions
        r.clip_to(self.image_thumb_rect)

        # ignore rects smaller than this size
        if min(r.h, r.w) < 10:
            return

        ra = r
        ra = ra.scale_rect(self.scale)
        ra = ra.move_rect(self.x0, self.y0)
        ra = ra.valid_rect(self.w, self.h)
        if self.zoommode:
            self.canvas.delete(tk.ALL)
            self.x0 = ra.left
            self.y0 = ra.top
            za = (ra.left, ra.top, ra.right, ra.bottom)
            self.image_thumb = self.image.crop(za)
            self.image_thumb.thumbnail(thumbsize, Image.ANTIALIAS)
            self.image_thumb_rect = Rect(self.image_thumb.size)
            self.displayimage()
            x_scale = float(ra.w) / self.image_thumb_rect.w
            y_scale = float(ra.h) / self.image_thumb_rect.h
            self.scale = (x_scale, y_scale)
            self.redraw_rect()
            self.zoommode = False
            self.zoomButton.deselect()
        else:
            self.drawrect(r)
            self.crop_rects.append(ra)
            self.n = self.n + 1

    def zoom_ignore_dead_space(self):
        gray_color = [125, 125, 125]
        self.zoommode = True
        import numpy as np
        data = np.asarray(self.image.getdata()).reshape((self.w, self.h, 3))

        start_row = 0
        start_col = 0
        end_row = 0
        end_col = 0

        # count up and find first non-gray occurence of a pixel row
        for row in range(0, self.h):
            if np.any(data[row, :, :] != gray_color):
                start_row = row
                break
        # count down and find first non-gray occurence of a pixel row
        for row in range(self.h - 1, 0, -1):
            if np.any(data[row, :, :] != gray_color):
                end_row = row
                break
        # count right and find first non-gray occurence of a pixel col
        for col in range(0, self.w):
            if np.any(data[:, col, :] != gray_color):
                start_col = col
                break
        # count left and find first non-gray occurence of a pixel col
        for col in range(self.w - 1, 0, -1):
            if np.any(data[:, col, :] != gray_color):
                end_col = col
                break

        self.croprect_start = [start_row, start_col]
        self.croprect_end = [end_row, end_col]
        self.set_crop_area()

    def zoom_mode(self):
        if self.zoommode:
            self.zoommode = False
        else:
            self.zoommode = True

    def unzoom_image(self):
        self.canvas.delete(tk.ALL)
        self.zoommode = False
        self.zoomButton.deselect()
        self.x0 = 0
        self.y0 = 0
        self.image_thumb = self.image.copy()
        self.image_thumb.thumbnail(thumbsize, Image.ANTIALIAS)
        self.image_thumb_rect = Rect(self.image_thumb.size)
        self.displayimage()
        x_scale = float(self.image_rect.w) / self.image_thumb_rect.w
        y_scale = float(self.image_rect.h) / self.image_thumb_rect.h
        self.scale = (x_scale, y_scale)
        self.redraw_rect()

    def plus_box(self):
        if self.n > 1:
            self.canvas.delete(tk.ALL)
            if self.crop_rects:
                ra = self.crop_rects[self.n - 1]
                self.crop_rects.pop()
                self.n = self.n - 1
                ra0 = self.crop_rects[self.n - 1]
                ra0 = ra0.plus_rect(ra)
                self.crop_rects[self.n - 1] = ra0
                self.displayimage()
                self.redraw_rect()
                self.zoommode = False
                self.zoomButton.deselect()

    def redraw_rect(self):
        for croparea in self.crop_rects:
            self.drawrect(croparea.rescale_rect(self.scale, self.x0, self.y0))

    def undo_last(self):
        if self.canvas_rects:
            r = self.canvas_rects.pop()
            self.canvas.delete(r)

        if self.crop_rects:
            self.crop_rects.pop()

    def drawrect(self, rect):
        bbox = (rect.left, rect.top, rect.right, rect.bottom)
        cr = self.canvas.create_rectangle(
            bbox, activefill='', fill='red', stipple='gray25')
        self.canvas_rects.append(cr)

    def displayimage(self):
        self.photoimage = ImageTk.PhotoImage(self.image_thumb)
        w, h = self.image_thumb.size
        self.canvas.configure(
            width=(w + 2 * thumboffset),
            height=(h + 2 * thumboffset))

        self.canvas.create_image(
            thumboffset,
            thumboffset,
            anchor=tk.NW,
            image=self.photoimage)

    def reset(self):
        self.canvas.delete(tk.ALL)
        self.zoommode = False
        self.zoomButton.deselect()
        self.canvas_rects = []
        self.crop_rects = []

        self.displayimage()

    def loadimage(self):

        self.image = Image.open(self.filename)
        #print self.image.size
        self.image_rect = Rect(self.image.size)
        self.w = self.image_rect.w
        self.h = self.image_rect.h

        self.image_thumb = self.image.copy()
        self.image_thumb.thumbnail(thumbsize, Image.ANTIALIAS)

        self.image_thumb_rect = Rect(self.image_thumb.size)

        self.displayimage()
        x_scale = float(self.image_rect.w) / self.image_thumb_rect.w
        y_scale = float(self.image_rect.h) / self.image_thumb_rect.h
        self.scale = (x_scale, y_scale)

        # force rotation for correct coordinates
        #self.image = self.image.rotate(90)

        # we will zoom in to cut out dead area.
        self.zoom_ignore_dead_space()


    def newfilename(self, filenum):
        f, e = os.path.splitext(self.filename)
        return '%s__crop__%s%s' % (f, filenum, e)

    def start_cropping(self):
        cropcount = 0
        coord_list = []
        for croparea in self.crop_rects:
            cropcount += 1
            #print croparea
            coord_list.append(self.crop(croparea))
        print(str(coord_list).replace(" ",""))
        self.quit()

    def croparea_to_xiaomi_coords(self, croparea):
        ca = map(int, (croparea.left / float(self.w) * 51000,
                       (1 - (croparea.bottom / float(self.h))) * 51000,
                       croparea.right / float(self.w) * 51000,
                       (1 - (croparea.top / float(self.h))) * 51000,
                       ))
        return ca

    def crop(self, croparea):
        #ca = (croparea.left, croparea.top, croparea.right, croparea.bottom)
        ca = self.croparea_to_xiaomi_coords(croparea)
        return ca


class Rect(object):
    def __init__(self, *args):
        self.set_points(*args)

    def set_points(self, *args):
        if len(args) == 2:
            pt1 = args[0]
            pt2 = args[1]
        elif len(args) == 1:
            pt1 = (0, 0)
            pt2 = args[0]
        elif len(args) == 0:
            pt1 = (0, 0)
            pt2 = (0, 0)

        x1, y1 = pt1
        x2, y2 = pt2

        self.left = min(x1, x2)
        self.top = min(y1, y2)
        self.right = max(x1, x2)
        self.bottom = max(y1, y2)

        self._update_dims()

    def clip_to(self, containing_rect):
        cr = containing_rect
        self.top = max(self.top, cr.top + thumboffset)
        self.bottom = min(self.bottom, cr.bottom + thumboffset)
        self.left = max(self.left, cr.left + thumboffset)
        self.right = min(self.right, cr.right + thumboffset)
        self._update_dims()

    def _update_dims(self):
        """added to provide w and h dimensions."""

        self.w = self.right - self.left
        self.h = self.bottom - self.top

    def scale_rect(self, scale):
        x_scale = scale[0]
        y_scale = scale[1]

        r = Rect()
        r.top = int((self.top - thumboffset) * y_scale)
        r.bottom = int((self.bottom - thumboffset) * y_scale)
        r.right = int((self.right - thumboffset) * x_scale)
        r.left = int((self.left - thumboffset) * x_scale)
        r._update_dims()

        return r

    def move_rect(self, x0, y0):
        r = Rect()
        r.top = int(self.top + y0)
        r.bottom = int(self.bottom + y0)
        r.right = int(self.right + x0)
        r.left = int(self.left + x0)
        r._update_dims()

        return r

    def rescale_rect(self, scale, x0, y0):
        x_scale = scale[0]
        y_scale = scale[1]

        r = Rect()
        r.top = int((self.top - y0) / y_scale + thumboffset)
        r.bottom = int((self.bottom - y0) / y_scale + thumboffset)
        r.right = int((self.right - x0) / x_scale + thumboffset)
        r.left = int((self.left - x0) / x_scale + thumboffset)
        r._update_dims()

        return r

    def plus_rect(self, r0):
        r = Rect()
        r.top = min(self.top, r0.top)
        r.bottom = max(self.bottom, r0.bottom)
        r.right = max(self.right, r0.right)
        r.left = min(self.left, r0.left)
        r._update_dims()

        return r

    def valid_rect(self, w, h):
        r = Rect()
        r.top = self.top
        if r.top < 0:
            r.top = 0
        if r.top > h - 1:
            r.top = h - 1
        r.bottom = self.bottom
        if r.bottom < 1:
            r.bottom = 1
        if r.bottom > h:
            r.bottom = h
        r.right = self.right
        if r.right < 1:
            r.right = 1
        if r.right > w:
            r.right = w
        r.left = self.left
        if r.left < 0:
            r.left = 0
        if r.left > w - 1:
            r.left = w - 1
        r._update_dims()

        return r

    def __repr__(self):
        return '(%d,%d)-(%d,%d)' % (self.left,
                                    self.top, self.right, self.bottom)


def main():
    filename = None
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    # else:
        # print "Need a filename"
        # return

    app = Application(filename=filename)
    app.master.title(PROGNAME)
    app.mainloop()


if __name__ == '__main__':
    main()
