"""
========================================================
Eye Tracker Module
--------------------------------------------------------
Detects eye closure and blinking using Eye Aspect Ratio (EAR).

EAR Formula:
  EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)

  HIGH EAR (~0.38) = eyes OPEN
  LOW  EAR (~0.15) = eyes CLOSED

ear_percent:
  0%   = eyes open OR normal blink (≤15 frames) — never triggers drowsiness
  1–99% = sustained closure building (16–59 frames)
  100% = fully drowsy (≥60 frames, ~2.0s)

  Normal blinks (3–15 frames) are completely ignored — ear_percent stays 0%
  so a single blink never contributes to the drowsiness score.

consecutive_frames = 60  → is_drowsy fires after ~2.0s at 30fps

Author: Joys Johney
========================================================
"""

import numpy as np


def euclidean_distance(point1, point2):
    return float(np.sqrt(np.sum((np.array(point1) - np.array(point2)) ** 2)))


class EyeTracker:

    def __init__(self, ear_threshold=0.22, consecutive_frames=60):
        """
        ear_threshold    : EAR below this = eyes closed (0.22 — triggers at ep>=70%)
        consecutive_frames: frames eyes must stay closed → is_drowsy = True
                            60 frames @ 30fps = ~2.0 seconds
                            This feeds score 80 (Alert) in alert_manager
        """

        self.EAR_THRESHOLD      = ear_threshold
        self.CONSECUTIVE_FRAMES = consecutive_frames   # 60 frames @ 30fps = ~2.0 seconds

        # Real MediaPipe EAR range from webcam calibration:
        #   0.38 = wide open, 0.15 = fully closed
        self.EAR_OPEN   = 0.38
        self.EAR_CLOSED = 0.15

        self.blink_counter = 0
        self.total_blinks  = 0
        self.frame_counter = 0   # consecutive frames eyes are closed

        # MediaPipe landmark indices (6-point eye model)
        self.LEFT_EYE_INDICES  = [33,  160, 158, 133, 153, 144]
        self.RIGHT_EYE_INDICES = [362, 385, 387, 263, 373, 380]


    def calculate_ear(self, eye_landmarks):
        """EAR = (A + B) / (2 * C)"""
        A = euclidean_distance(eye_landmarks[1], eye_landmarks[5])
        B = euclidean_distance(eye_landmarks[2], eye_landmarks[4])
        C = euclidean_distance(eye_landmarks[0], eye_landmarks[3])
        return (A + B) / (2.0 * C) if C > 0 else 0.0


    def extract_eye_landmarks(self, face_landmarks, eye_indices, frame_width, frame_height):
        landmarks = []
        for idx in eye_indices:
            lm = face_landmarks.landmark[idx]
            landmarks.append([int(lm.x * frame_width),
                               int(lm.y * frame_height)])
        return landmarks


    def process_frame(self, face_landmarks, frame_width, frame_height):
        """
        Called every frame. Returns:
          avg_ear        : raw EAR  (0.15–0.38 typical)
          ear_percent    : closure% (0=open, 100=closed) ← KEY OUTPUT
          eyes_closed    : bool
          closed_frames  : consecutive closed frame count
          is_drowsy      : True when closed_frames >= 20
          blink_count    : total blinks
        """

        left_eye  = self.extract_eye_landmarks(
            face_landmarks, self.LEFT_EYE_INDICES,  frame_width, frame_height)
        right_eye = self.extract_eye_landmarks(
            face_landmarks, self.RIGHT_EYE_INDICES, frame_width, frame_height)

        left_ear  = self.calculate_ear(left_eye)
        right_ear = self.calculate_ear(right_eye)
        avg_ear   = (left_ear + right_ear) / 2.0

        # Eyes closed when EAR drops below threshold
        eyes_closed = avg_ear < self.EAR_THRESHOLD

        # Blink: closed 3–15 frames then reopened = one blink
        if eyes_closed:
            self.frame_counter += 1
        else:
            if 3 <= self.frame_counter <= 15:
                self.total_blinks += 1
            self.frame_counter = 0

        # is_drowsy: eyes closed for >= CONSECUTIVE_FRAMES consecutive frames (~2.0s)
        is_drowsy = self.frame_counter >= self.CONSECUTIVE_FRAMES

        # ear_percent: closure percentage — ONLY counts sustained closure, NOT blinks.
        # A normal blink lasts 3–15 frames; we ignore those so the score never spikes.
        # ear_percent is only non-zero when eyes have been closed beyond the blink window (>15 frames).
        # This prevents a single blink from triggering Warning/Alert.
        #
        #   frame_counter <= 15   → blink window, report 0% (eyes considered open)
        #   frame_counter 16–59   → sustained closure building up, scale 0→79%
        #   frame_counter >= 60   → fully drowsy, report 100%
        BLINK_MAX_FRAMES = 15
        if self.frame_counter <= BLINK_MAX_FRAMES:
            # Normal blink or eyes open — not drowsy
            ear_percent = 0
        else:
            # Sustained closure: map frames 16→60 to 0→100%
            sustained = self.frame_counter - BLINK_MAX_FRAMES
            max_sustained = self.CONSECUTIVE_FRAMES - BLINK_MAX_FRAMES  # 45 frames
            ear_percent = int(min(100, (sustained / max_sustained) * 100))

        return {
            "left_ear":            float(round(left_ear,  3)),
            "right_ear":           float(round(right_ear, 3)),
            "avg_ear":             float(round(avg_ear,   3)),
            "ear_percent":         ear_percent,        # 0=open, 100=closed
            "eyes_closed":         bool(eyes_closed),
            "blink_count":         int(self.total_blinks),
            "closed_frames":       int(self.frame_counter),
            "is_drowsy":           bool(is_drowsy),
            "left_eye_landmarks":  left_eye,
            "right_eye_landmarks": right_eye
        }


    def reset(self):
        self.blink_counter = 0
        self.total_blinks  = 0
        self.frame_counter = 0