import cv2
import threading
import pygame
import time
import speech_recognition as sr
from openai import OpenAI
import subprocess
import pyaudio
import pvporcupine
import numpy as np
import random
import math
import base64
import serial
import glob
from picamera2 import Picamera2
import os
import datetime
from ddgs import DDGS 

# --- CONFIGURATION ---
OPENAI_API_KEY = "sk-proj-..." # PUT YOUR KEY HERE
PICOVOICE_ACCESS_KEY = "rsh4L78Y/..." # PUT YOUR KEY HERE
KEYWORD_PATH = "aura.ppn"

# --- MODEL FILES (TensorFlow V2) ---
# We use the files you just downloaded
MODEL_PATH = "frozen_inference_graph.pb"
CONFIG_PATH = "ssd_mobilenet_v2_coco_2018_03_29.pbtxt"
BAUD_RATE = 9600

# --- ARDUINO CONNECTION ---
def find_arduino():
    ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
    for p in ports:
        try:
            print(f" >> Attempting connection on {p}...")
            ser = serial.Serial(p, BAUD_RATE, timeout=0.1)
            time.sleep(2)
            print(f" >> SUCCESS: Arduino found on {p}")
            return ser
        except: pass
    print(" !! SPINE DISCONNECTED (MOTORS OFFLINE) !!")
    return None

arduino = find_arduino()

def send_command(cmd):
    if arduino:
        try: 
            arduino.write(cmd.encode())
            arduino.flush()
            print(f" >> MOTOR: {cmd}")
        except: pass

# --- TUNING ---
MOVE_TIME = 5.0 

# COCO CLASSES (90 Objects) - We only care about "Box-like" things
CLASSES = {
    1: 'person', 2: 'bicycle', 3: 'car', 4: 'motorcycle', 5: 'airplane',
    6: 'bus', 7: 'train', 8: 'truck', 9: 'boat', 10: 'traffic light',
    11: 'fire hydrant', 13: 'stop sign', 14: 'parking meter', 15: 'bench',
    16: 'bird', 17: 'cat', 18: 'dog', 19: 'horse', 20: 'sheep',
    21: 'cow', 22: 'elephant', 23: 'bear', 24: 'zebra', 25: 'giraffe',
    27: 'backpack', 28: 'umbrella', 31: 'handbag', 32: 'tie', 33: 'suitcase',
    34: 'frisbee', 35: 'skis', 36: 'snowboard', 37: 'sports ball', 38: 'kite',
    39: 'baseball bat', 40: 'baseball glove', 41: 'skateboard', 42: 'surfboard',
    43: 'tennis racket', 44: 'bottle', 46: 'wine glass', 47: 'cup', 48: 'fork',
    49: 'knife', 50: 'spoon', 51: 'bowl', 52: 'banana', 53: 'apple',
    54: 'sandwich', 55: 'orange', 56: 'broccoli', 57: 'carrot', 58: 'hot dog',
    59: 'pizza', 60: 'donut', 61: 'cake', 62: 'chair', 63: 'couch',
    64: 'potted plant', 65: 'bed', 67: 'dining table', 70: 'toilet', 72: 'tv',
    73: 'laptop', 74: 'mouse', 75: 'remote', 76: 'keyboard', 77: 'cell phone',
    78: 'microwave', 79: 'oven', 80: 'toaster', 81: 'sink', 82: 'refrigerator',
    84: 'book', 85: 'clock', 86: 'vase', 87: 'scissors', 88: 'teddy bear',
    89: 'hair drier', 90: 'toothbrush'
}

# The objects Aura will hunt
BOX_TARGETS = ["suitcase", "backpack", "handbag", "book", "laptop", "tv", "microwave", "oven", "toaster", "refrigerator", "bowl", "cup"] 

# --- GLOBAL VARIABLES ---
client = None
face_system = None
frame_lock = threading.Lock()
current_frame = None
current_dist = 999
target_x = -1   
HUNT_MODE = False
god_mode_active = False

