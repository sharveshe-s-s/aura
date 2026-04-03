# AURA: The Embodied AI Robot 🤖✨

> **"Code is no longer silent. It is alive."**


# Demo
https://youtu.be/rq5pJGRbYKM?si=Qpjih5rUlvc8_fWa

Aura is an **Embodied AI Agent** that bridges the gap between Digital Superintelligence and the physical world. Unlike traditional robots that follow hard-coded loops, Aura utilizes a **Heterogeneous Split-Core Architecture** to "think" with Cloud AI (GPT-4o) and "act" with reflex-driven Edge AI (TensorFlow Lite).

---

## 🚀 Project Overview

Aura solves the **"Digital Paralysis"** of modern AI. While LLMs have high IQ, they lack agency. Aura provides a physical vessel for intelligence, designed to perceive, reason, and interact with her environment.

### **Key Capabilities**
* **👁️ Semantic Vision:** Understands complex scenes and context via **GPT-4o Vision**.
* **🎯 Kinetic Tracking:** Hunts and follows objects in real-time using **TensorFlow Lite (MobileNet V2)**.
* **🎭 Affective UI:** Features a "Liquid Face" engine that blinks, looks around, and reacts to emotions.
* **🧠 Infinite Knowledge:** Connects to the live internet via a **RAG Pipeline** to answer any query.
* **🗣️ Natural Voice:** Engaging, context-aware conversation with neural text-to-speech.

---

## 🧠 System Architecture

Aura mimics a biological nervous system by splitting "Cognition" and "Reflexes" across two distinct computing cores.

| **Layer** | **Component** | **Hardware** | **Function** |
| :--- | :--- | :--- | :--- |
| **Cognitive Cortex** | The Brain | **Raspberry Pi 4 (4GB)** | Vision, LLM Logic, Audio Processing, RAG |
| **Spinal Cord** | The Reflexes | **Arduino Uno R3** | Motor Control, Collision Avoidance, Safety |
| **The Forge** | Development | **AMD Ryzen™ 5 7640HS** | Model Training, Simulation, Optimization |

---
### 🎮 Core Functions & Voice Commands
Aura operates fully hands-free via a custom-trained Picovoice Porcupine wake-word engine. Once awakened, she enters an "Alexa-style" continuous conversation loop, allowing for fluid, back-and-forth interaction without needing to repeat her name.

### 🧠 Conversational Intelligence
Contextual Memory: Aura remembers the last 10 interactions in her buffer. If you ask, "What is the capital of Japan?" and follow up with, "What is the weather like there?", she understands the context.

Live Web Search: If asked about current events (e.g., "Give me a news update"), Aura autonomously scrapes DuckDuckGo for real-time 2026 data before answering.

"Clear Your Memory": A voice command that instantly wipes her conversational buffer for a fresh interaction.

### 👁️ Vision & Autonomy
"Aura, what do you see?" -> Triggers the PiCamera to snap a frame, encodes it in Base64, and sends it to GPT-4o for a highly descriptive, semantic breakdown of her surroundings.

"Aura, find the box." -> Activates HUNT MODE. Aura overrides the LLM, engaging the OpenCV TensorFlow model to visually scan the room. Once she locks onto a target, she autonomously drives toward it and uses her ultrasonic "Spine" to stop exactly 20cm away.

### 🎶 Media & Entertainment
"Aura, play [Song Name]." -> Bypasses standard storage limits by directly streaming high-bitrate YouTube audio into RAM using yt-dlp and mpv.

"Aura, stop the music." -> Instantly kills the streaming process and returns her to active listening mode.

### 🕹️ Direct Kinematics & Easter Eggs
Voice-Piloting: Commands like "Move forward," "Come here," "Turn left," and "Back up" send instant serial interrupts to the Arduino motor shield for precise movement.

God Mode: Asking "Who created you?" or "Activate God Mode" triggers an intense visual UI change (red eyes) and a custom voice protocol acknowledging her creator.

## 🛠️ Technology Stack

### **Hardware Components**
* **Compute:** Raspberry Pi 4 Model B (4GB), Arduino Uno R3 (ATmega328P)
* **Sensors:** Raspberry Pi Camera Module V2 (8MP), HC-SR04 Ultrasonic Array
* **Actuation:** L298N Dual H-Bridge Driver, Yellow TT Gear Motors, SG90 Servo
* **Audio:** USB Omni-directional Microphone, Active Speaker System

### **Software & Libraries**
* **Core:** Python 3.9+, C++ (Arduino)
* **Computer Vision:** OpenCV (`cv2`), TensorFlow Lite Runtime
* **AI Intelligence:** GPT-4o Vision API, OpenAI API
* **Voice Interaction:** Picovoice Porcupine (Wake Word), Google STT, Edge-TTS
* **Interface:** Pygame (Liquid Face UI), DuckDuckGo Search API



---
