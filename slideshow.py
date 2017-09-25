
''' tk_image_slideshow3.py
create a Tkinter image repeating slide show
tested with Python27/33  by  vegaseat  03dec2013
'''
import os
import io 
from itertools import cycle
from PIL import Image
try:
    # Python2
    import Tkinter as tk
except ImportError:
    # Python3
    import tkinter as tk

def photo_image(self, jpg_filename):
    with io.open(jpg_filename, 'rb') as ifh:
        pil_image = Image.open(ifh)
        return ImageTk.PhotoImage(pil_image)
class App(tk.Tk):
    '''Tk window/label adjusts to size of image'''
    def __init__(self, image_files, x, y, delay):
        # the root will be self
        tk.Tk.__init__(self)
        # set x, y position only
        self.geometry("{0}x{1}+0+0".format(self.winfo_screenwidth(), self.winfo_screenheight()))
        self.state('iconic')
        
        self.configure(background='black')
        self.delay = delay
        self.bind("<Escape>", lambda e: self.quit())
        self.focus_force()
        self.after(5000, lambda: self.focus_force())
        self.wm_attributes("-topmost" , -1)
        self.focus_set()
        # allows repeat cycling through the pictures
        # store as (img_object, img_name) tuple
        self.pictures = cycle((tk.PhotoImage(file=image), image)
                              for image in image_files)
        self.picture_display = tk.Label(self)
        self.picture_display.pack()
    def show_slides(self):
        '''cycle through the images and show them'''
        # next works with Python26 or higher
        img_object, img_name = next(self.pictures)
        self.picture_display.config(image=img_object)
        # shows the image filename, but could be expanded
        # to show an associated description of the image
        self.title(img_name)
        self.after(self.delay, self.show_slides)
    def run(self):
        self.mainloop()
        self.after(5000, lambda: self.focus_force())
    def toggle_geom(self,event):
        geom=self.master.winfo_geometry()
        print(geom,self._geom)
        self.master.geometry(self._geom)
        self._geom=geom
# set milliseconds time between slides
delay = 3500
# get a series of gif images you have in the working folder
# or use full path, or set directory to where the images are
filelist = [ f for f in os.listdir("/home/pi/Documents/AutoFrame/Flickr/") ]
image_files = []
for f in filelist:
    image_files.append("/home/pi/Documents/AutoFrame/Flickr/"+f)
# upper left corner coordinates of app window
x = 100
y = 50
app = App(image_files, x, y, delay)
app.show_slides()
app.run()