# --- AI MODEL LOADER (OPENCV DNN) ---
print(" >> LOADING AI MODEL (OpenCV TensorFlow)...")
try:
    net = cv2.dnn.readNetFromTensorflow(MODEL_PATH, CONFIG_PATH)
    print(" >> AI MODEL LOADED SUCCESSFULLY.")
except Exception as e:
    print(f" !! MODEL ERROR: {e}")
    print(" !! DID YOU RUN THE DOWNLOAD COMMANDS? !!")

# --- 1. LIVE INTERNET SEARCH ---
def search_web(query):
    current_year = datetime.date.today().year
    enhanced_query = f"{query} current status {current_year}"
    print(f" >> SEARCHING: {enhanced_query}")
    try:
        results = DDGS().text(enhanced_query, max_results=2)
        if results:
            return "\n".join([r['body'] for r in results])
    except: pass
    return None

# --- 2. GPT & VISION ---
def analyze_vision(frame):
    if frame is None: return "My eyes are closed."
    retval, buffer = cv2.imencode('.jpg', frame)
    b64 = base64.b64encode(buffer).decode('utf-8')
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[{"role": "user", "content": [{"type": "text", "text": "Describe this scene briefly."}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}]}],
            max_tokens=60
        )
        return resp.choices[0].message.content
    except Exception as e: return f"Vision Error: {e}"

def ask_gpt(user_text):
    if face_system: face_system.set_expression("thinking")
    try:
        web_context = search_web(user_text)
        today = datetime.date.today().strftime("%B %d, %Y")
        sys = f"You are Aura. Date: {today}. Answer using this LIVE INFO: {web_context}" if web_context else f"You are Aura. Date: {today}."
        resp = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "system", "content": sys}, {"role": "user", "content": user_text}])
        return resp.choices[0].message.content
    except Exception as e: return f"System Error: {e}"

