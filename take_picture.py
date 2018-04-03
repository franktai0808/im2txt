#!/usr/bin/env python

import serial
import picamera
import sys, os, subprocess
import requests, json
import time, datetime

from run_inference import generateCaption

SERVER_URL = 'http://ec2-18-191-1-128.us-east-2.compute.amazonaws.com/images'
UPLOAD_IMAGE_URI = 'images'
PHOTOFORMAT = 'jpeg'

def takePicture(filename):
  with picamera.PiCamera() as camera:
    camera.resolution = (1920, 1080)
    camera.capture(filename + '.' + PHOTOFORMAT, format=PHOTOFORMAT)
    print("Photo captured and saved ...")
    return filename + '.' + PHOTOFORMAT

def timestamp():
  tstring = datetime.datetime.now()
  print("Filename generated ...")
  return tstring.strftime("%Y%m%d_%H%M%S")

def deleteFile(filename):
  os.system("rm " + filename)
  print("File: " + filename + " deleted ...")

def uploadPicture(filename, caption, coords):
  filePath = './' + filename + '.' + PHOTOFORMAT

  print("Uploading " + filename + " to AWS Server")
  
  print("coords: "+coords)
  headers = {'caption': caption, 'coordinates': coords} 
  files = {'file': open(filePath, 'rb')}
  url = SERVER_URL

  #try: 
  r = requests.post(url, files=files, headers=headers)
  print(r.status_code)
  print(r.text)
  #r.raise_for_status()
  #except Exception as e:
  #  print("ERROR: File upload failed")
  #  print(e.args[0])
  #else:
  #  print("File upload succeeded!")

def getLocation():
  send_url = 'http://freegeoip.net/json'
  r = requests.get(send_url)
  j = json.loads(r.text)
  lat = j['latitude']
  lon = j['longitude']
  return str(lat) + ',' + str(lon)

def main():
  serialData = serial.Serial('/dev/ttyAMA0', 115200, timeout=1)
  print("start serial conn")  
  while True: 
    input = serialData.read()
    print("waiting for take photo message")
    while(input != b'P'):
      input = serialData.read()
      print(str(input))
    serialData.write(b'p')
    print("photo message has been received")


    print("waiting for GPS message")
    input = serialData.read()
    while(input != b'G'):
      input = serialData.read()
  
    serialData.write(b'g')
    print("GPS message has been received")    

    while(serialData.in_waiting == 0):
      continue; 
    latitude = ""
    input = serialData.read()
    
    while(input != b'\n'):
      print(input)
      if input != b'\x00':
        latitude = latitude + input.decode("utf-8")
      input = serialData.read()  

    print("latitude: "+latitude) 
    while(serialData.in_waiting == 0):
      continue;
    longitude = ""
    input = serialData.read()
    
    while(input != b'\n'):
      if input != b'\x00':
        longitude = longitude + input.decode("utf-8")
      input = serialData.read()

    print("longitude: "+longitude)
    #Generate filename from current time
    filename = timestamp()

    #Capture photo
    file = takePicture(filename)

    #Generate Caption
    #caption = generateCaption("./" + filename + "." + PHOTOFORMAT)
    #coords = getLocation()
    coords = latitude + ',' + longitude 

    #subprocess.call("../speech.sh "+caption, shell=True)
    #print("Generated caption for photo is: " + caption)
    #Upload photo
    uploadPicture(filename, "this is a caption", coords)

    #Delete local file
    deleteFile(filename + '.' + PHOTOFORMAT)

    print("Done\n\n")

if __name__ == '__main__':
  main() 
