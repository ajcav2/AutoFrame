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

access_token = InstaKeys.accessToken
client_secret = InstaKeys.clientSecret
api = InstagramAPI(access_token=access_token, client_secret=client_secret)
flickr = FlickrAPI(FlickrKeys.clientID, FlickrKeys.clientSecret, format='parsed-json')
extras = 'url_c'

def downloadInsta(hashtag, user=""):
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
                    urllib.urlretrieve(pictureObj['images']['standard_resolution']['url'],"/home/pi/Documents/AutoFrame/Instagram/"+fname+".jpg")
                    
    # Convert all images to .gif
    filelist = [ f for f in os.listdir("/home/pi/Documents/AutoFrame/Instagram/") if f.endswith(".jpg") ]
    for f in filelist:
        img = Image.open("/home/pi/Documents/AutoFrame/Instagram/"+f)
        s = "/home/pi/Documents/AutoFrame/Instagram/"+f
        img.save(s[:-4],'gif')

    # Delete old jpegs
    filelist = [ f for f in os.listdir("/home/pi/Documents/AutoFrame/Instagram/") if f.endswith(".jpg") ]
    for f in filelist:
        print("Removing " + f)
        os.remove("/home/pi/Documents/AutoFrame/Instagram/"+f)
    return


def downloadFlickr(term):
    
    # Delete all photos in Flickr folder
    filelist = [ f for f in os.listdir("/home/pi/Documents/AutoFrame/Flickr/") if f.endswith(".gif") ]
    for f in filelist:
        print("Removing " + f)
        os.remove("/home/pi/Documents/AutoFrame/Flickr/"+f)

    # Create a unique filename for each photo
    count = 0

    # Call Flickr API and parse JSON
    results = flickr.photos.search(text=term, per_page=50, extras=extras, sort="relevance")
    for photo in results['photos']['photo']:
        try:
            url = photo['url_c']
        except KeyError as e:
            print ("[Flickr] Key error.")
            continue
        # Save photos
        urllib.urlretrieve(url,"/home/pi/Documents/AutoFrame/Flickr/"+str(count)+".jpg")
        count += 1

    # Convert all images to .gif
    filelist = [ f for f in os.listdir("/home/pi/Documents/AutoFrame/Flickr/") if f.endswith(".jpg") ]
    for f in filelist:
        img = Image.open("/home/pi/Documents/AutoFrame/Flickr/"+f)
        try:
            img = resizeimage.resize_height(img, 800)
        except:
            pass
        s = "/home/pi/Documents/AutoFrame/Flickr/"+f
        img.save(s[:-4],'gif')

    # Delete old jpegs
    filelist = [ f for f in os.listdir("/home/pi/Documents/AutoFrame/Flickr/") if f.endswith(".jpg") ]
    for f in filelist:
        print("Removing " + f)
        os.remove("/home/pi/Documents/AutoFrame/Flickr/"+f)
    return

if __name__ == "__main__":
    downloadInsta("anything")
    downloadFlickr("ocean")
