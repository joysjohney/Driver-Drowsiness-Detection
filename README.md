<<<<<<< HEAD
# Driver-Drowsiness-Detection
=======
# 🚗 AI-Based Driver Drowsiness Detection System

## 📌 Project Overview

This project implements a **Driver Drowsiness Detection System** using **Computer Vision and Web Technologies**. The system monitors a driver in real time using a webcam and detects signs of fatigue such as **eye closure and yawning**.

If the system detects drowsiness, it will:

* Trigger an **audio alert**
* Display a **warning notification**
* Update the **admin monitoring dashboard**

This project was developed as a **final year academic project**.

---

# 🛠 Technologies Used

### Backend

* Python
* Flask
* SQLite
* OpenCV
* MediaPipe
* NumPy

### Frontend

* HTML
* CSS
* JavaScript
* Chart.js

### Computer Vision Algorithms

* Eye Aspect Ratio (EAR)
* Mouth Aspect Ratio (MAR)

---

# ⚙️ Installation Guide (macOS)

Follow these steps to run the project.

---

## Step 1 — Install Python

Check if Python is installed:

```bash
python3 --version
```

Python **3.8 or higher** is recommended.

---

## Step 2 — Extract the Project ZIP

Download the project ZIP file and extract it.

Example:

```
Driver-Drowsiness-Detection.zip
```

Open **Terminal** and navigate to the folder:

```bash
cd Driver-Drowsiness-Detection
```

---

## Step 3 — Create Virtual Environment

Create a virtual environment:

```bash
python3 -m venv venv
```

Activate it:

```bash
source venv/bin/activate
```

You should see:

```
(venv)
```

in your terminal.

---

## Step 4 — Install Required Libraries

Install dependencies from `requirements.txt`.

```bash
pip install -r requirements.txt
```

This installs:

* Flask
* OpenCV
* MediaPipe
* NumPy
* Other required libraries

---

## Step 5 — Run the Application

First navigate to the **backend folder**:

```bash
cd backend
```

Then start the Flask server:

```bash
python app.py
```

If the server starts successfully, you will see something similar to:

```
Running on http://127.0.0.1:5000
```

---

## Step 6 — Open the Application

Open your web browser and go to:

```
http://127.0.0.1:5000
```

The Driver Drowsiness Detection System will now start running.

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
│   ├── timeline.html
│
├── requirements.txt
└── README.md
```

---

# ⚙️ How the System Works

1. The webcam captures the driver's face.
2. MediaPipe FaceMesh detects facial landmarks.
3. Eye and mouth landmarks are extracted.
4. EAR and MAR values are calculated.
5. Drowsiness score is computed.
6. If fatigue is detected, alerts are triggered.

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

# 🧠 Detection Algorithms

## Eye Aspect Ratio (EAR)

EAR is used to detect eye closure.

```
EAR = (||p2 − p6|| + ||p3 − p5||) / (2 × ||p1 − p4||)
```

If EAR drops below a threshold, the system detects closed eyes.

---

## Mouth Aspect Ratio (MAR)

MAR is used to detect yawning.

```
MAR = vertical mouth distance / horizontal mouth distance
```

High MAR values indicate yawning.

---

# 🚨 System Features

* Real-time driver monitoring
* Eye blink detection
* Yawn detection
* Drowsiness score calculation
* Audio alert system
* Driver dashboard
* Admin monitoring dashboard
* Driver management panel
* Timeline chart visualization

---

# 🎓 Academic Purpose

This project demonstrates:

* Real-time computer vision
* Facial landmark detection
* Driver fatigue monitoring
* Full-stack web application development

---

# 👤 Student Information

Name: **Sanrose Thomas**

Project: **Driver Drowsiness Detection System**

Type: **BCA Academic Project**

---

# 📜 License

This project is created **for educational purposes only**.
>>>>>>> 95c6c77 (Initial commit)
