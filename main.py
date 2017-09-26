import time
import datetime
import InstaKeys
import urllib2, json
import urllib
from instagram.client import InstagramAPI
from pathlib import Path
from flickrapi import FlickrAPI
import FlickrKeys
import os
from Tkinter import *
from PIL import Image
from resizeimage import resizeimage
from flask import Flask
from flask_ask import Ask, statement, convert_errors, question
import logging
import threading
import thread
import io 
from itertools import cycle
try:
    # Python2
    import Tkinter as tk
except ImportError:
    # Python3
    import tkinter as tk

global slide

app = Flask(__name__)
ask = Ask(app, '/')

access_token = InstaKeys.accessToken
client_secret = InstaKeys.clientSecret
api = InstagramAPI(access_token=access_token, client_secret=client_secret)
flickr = FlickrAPI(FlickrKeys.clientID, FlickrKeys.clientSecret, format='parsed-json')
extras = 'url_c'

logging.getLogger("flask_ask").setLevel(logging.DEBUG)

@ask.launch
def begin():
    return question("What would you like to see photos of")

@ask.intent('getPhotoSubject', mapping={'term': 'photoSubject'})
def respondToUser(term):

    # Spawn process on new thread
    download_thread = threading.Thread(target=downloadAndConvert, args=[term])
    download_thread.daemon = True
    download_thread.start()
    
    return statement('Showing photos of {}'.format(term))

    
def downloadAndConvert(term):
    if "kids" not in term and "family" not in term:
        method = "Flickr"
        
        # Delete all photos in Flickr folder
        filelist = [ f for f in os.listdir("/home/pi/Documents/AutoFrame/Flickr/") ]
        for f in filelist:
            print("Removing " + f)
            os.remove("/home/pi/Documents/AutoFrame/Flickr/"+f)
            
        # Create a unique filename for each photo
        count = 0

        # Call Flickr API and parse JSON
        results = flickr.photos.search(text=term, per_page=10, extras=extras, sort="relevance")
        for photo in results['photos']['photo']:
            try:
                url = photo['url_c']
            except KeyError as e:
                print ("[Flickr] Key error.")
                continue
            # Save photos
            urllib.urlretrieve(url,"/home/pi/Documents/AutoFrame/Flickr/"+str(count)+".jpg")
            count += 1

    else:
        method = "Instagram"
        
        # Get user ID's
        megan = api.user_search('megan_cav')[0].id
        sarah = api.user_search('sarahcav456')[0].id
        alex = api.user_search('ajcav2')[0].id

        # Create arrays to hold user info
        users = [alex, megan, sarah]
        accessTokens = [InstaKeys.accessToken, InstaKeys.accessToken_MEGAN, InstaKeys.accessToken_SARAH]
        tag = "cav_ep"
        i = 0

        # Loop through each user
        for user in users:
            
            # Call instagram API
            urlInstagram = "https://api.instagram.com/v1/users/"+user+"/media/recent?access_token="+accessTokens[i]
            i += 1
            response = urllib.urlopen(urlInstagram)
            data = json.loads(response.read())

            # If we find the tag in a photo, download it
            for pictureObj in data['data']:
                if tag in pictureObj['tags']:
                    fname = pictureObj['caption']['text']
                    if len(fname) > 20:
                        fname = fname[0:20]
                    if len(fname) == 0:
                        fname = datetime.date.today().strftime("%B %d, %Y")
                    test = Path("/home/pi/Documents/AutoFrame/Instagram/"+fname+".jpg")
                    if test.is_file():
                        continue
                    else:
                        print("Downloading " + fname + "...")
                        urllib.urlretrieve(pictureObj['images']['standard_resolution']['url'],"/home/pi/Documents/AutoFrame/Instagram/"+fname+".jpg")

    # Convert all images to .gif
    filelist = [ f for f in os.listdir("/home/pi/Documents/AutoFrame/"+method+"/") if f.endswith(".jpg") ]
    for f in filelist:
        img = Image.open("/home/pi/Documents/AutoFrame/"+method+"/"+f)
        try:
            img = resizeimage.resize_height(img, 800)
        except:
            pass
        s = "/home/pi/Documents/AutoFrame/"+method+"/"+f
        img.save(s[:-4],'gif')

    # Delete old jpegs
    filelist = [ f for f in os.listdir("/home/pi/Documents/AutoFrame/"+method+"/") if f.endswith(".jpg") ]
    for f in filelist:
        print("Removing " + f)
        os.remove("/home/pi/Documents/AutoFrame/"+method+"/"+f)

    # Start slideshow
    print("Starting slideshow...")
    startSlideshow(method)
    return

def photo_image(self, jpg_filename):
    with io.open(jpg_filename, 'rb') as ifh:
        pil_image = Image.open(ifh)
        return ImageTk.PhotoImage(pil_image)

class App(tk.Tk): # was tk.Tk
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
        #self.after(5000, lambda: self.focus_force())
        #self.wm_attributes("-topmost" , -1)
        #self.focus_set()
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
    def toggle_geom(self,event):
        geom=self.master.winfo_geometry()
        print(geom,self._geom)
        self.master.geometry(self._geom)
        self._geom=geom

def startSlideshow(source):
    # set milliseconds time between slides
    delay = 3500
    # get a series of gif images you have in the working folder
    # or use full path, or set directory to where the images are
    filelist = [ f for f in os.listdir("/home/pi/Documents/AutoFrame/"+source+"/") ]
    image_files = []
    for f in filelist:
        image_files.append("/home/pi/Documents/AutoFrame/"+source+"/"+f)
    # upper left corner coordinates of app window
    x = 100
    y = 50
    slide = App(image_files, x, y, delay)
    slide.show_slides()
    slide.run()
    
 
if __name__ == "__main__":
    port = 5000
    app.run(host='0.0.0.0', port=port)
    
