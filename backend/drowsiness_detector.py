"""
========================================================
Drowsiness Detection Engine
--------------------------------------------------------
This module performs the core driver monitoring logic.

Main Responsibilities:
1. Detect face landmarks using MediaPipe Face Mesh
2. Track eye movement using EAR (Eye Aspect Ratio)
3. Detect yawning using MAR (Mouth Aspect Ratio)
4. Calculate a drowsiness score
5. Trigger alerts when fatigue is detected
6. Store detection results in the database

This module integrates:
- EyeTracker
- YawnDetector
- AlertManager

Author: Joys Johney
========================================================
"""

# -------------------------------------------------------
# Import Required Libraries
# -------------------------------------------------------

import cv2
import mediapipe as mp

from utils.eye_tracker import EyeTracker
from utils.yawn_detector import YawnDetector
from utils.alert_manager import AlertManager

from database import insert_status


# -------------------------------------------------------
# Drowsiness Detector Class
# -------------------------------------------------------

class DrowsinessDetector:

    def __init__(self):
        """
        Initialize detection engine and required modules.
        """

        # MediaPipe Face Mesh initialization
        self.mp_face_mesh = mp.solutions.face_mesh

        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # Drawing utilities for visualization
        self.mp_drawing = mp.solutions.drawing_utils
        self.drawing_spec = self.mp_drawing.DrawingSpec(
            thickness=1,
            circle_radius=1
        )

        # Initialize tracking modules
        self.eye_tracker = EyeTracker(
            ear_threshold=0.22,
            consecutive_frames=60
        )

        self.yawn_detector = YawnDetector(
            mar_threshold=0.55,
            consecutive_frames=20
        )

        self.alert_manager = AlertManager(
            timeline_seconds=60
        )

        self.frame_count = 0

        # -------------------------------------------------------
        # Toast Event Counter
        # -------------------------------------------------------
        # Counts confirmed drowsiness events (any mix of eye + yawn).
        # Rules:
        #   +1 when status transitions INTO Alert (eye closure event)
        #   +1 when a yawn is confirmed (yawn_detected rising edge)
        #   Every 3 events -> fire toast, counter resets to 0
        #   Next toast also needs exactly 3 fresh events (cool-off by count)
        #
        # MIN_EVENT_GAP_SEC: minimum seconds between any two counted events
        #   so a rapid burst of yawns cannot stack 3 events instantly.
        #   Each event must be at least 5s apart to count as a new one.
        self.toast_event_count     = 0       # events since last toast
        self.TOAST_EVENT_THRESHOLD = 3       # fire toast every N events
        self.prev_was_alert        = False   # edge-detect: Alert rising edge
        self.prev_yawn_detected    = False   # edge-detect: yawn rising edge
        self.last_event_time       = 0       # timestamp of last counted event
        self.MIN_EVENT_GAP_SEC     = 5       # min seconds between counted events
        self.toast_latch           = False   # stays True for TOAST_LATCH_SEC
        self.toast_latch_until     = 0       # timestamp when latch expires
        self.TOAST_LATCH_SEC       = 3.0     # hold toast flag 3s so poll can't miss it


    # ---------------------------------------------------
    # Process Video Frame
    # ---------------------------------------------------

    def process_frame(self, frame):
        """
        Process a single webcam frame and detect drowsiness.

        Steps:
        1. Convert frame to RGB
        2. Detect face landmarks
        3. Track eye and mouth features
        4. Calculate drowsiness score
        5. Trigger alerts if needed
        6. Store results in database
        """

        self.frame_count += 1

        height, width = frame.shape[:2]

        # Convert BGR frame to RGB (required by MediaPipe)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = self.face_mesh.process(rgb_frame)

        # Default detection results
        eye_data = {
            "avg_ear": 0.0, "ear_percent": 0,
            "blink_count": self.eye_tracker.total_blinks,
            "eyes_closed": False, "closed_frames": 0, "is_drowsy": False
        }

        yawn_data = {
            "mar": 0.0, "mar_percent": 0,
            "yawn_count": self.yawn_detector.total_yawns,
            "yawn_detected": False, "is_yawning": False
        }

        no_face_detected = False

        annotated_frame = frame.copy()


        # ---------------------------------------------------
        # Face Detected
        # ---------------------------------------------------

        if results.multi_face_landmarks:

            face_landmarks = results.multi_face_landmarks[0]

            # Eye tracking
            eye_data = self.eye_tracker.process_frame(
                face_landmarks,
                width,
                height
            )

            # Yawn detection
            yawn_data = self.yawn_detector.process_frame(
                face_landmarks,
                width,
                height
            )

        else:

            # If no face detected
            no_face_detected = True

            cv2.putText(
                annotated_frame,
                "NO FACE DETECTED",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2
            )


        # ---------------------------------------------------
        # Calculate Drowsiness Score
        # ---------------------------------------------------

        score = self.alert_manager.calculate_drowsiness_score(
            eye_data,
            yawn_data,
            no_face_detected
        )

        # Add score to timeline graph
        self.alert_manager.add_to_timeline(score)

        # Determine alert level
        alert_info = self.alert_manager.update_status(score)


        # ---------------------------------------------------
        # Visual Alert Overlay
        # ---------------------------------------------------

        import time as _time

        current_status = alert_info["status"]
        is_alert_now   = current_status == "Alert"
        now            = _time.time()

        # Red overlay + text ONLY for Alert. No yellow warning overlay on video.
        if is_alert_now:
            overlay = annotated_frame.copy()
            cv2.rectangle(overlay, (0, 0), (width, height), (0, 0, 255), -1)
            annotated_frame = cv2.addWeighted(annotated_frame, 0.75, overlay, 0.25, 0)
            text = "DROWSINESS DETECTED!"
            (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)
            cv2.putText(
                annotated_frame, text,
                ((width - tw) // 2, height // 2 + th // 2),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3
            )

        # ---------------------------------------------------
        # Toast Event Counter (any mix of eye Alert + yawn = 3 -> toast)
        # ---------------------------------------------------
        # Rising edge detection — a sustained Alert or held yawn counts as
        # ONE event, not one per frame.
        # MIN_EVENT_GAP_SEC (5s) prevents a rapid burst of yawns from
        # stacking 3 events back-to-back in a few seconds.

        alert_rising_edge = is_alert_now and not self.prev_was_alert
        yawn_rising_edge  = (yawn_data.get("yawn_detected", False) and
                             not self.prev_yawn_detected)

        if alert_rising_edge or yawn_rising_edge:
            if (now - self.last_event_time) >= self.MIN_EVENT_GAP_SEC:
                self.toast_event_count += 1
                self.last_event_time    = now

                if self.toast_event_count >= self.TOAST_EVENT_THRESHOLD:
                    # Fire toast — reset so next toast needs 3 more fresh events
                    self.toast_latch       = True
                    self.toast_latch_until = now + self.TOAST_LATCH_SEC
                    self.toast_event_count = 0

        # Update edge-detection state for next frame
        self.prev_was_alert     = is_alert_now
        self.prev_yawn_detected = yawn_data.get("yawn_detected", False)

        # Latch: hold trigger_toast=True for TOAST_LATCH_SEC so 500ms poll never misses it
        if self.toast_latch:
            trigger_toast = now < self.toast_latch_until
            if not trigger_toast:
                self.toast_latch = False
        else:
            trigger_toast = False

        alert_info["trigger_toast"] = trigger_toast


        # ---------------------------------------------------
        # Store Detection Data in Database
        # ---------------------------------------------------

        insert_status(
            status=alert_info["status"],
            drowsiness_score=score,
            ear=eye_data.get("avg_ear", 0.0),
            mar=yawn_data.get("mar", 0.0),
            blink_count=self.eye_tracker.total_blinks,
            yawn_count=self.yawn_detector.total_yawns,
            alert_count=self.alert_manager.get_total_alerts()
        )


        # ---------------------------------------------------
        # Prepare Output Results
        # ---------------------------------------------------

        detection_results = {
            "eye_data": eye_data,
            "yawn_data": yawn_data,
            "alert_info": alert_info,
            "no_face_detected": bool(no_face_detected),
            "frame_count": self.frame_count
        }

        return annotated_frame, detection_results


    # ---------------------------------------------------
    # Get Current System Status
    # ---------------------------------------------------

    def get_current_status(self):

        return {
            "status": self.alert_manager.current_status,
            "blink_count": self.eye_tracker.total_blinks,
            "yawn_count": self.yawn_detector.total_yawns,
            "alert_stats": self.alert_manager.get_alert_stats()
        }


    # ---------------------------------------------------
    # Reset Detection System
    # ---------------------------------------------------

    def reset(self):
        self.alert_manager.reset()
        self.eye_tracker.reset()
        self.yawn_detector.reset()
        self.frame_count           = 0
        self.toast_event_count     = 0
        self.prev_was_alert        = False
        self.prev_yawn_detected    = False
        self.last_event_time       = 0
        self.toast_latch           = False
        self.toast_latch_until     = 0


    # ---------------------------------------------------
    # Cleanup Resources
    # ---------------------------------------------------

    def cleanup(self):

        self.face_mesh.close()