# test_vision_api.py
from google.cloud import vision
import os

# Make sure this points to your credentials file
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:/Users/philc/Downloads/principal-bond-359020-eb7876c5bf3b.json"

# Create a simple test
client = vision.ImageAnnotatorClient()
image = vision.Image()
image.source.image_uri = "https://cloud.google.com/vision/docs/images/sign_text.png"
response = client.text_detection(image=image)
print(response.text_annotations[0].description if response.text_annotations else "No text found")