# --- 3. THE FACE ENGINE ---
class LiquidFace:
    def __init__(self, screen):
        self.screen = screen
        self.w, self.h = screen.get_size()
        self.cx, self.cy = self.w // 2, self.h // 2
        self.eye_h = 100
        self.color = (0, 255, 255) # Cyan
        self.expression = "neutral"
        self.blink_timer = 0
        self.tick = 0

    def lerp(self, start, end, speed):
        return start + (end - start) * speed

    def set_expression(self, expr):
        if god_mode_active and expr != "god":
             self.expression = "god"; self.color = (255, 0, 0); self.eye_h = 40; return
        self.expression = expr
        if expr == "neutral": self.color = (0, 255, 255); self.eye_h = 120
        elif expr == "listening": self.color = (0, 255, 0); self.eye_h = 140
        elif expr == "speaking": self.color = (50, 255, 100); self.eye_h = 100
        elif expr == "hunting": self.color = (255, 0, 0); self.eye_h = 60
        elif expr == "scanning": self.color = (255, 165, 0); self.eye_h = 100
        elif expr == "god": self.color = (255, 0, 0); self.eye_h = 40
        elif expr == "thinking": self.color = (255, 255, 255); self.eye_h = 100

    def update(self):
        self.tick += 1
        self.screen.fill((0, 0, 0))
        target_h = self.eye_h
        if self.expression == "speaking": target_h = 100 + 30 * math.sin(self.tick * 0.5)
        
        self.blink_timer -= 1
        if self.blink_timer <= 0:
            target_h = 5 
            if self.blink_timer < -10: self.blink_timer = random.randint(100, 400)

        pygame.draw.ellipse(self.screen, self.color, (self.cx-150, self.cy-target_h//2, 90, target_h), 6)
        pygame.draw.ellipse(self.screen, self.color, (self.cx+60, self.cy-target_h//2, 90, target_h), 6)
        pygame.draw.circle(self.screen, self.color, (self.cx-105, self.cy), 20)
        pygame.draw.circle(self.screen, self.color, (self.cx+105, self.cy), 20)

# --- UTILS ---
def speak(text):
    print(f"Aura: {text}")
    if face_system: face_system.set_expression("speaking")
    if client:
        try:
            proc = subprocess.Popen(["mpg123", "-q", "-"], stdin=subprocess.PIPE)
            resp = client.audio.speech.create(model="tts-1", voice="nova", input=text)
            for chunk in resp.iter_bytes():
                if proc.poll() is None: proc.stdin.write(chunk)
            proc.stdin.close(); proc.wait()
        except: pass
    if face_system: face_system.set_expression("neutral")

def play_song(name):
    speak(f"Playing {name}...")
    try:
        cmd = f'yt-dlp "ytsearch1:{name}" -x --audio-format mp3 -o "song.%(ext)s" --force-overwrites'
        subprocess.run(cmd, shell=True)
        subprocess.Popen(["mpg123", "-q", "-f", "32000", "song.mp3"])
    except: speak("Song not found.")

def stop_music():
    send_command('S')

# --- THREAD 1: AI VISION (OPENCV DNN) ---
def vision_thread_logic():
    global current_frame, target_x, HUNT_MODE
    picam2 = Picamera2()
    # 300x300 is optimal for this model
    picam2.configure(picam2.create_video_configuration(main={"size": (300, 300), "format": "RGB888"}))
    picam2.start()

    while True:
        try:
            time.sleep(0.05)
            frame = picam2.capture_array()
            # Flip color for OpenCV (RGB -> BGR)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            with frame_lock: current_frame = frame.copy()

            if HUNT_MODE:
                # 1. Prepare Image for AI
                blob = cv2.dnn.blobFromImage(frame, size=(300, 300), swapRB=True, crop=False)
                net.setInput(blob)
                
                # 2. Run AI
                detections = net.forward()
                
                # 3. Parse Results
                found = False
                h, w = frame.shape[:2]
                
                # detections: [1, 1, N, 7] -> 7 = (batch, class, score, x, y, x, y)
                for i in range(detections.shape[2]):
                    confidence = detections[0, 0, i, 2]
                    
                    if confidence > 0.5: # 50% Confidence
                        idx = int(detections[0, 0, i, 1])
                        if idx in CLASSES:
                            label = CLASSES[idx]
                            
                            if label in BOX_TARGETS:
                                # Get Box Coordinates
                                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                                (startX, startY, endX, endY) = box.astype("int")
                                
                                # Find Center
                                center_x = (startX + endX) / 2
                                target_x = int(center_x)
                                found = True
                                print(f" >> FOUND {label} at X:{target_x}")
                                break # Found one, lock on
                
                if not found: target_x = -1
            else:
                target_x = -1
        except Exception as e: pass

# --- THREAD 2: HARDWARE (Spine Logic) ---
def hardware_thread_logic():
    global current_dist, target_x, HUNT_MODE, arduino, face_system
    last_action = 0

    while True:
        if arduino and arduino.in_waiting:
            try:
                line = arduino.readline().decode().strip()
                if "D:" in line: current_dist = int(line.split('|')[0].split(':')[1])
            except: pass

        if HUNT_MODE:
            if time.time() - last_action > 0.1:
                # 1. ARRIVED? (Ultrasonic < 20cm)
                if current_dist < 20 and current_dist > 0:
                    send_command('S')
                    speak("Box found.")
                    HUNT_MODE = False
                    if face_system: face_system.set_expression("neutral")
                
                # 2. SEARCH (Step-Scan to prevent blur)
                elif target_x == -1:
                    if face_system: face_system.set_expression("scanning")
                    # Turn small amount
                    send_command('L')
                    time.sleep(0.2) 
                    # STOP to let camera focus
                    send_command('S')
                    time.sleep(0.8) 
                
                # 3. ATTACK (Drive)
                else:
                    if face_system: face_system.set_expression("hunting")
                    # Frame width is 300. Center is 150.
                    if target_x < 100: send_command('L')
                    elif target_x > 200: send_command('R')
                    else: send_command('F')
                
                last_action = time.time()
        time.sleep(0.05)

# --- THREAD 3: AUDIO ---
def audio_thread_logic():
    global client, HUNT_MODE, face_system, god_mode_active, current_frame
    try: client = OpenAI(api_key=OPENAI_API_KEY)
    except: pass
    
    MIC_INDEX = 1
    INPUT_RATE = 44100
    try: porcupine = pvporcupine.create(access_key=PICOVOICE_ACCESS_KEY, keyword_paths=[KEYWORD_PATH], sensitivities=[1.0])
    except: porcupine = pvporcupine.create(access_key=PICOVOICE_ACCESS_KEY, keywords=["jarvis"], sensitivities=[1.0])

    pa = pyaudio.PyAudio()
    PORCUPINE_RATE = 16000
    resample_ratio = INPUT_RATE / PORCUPINE_RATE
    chunk_size_in = int(porcupine.frame_length * resample_ratio)
    stream = pa.open(rate=INPUT_RATE, channels=1, format=pyaudio.paInt16, input=True, frames_per_buffer=chunk_size_in, input_device_index=MIC_INDEX)
    rec = sr.Recognizer()

    speak("Aura Online.")

    while True:
        try:
            pcm = stream.read(chunk_size_in, exception_on_overflow=False)
            audio_data = np.frombuffer(pcm, dtype=np.int16)
            resampled = np.interp(np.linspace(0, len(audio_data), porcupine.frame_length, endpoint=False), np.arange(len(audio_data)), audio_data).astype(np.int16)

            if porcupine.process(resampled) >= 0:
                print(" [WAKE] Detected")
                if face_system: face_system.set_expression("listening")
                frames = []
                for _ in range(0, int(INPUT_RATE / chunk_size_in * 4)): frames.append(stream.read(chunk_size_in, exception_on_overflow=False))
                
                try:
                    user = rec.recognize_google(sr.AudioData(b''.join(frames), INPUT_RATE, 2)).lower()
                    print(f"DEBUG: Heard '{user}'")

                    if "box" in user or "find" in user:
                        speak("Hunting for box.")
                        HUNT_MODE = True

                    elif any(x in user for x in ["god mode", "who created you"]):
                        god_mode_active = True
                        if face_system: face_system.set_expression("god")
                        speak("I was created by The Architect. I am the code, and you are the god.")
                        god_mode_active = False; face_system.set_expression("neutral")

                    elif "forward" in user or "come" in user:
                        speak("Moving forward.")
                        send_command('F'); time.sleep(MOVE_TIME); send_command('S')

                    elif "back" in user:
                        speak("Moving back.")
                        send_command('B'); time.sleep(MOVE_TIME); send_command('S')

                    elif "left" in user:
                        speak("Turning left.")
                        send_command('L'); time.sleep(1.0); send_command('S')

                    elif "right" in user:
                        speak("Turning right.")
                        send_command('R'); time.sleep(1.0); send_command('S')

                    elif "stop" in user:
                        HUNT_MODE = False; send_command('S'); speak("Stopping.")

                    elif "play" in user:
                        play_song(user.split("play")[1])

                    elif "see" in user:
                        with frame_lock: speak(analyze_vision(current_frame.copy()))

                    else:
                        speak(ask_gpt(user))
                except: 
                    if face_system: face_system.set_expression("neutral")
        except: pass

# --- MAIN ---
def main():
    global face_system
    threading.Thread(target=vision_thread_logic, daemon=True).start()
    threading.Thread(target=hardware_thread_logic, daemon=True).start()
    threading.Thread(target=audio_thread_logic, daemon=True).start()
    pygame.init()
    screen = pygame.display.set_mode((800, 480), pygame.FULLSCREEN)
    pygame.mouse.set_visible(False)
    face_system = LiquidFace(screen)
    while True:
        face_system.update()
        pygame.display.flip()

if __name__ == "__main__":
    main()
