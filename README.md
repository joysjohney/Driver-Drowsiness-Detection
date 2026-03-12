# 🚗 Driver Drowsiness Detection System

A **real-time driver monitoring system** that detects driver fatigue using **computer vision techniques**.  
The system analyzes **eye closure and yawning patterns** through a webcam and alerts the driver when signs of drowsiness are detected.

This project was developed as a **Final Year BCA Academic Project**.

---

# ⚙ Installation Guide (macOS)

Follow the steps below to run the project locally.

---

## Step 1 — Install Python

Check if Python is installed.

```bash
python3 --version
```

Python **3.8 or higher** is recommended.

If Python is not installed, download it from:

https://www.python.org/downloads/

---

## Step 2 — Download and Extract the Project

Download the project ZIP file.

Example:

Driver-Drowsiness-Detection.zip

Extract the file.

Open **Terminal** and navigate to the project folder.

```bash
cd Driver-Drowsiness-Detection
```

---

## Step 3 — Create Virtual Environment

Create a Python virtual environment.

```bash
python3 -m venv venv
```

Activate the environment.

```bash
source venv/bin/activate
```

Your terminal will now show:

```
(venv)
```

---

## Step 4 — Install Required Libraries

Install all dependencies.

```bash
pip install -r requirements.txt
```

This installs required libraries such as:

- Flask
- OpenCV
- MediaPipe
- NumPy
- Other required dependencies

---

## Step 5 — Run the Application

Navigate to the backend folder.

```bash
cd backend
```

Start the Flask server.

```bash
python app.py
```

If successful, the terminal will display:

```
Running on http://127.0.0.1:5000
```

---

## Step 6 — Open the Application

Open a web browser and go to:

```
http://127.0.0.1:5000
```

The **Driver Drowsiness Detection System** will now start running.

---

# 📌 Project Overview

This system monitors the driver's face in real time using a webcam and detects signs of fatigue such as:

- Eye closure
- Yawning

When drowsiness is detected, the system will:

- 🔊 Trigger an audio alert
- ⚠ Display a warning notification
- 📊 Update the admin monitoring dashboard

---

# 🛠 Technologies Used

## Backend

- Python  
- Flask  
- SQLite  
- OpenCV  
- MediaPipe  
- NumPy  

## Frontend

- HTML  
- CSS  
- JavaScript  
- Chart.js  

---

# 🧠 Computer Vision Algorithms

## Eye Aspect Ratio (EAR)

```
EAR = (||p2 − p6|| + ||p3 − p5||) / (2 × ||p1 − p4||)
```

If the **EAR falls below a threshold**, the system detects eye closure.

---

## Mouth Aspect Ratio (MAR)

```
MAR = vertical mouth distance / horizontal mouth distance
```

Higher MAR values indicate **yawning**.

---

# ⚙ How the System Works

1. Webcam captures the driver's face  
2. MediaPipe FaceMesh detects facial landmarks  
3. Eye and mouth landmarks are extracted  
4. EAR and MAR values are calculated  
5. A drowsiness score is computed  
6. If fatigue is detected, the system triggers alerts  

---

# 🏗 System Architecture

```
Webcam Input
     │
     ▼
OpenCV Video Capture
     │
     ▼
MediaPipe FaceMesh
     │
     ├── Eye Tracker (EAR)
     ├── Yawn Detector (MAR)
     │
     ▼
Drowsiness Score Calculation
     │
     ▼
Alert Manager
     │
     ├── Audio Alert
     ├── Database Logging
     └── Admin Dashboard
```

---

# 🚨 System Features

- Real-time driver monitoring  
- Eye blink detection  
- Yawn detection  
- Drowsiness score calculation  
- Audio alert system  
- Driver dashboard  
- Admin monitoring dashboard  
- Driver management panel  
- Timeline chart visualization  

---

# 📂 Project Folder Structure

```
Driver-Drowsiness-Detection
│
├── backend
│   ├── app.py
│   ├── auth.py
│   ├── database.py
│   ├── drowsiness_detector.py
│   └── utils
│       ├── alert_manager.py
│       ├── eye_tracker.py
│       └── yawn_detector.py
│
├── frontend
│   ├── admin.html
│   ├── driver.html
│   ├── login.html
│   ├── register.html
│   ├── profile.html
│   ├── admin-profile.html
│   ├── user-management.html
│   └── timeline.html
│
├── requirements.txt
└── README.md
```

---

# 👤 Student Information

**Name:** Sanrose Thomas  
**Project Title:** Driver Drowsiness Detection System  
**Course:** Bachelor of Computer Applications (BCA)  
**Project Type:** Final Year Academic Project