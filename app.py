"""
Written by Codenet Developers
Smart Motion Sensor Dashboard - Single Alert per Motion Episode with Screenshots
- Each motion episode triggers 1 siren
- Additional motion during siren continues the same alert
- Siren stops automatically after completion
- Saves a screenshot of each motion detection
- Streams live feed to browser/TV
- Logs recent motion events
"""

from flask import Flask, render_template, Response, jsonify
import cv2
from datetime import datetime
import pandas as pd
import threading
import pygame
import time
import os

# ------------------- Flask Setup ------------------- #
app = Flask(__name__)

# ------------------- Camera Setup ------------------- #
camera = cv2.VideoCapture(0)

# ------------------- Motion Detection Variables ------------------- #
motion_alert = {"motion": False, "sound_playing": False}
first_frame = None
motion_counter = 0
required_frames = 3         # motion persistence
min_contour_area = 2500     # minimum movement size to trigger

# ------------------- CSV Logging ------------------- #
csv_file = "motion_events.csv"
try:
    pd.read_csv(csv_file)
except FileNotFoundError:
    df = pd.DataFrame(columns=["timestamp"])
    df.to_csv(csv_file, index=False)

# ------------------- Screenshots Folder ------------------- #
screenshots_folder = "screenshots"
os.makedirs(screenshots_folder, exist_ok=True)

# ------------------- Initialize Sound ------------------- #
pygame.mixer.init()
pygame.mixer.music.load("alert_sound.mp3")  # Put your siren sound in project folder

# ------------------- Sound Functions ------------------- #
def play_single_alert():
    """Play siren once per motion episode."""
    if pygame.mixer.music.get_busy():
        return  # already playing, don't start again
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)  # wait until sound finishes

# Wrapper to reset sound_playing flag
def play_single_alert_wrapper():
    global motion_alert
    play_single_alert()
    motion_alert['sound_playing'] = False  # reset flag after completion

# ------------------- Motion Detection Generator ------------------- #
def detect_motion():
    global motion_alert, first_frame, motion_counter
    while True:
        ret, frame = camera.read()
        if not ret:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21,21), 0)

        if first_frame is None:
            first_frame = gray.copy().astype("float")
            continue

        # running average for background
        cv2.accumulateWeighted(gray, first_frame, 0.5)
        delta_frame = cv2.absdiff(gray, cv2.convertScaleAbs(first_frame))
        thresh = cv2.threshold(delta_frame, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motion_detected = False
        for contour in contours:
            if cv2.contourArea(contour) < min_contour_area:
                continue
            (x, y, w, h) = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0,0,255), 2)
            motion_detected = True

        # Motion persistence
        if motion_detected:
            motion_counter += 1
        else:
            motion_counter = 0

        # Trigger siren for motion episode
        if motion_counter >= required_frames:
            if not motion_alert['motion']:
                motion_alert['motion'] = True

                # Log timestamp
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                df = pd.read_csv(csv_file)
                df = pd.concat([df, pd.DataFrame({"timestamp":[timestamp]})], ignore_index=True)
                df.to_csv(csv_file, index=False)

                # Save screenshot
                screenshot_filename = os.path.join(screenshots_folder, f"motion_{timestamp}.jpg")
                cv2.imwrite(screenshot_filename, frame)

                # Play siren only if not already playing
                if not motion_alert['sound_playing']:
                    motion_alert['sound_playing'] = True
                    threading.Thread(target=play_single_alert_wrapper, daemon=True).start()
        else:
            motion_alert['motion'] = False

        # Encode frame as JPEG for streaming
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# ------------------- Flask Routes ------------------- #
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(detect_motion(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/motion_status')
def motion_status():
    df = pd.read_csv(csv_file)
    return jsonify({
        "motion_detected": motion_alert['motion'],
        "motion_events": df['timestamp'].tail(5).tolist()
    })

# ------------------- Run App ------------------- #
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
