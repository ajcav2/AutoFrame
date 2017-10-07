import time
import datetime
import InstaKeys
import urllib2, json
import urllib
from instagram.client import InstagramAPI
from pathlib import Path
import os
from flask import Flask
from flask_ask import Ask, statement, convert_errors, question
import logging
import threading
import thread
import io 
import subprocess
import signal
import unsplashKeys


# This holds the process for the slideshow
global task

# Initialize multipleDoS so parents don't spam Alexa
# when it's taking too long.
global multipleDoS
multipleDoS = False

# Start flask
app = Flask(__name__)
ask = Ask(app, '/')

# Initialize Instagram and Flickr API's
access_token = InstaKeys.accessToken
client_secret = InstaKeys.clientSecret
api = InstagramAPI(access_token=access_token, client_secret=client_secret)
#flickr = FlickrAPI(FlickrKeys.clientID, FlickrKeys.clientSecret, format='parsed-json')
#extras = 'url_c'

logging.getLogger("flask_ask").setLevel(logging.DEBUG)

# Initialize intent
@ask.launch
def begin():
    global multipleDoS
    if threading.activeCount() > 1 and multipleDoS == False:
        multipleDoS = True
        return statement('Please wait for previous request to finalize.')
    elif threading.activeCount() > 1 and multipleDoS == True:
        return statement('Please wait for the previous request to finalize. If its taking too long maybe dad should reset the internet.')
    else:
        multipleDoS = False
    return question("What would you like to see photos of?")
        

# Get search term
@ask.intent('getPhotoSubject', mapping={'term': 'photoSubject'})
def respondToUser(term):

    # Try to stop any currently running slideshows
    try:
        global task
        os.killpg(os.getpgid(task.pid), signal.SIGTERM)
        print("Slideshow succesfully terminated.")
    except Exception as e:
        print("No task to terminate.") 

    # Spawn process on new thread so that the user doesn't have to wait long
    # for a response
    download_thread = threading.Thread(target=downloadPhotos, args=[term])
    download_thread.daemon = True
    download_thread.start()

    if "my kids" in term.lower() or "my family" in term.lower() or "my children" in term.lower():
        return statement('Showing photos of your family')
    else:
        return statement('Showing photos of {}. This may take some time.'.format(term))

    
def downloadPhotos(term):
    # Delete all old photos in pictures folder
    filelist = [ f for f in os.listdir("/home/pi/Documents/AutoFrame/pictures/") ]
    for f in filelist:
        print("Removing " + f)
        os.remove("/home/pi/Documents/AutoFrame/pictures/"+f)

    if "my kids" in term.lower() or "my family" in term.lower() or "my children" in term.lower():
        # Instagram
        # Get user ID's
        megan = api.user_search('megan_cav')[0].id
        sarah = api.user_search('sarahcav456')[0].id
        alex = api.user_search('ajcav2')[0].id

        # Create arrays to hold user info
        users = [alex, megan, sarah]
        accessTokens = [InstaKeys.accessToken, InstaKeys.accessToken_MEGAN, InstaKeys.accessToken_SARAH]
        tag = "cav_ep"
        i = 0
        count = 0

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
                    print("Downloading " + str(count) + ".jpg...")
                    urllib.urlretrieve(pictureObj['images']['standard_resolution']['url'],"/home/pi/Documents/AutoFrame/pictures/"+str(count)+".jpg")
                    count += 1
            
    else:
        # Unsplash
        unsplashLink = "https://api.unsplash.com/search/photos?client_id="+unsplashKeys.applicationID+"&page=1&per_page=50&query="+term
        unsplashResponse = urllib.urlopen(unsplashLink)
        unsplashJSON = json.loads(unsplashResponse.read())
        count = 0
        for link in unsplashJSON['results']:
            print("Downloading " + str(count) + ".jpg...")
            urllib.urlretrieve(link['links']['download'],"/home/pi/Documents/AutoFrame/pictures/"+str(count)+".jpg")
            count += 1
    print("Done.")
        
  ##### OLD METHOD TO DOWNLOAD FROM FLICKR #####
  #          
  #  # Create a unique filename for each photo
  #  count = 0
  #
  #  # Call Flickr API and parse JSON
  #  results = flickr.photos.search(text=term, per_page=50, extras=extras, sort="relevance")
  #  for photo in results['photos']['photo']:
  #      try:
  #          url = photo['url_c']
  #      except KeyError as e:
  #          print ("[Flickr] Key error.")
  #          continue
  #      # Save photos
  #      urllib.urlretrieve(url,"/home/pi/Documents/AutoFrame/pictures/"+str(count)+".jpg")
  #      count += 1
  #
  ##############################################

    # Create JSON for slideshow
    print("Generating JSON...")
    generateJSON(count)

    # Create a task for the slideshow                                                                       Add -f as final option for full screen
    global task
    print("Starting slideshow...")
    task = subprocess.Popen('sudo python /home/pi/pipresents/pipresents.py --home /home/pi/ --profile myMediaShow3', shell=True, preexec_fn=os.setsid)
    return

def generateJSON(highestJPEG):
    data = {}
    data.update({"issue": "1.2"})
    data["tracks"] = []

    for i in range(0,highestJPEG):
        data["tracks"].append({
        "animate-begin": "", 
       "animate-clear": "no", 
       "animate-end": "", 
       "background-colour": "", 
       "background-image": "", 
       "display-show-background": "yes", 
       "display-show-text": "yes", 
       "duration": "", 
       "image-window": "fit", 
       "links": "", 
       "location": "/home/pi/Documents/AutoFrame/pictures/"+str(i)+".jpg", 
       "plugin": "", 
       "show-control-begin": "", 
       "show-control-end": "", 
       "thumbnail": "", 
       "title": str(i)+".jpg", 
       "track-ref": "", 
       "track-text": "", 
       "track-text-colour": "", 
       "track-text-font": "", 
       "track-text-x": "0", 
       "track-text-y": "0", 
       "transition": "", 
       "type": "image"
        })

    # Write JSON to file for slideshow
    with open('/home/pi/pp_home/pp_profiles/myMediaShow3/media.json', 'w') as outfile:
        json.dump(data, outfile)
            
    return
    
 
if __name__ == "__main__":
    port = 5000
    app.run(host='0.0.0.0', port=port)
    
