For this code to work fully:

1. Python and Libraries

You need Python installed (3.8+) and these libraries:

flask → For the web dashboard and routes.

opencv-python → For accessing the camera and processing video frames.

pandas → To log motion events in a CSV file.

pygame → To play the siren sound.

threading → To run the alert without blocking video feed.

datetime, os, time → Standard libraries for file handling and timing.

Install with pip:

pip install flask opencv-python pandas pygame

2. Camera

The script uses cv2.VideoCapture(0), which means it expects a webcam or camera at index 0.

If you have multiple cameras, you may need to change the index.

3. Siren Sound

You must have a file named alert_sound.mp3 in the project folder.

pygame will fail to play if this file is missing or incorrectly named.

4. CSV File

Motion events are logged in motion_events.csv.

The code will create it if missing, but the folder where the code runs must be writeable.

Make sure Python has permission to write files in this folder.

5. Screenshots Folder

Screenshots of motion events are saved in a screenshots folder.

The folder is created automatically (os.makedirs(screenshots_folder, exist_ok=True)), but again, permissions matter.

6. Motion Detection Settings

required_frames = 3 → Motion must persist for at least 3 frames to trigger an alert.

min_contour_area = 2500 → Small movements below this area are ignored.

You may need to tune these values depending on your camera resolution and environment.

7. Threading for Alerts

threading.Thread is used so that the siren can play without freezing the video feed.

Make sure your environment allows multi-threading; it works fine on most PCs.

8. Flask Server

The app runs on 0.0.0.0:5000, meaning:

http://localhost:5000 → Accessible locally.

Other devices on the same network → Accessible via your machine’s IP.

Make sure port 5000 is open if you want network access.

9. HTML Template

index.html must exist in a templates folder inside the project.

This file should include <img src="/video_feed"> for streaming.
