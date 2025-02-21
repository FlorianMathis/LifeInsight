# Import required packages

import time
import socket
import base64
import requests
import os
import openai
import keyboard  # using module keyboard
from gtts import gTTS
import os
from playsound import playsound
from datetime import datetime
import numpy as np 
import cv2 
import speech_recognition as sr
import time 
import RPi.GPIO as GPIO 
import pygame
from picamera2 import Picamera2, Preview 
from libcamera import controls 
picam = Picamera2()

GPIO.setwarnings(False) 
pygame.init()
config = picam.create_preview_configuration(main={"size": (820, 640)})
picam.configure(config)
picam.set_controls({"AfMode": 2, "AfTrigger": 0})

timestamp = ""
current_dir = "path/to/dir"

def audioFeedback():
    file_path = current_dir + 'ping.mp3'
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play() 
audioFeedback() 

def assistOpenAI(image, text):
	api_key = "OPENAI_key"
	headers = {
	  "Content-Type": "application/json",
	  "Authorization": f"Bearer {api_key}"
	}

	payload = {
	  "model": "gpt-4-vision-preview",
	  "messages": [
      
	    {
	      "role": "system",
	      "content": [
		{
		  "type": "text",
		  "text": "Assisting a blind person in their everyday life. Responses should be brief and outline the requested information immediately within one sentence."
		}]},
      
	    {
	      "role": "user",
	      "content": [
		{
		  "type": "text",
		  "text": text
		},
		{
		  "type": "image_url",
		  "image_url": {
		    "url": f"data:image/jpeg;base64,{image}"
		  }
		}
	      ]
	    }
	  ],
	  "max_tokens": 300
	}

	response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
	return response.json()['choices'][0]['message']['content']

def takePicture():
   picam.start()
   global timestamp
   timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
   picam.capture_file(current_dir + timestamp+"_image.jpg") 
   return current_dir + timestamp+"_image.jpg"
def recognize_from_microphone():
   r = sr.Recognizer("de-DE")
   #use own API key from google speech
   speech = sr.Microphone()
   with speech as source:    
   	audio = r.adjust_for_ambient_noise(source)    
   	audio = r.listen(source)	
   	try: 
	   	recog = r.recognize(audio)
   	except Exception as e:
	   	recog = "Try again."
   return recog

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

def store_prompt(text):
   timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
   file = open(current_dir + "prompts.txt","a")
   file.write(timestamp+";"+text+"\n")
   file.close() 
   
def store_AIoutput(text):
   timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
   file = open(current_dir + "AIoutput.txt","a")
   file.write(timestamp+";"+text+"\n")
   file.close() 

def text_to_speech(text):
    # Initialize gTTS with the text to convert
    speech = gTTS(text, lang="de")

    # Save the audio file to a temporary file
    speech_file = current_dir + 'speech.mp3'
    speech.save(speech_file)

    # Play the audio file

    file_path = current_dir + 'speech.mp3'
    #playsound(file_path)
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()

 
def obfuscateImage(img):    
    # Converting BGR image into a RGB image 
    #image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)   
    # plotting the original image 
    face_cascade = cv2.CascadeClassifier(current_dir+'haarcascade_frontalface_alt.xml')
    faces = face_cascade.detectMultiScale(img, 1.1, 5)

    for (x, y, w, h) in faces:
        roi = img[y:y+h, x:x+w]
        # apply gaussian blur to face rectangle
        roi = cv2.GaussianBlur(roi, (17, 17), 30)
        # add blurred face on original image to get final image
        img[y:y+roi.shape[0], x:x+roi.shape[1]] = roi
    cv2.imwrite(current_dir + timestamp+"_image.jpg",img)

print("reading")

def button_callback(channel):
            source = takePicture()
            audioFeedback() 
            obfuscateImage(cv2.imread(source))  
            print("timestamp" +source)
            base64_image = encode_image(source)
            text = recognize_from_microphone() #pre-defined by user
            if text != "Try again.":
            	audioFeedback()
            	store_prompt(text)
            	output = assistOpenAI(base64_image, text)
            	store_AIoutput(output)
            	print("working")
            	text_to_speech(output)
            else: text_to_speech(text)

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

GPIO.add_event_detect(10,GPIO.RISING,callback=button_callback)

message = input ("Press key to quit.")
GPIO.cleanup()

