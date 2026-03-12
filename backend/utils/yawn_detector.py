"""
========================================================
Yawn Detector Module
--------------------------------------------------------
This module detects yawning using Mouth Aspect Ratio (MAR)
based on facial landmarks provided by MediaPipe Face Mesh.

Main Responsibilities:
1. Extract mouth landmarks from the face
2. Calculate Mouth Aspect Ratio (MAR)
3. Detect yawning when mouth stays open for several frames
4. Count total yawns during monitoring

MAR Formula:

MAR = vertical mouth distance / horizontal mouth distance

If MAR becomes large and stays large for several frames,
it indicates yawning.

Author: Joys Johney
========================================================
"""

# -------------------------------------------------------
# Import Libraries
# -------------------------------------------------------

import numpy as np


# -------------------------------------------------------
# Euclidean Distance Function
# -------------------------------------------------------

def euclidean_distance(point1, point2):
    """
    Calculate Euclidean distance between two points.
    """

    return float(np.sqrt(np.sum((np.array(point1) - np.array(point2)) ** 2)))


# -------------------------------------------------------
# Yawn Detector Class
# -------------------------------------------------------

class YawnDetector:

    def __init__(self,
                 mar_threshold=0.75,
                 consecutive_frames=30,
                 use_inner_mouth=True,
                 debug=False):
        """
        Initialize Yawn Detector.

        Parameters
        ----------
        mar_threshold : float
            MAR above this value indicates yawning.

        consecutive_frames : int
            Number of frames mouth must remain open to confirm a yawn.

        use_inner_mouth : bool
            Use inner mouth corners for more sensitive detection.

        debug : bool
            Print MAR values for debugging.
        """

        self.MAR_THRESHOLD = mar_threshold        # 0.75 — requires VERY wide open mouth (real yawn)
        self.CONSECUTIVE_FRAMES = consecutive_frames  # 30 frames @ 30fps = ~1.0s sustained
        self.use_inner_mouth = use_inner_mouth
        self.debug = debug

        # Counters
        self.frame_counter = 0
        self.total_yawns = 0

        # MediaPipe landmark indices

        # Outer mouth
        self.OUTER_TOP = 13
        self.OUTER_BOTTOM = 14
        self.OUTER_LEFT = 61
        self.OUTER_RIGHT = 291

        # Inner mouth (more sensitive)
        self.INNER_LEFT = 78
        self.INNER_RIGHT = 308


    # ---------------------------------------------------
    # Calculate MAR (Mouth Aspect Ratio)
    # ---------------------------------------------------

    def calculate_mar(self, mouth_landmarks):
        """
        Calculate MAR using vertical and horizontal distances.
        """

        vertical = euclidean_distance(mouth_landmarks[0],
                                      mouth_landmarks[1])

        horizontal = euclidean_distance(mouth_landmarks[2],
                                        mouth_landmarks[3])

        mar = vertical / horizontal if horizontal > 0 else 0

        return mar


    # ---------------------------------------------------
    # Extract Mouth Landmarks
    # ---------------------------------------------------

    def extract_mouth_landmarks(self,
                                face_landmarks,
                                frame_width,
                                frame_height):
        """
        Convert normalized MediaPipe coordinates
        to pixel coordinates.
        """

        # Choose inner or outer mouth corners
        left_index = self.INNER_LEFT if self.use_inner_mouth else self.OUTER_LEFT
        right_index = self.INNER_RIGHT if self.use_inner_mouth else self.OUTER_RIGHT

        try:

            top = face_landmarks.landmark[self.OUTER_TOP]
            bottom = face_landmarks.landmark[self.OUTER_BOTTOM]
            left = face_landmarks.landmark[left_index]
            right = face_landmarks.landmark[right_index]

            landmarks = [
                [int(top.x * frame_width), int(top.y * frame_height)],
                [int(bottom.x * frame_width), int(bottom.y * frame_height)],
                [int(left.x * frame_width), int(left.y * frame_height)],
                [int(right.x * frame_width), int(right.y * frame_height)]
            ]

            return landmarks

        except (AttributeError, IndexError):

            return None


    # ---------------------------------------------------
    # Process Frame for Yawn Detection
    # ---------------------------------------------------

    def process_frame(self,
                      face_landmarks,
                      frame_width,
                      frame_height):
        """
        Detect yawning from mouth landmarks.
        """

        if face_landmarks is None:
            return {"mar": 0.0, "mar_percent": 0, "is_yawning": False,
                    "yawn_count": self.total_yawns, "yawn_detected": False, "mouth_landmarks": None}

        mouth_landmarks = self.extract_mouth_landmarks(
            face_landmarks,
            frame_width,
            frame_height
        )

        if mouth_landmarks is None:
            return {"mar": 0.0, "mar_percent": 0, "is_yawning": False,
                    "yawn_count": self.total_yawns, "yawn_detected": False, "mouth_landmarks": None}

        mar = self.calculate_mar(mouth_landmarks)

        if self.debug:
            print(f"MAR value: {mar:.3f}")


        # ---------------------------------------------------
        # Yawn Detection Logic
        # ---------------------------------------------------

        is_yawning = mar > self.MAR_THRESHOLD

        if is_yawning:

            self.frame_counter += 1

        else:

            if self.frame_counter >= self.CONSECUTIVE_FRAMES:

                self.total_yawns += 1

                if self.debug:
                    print("Yawn detected!")

            self.frame_counter = 0


        yawn_detected = self.frame_counter >= self.CONSECUTIVE_FRAMES

        # MAR 0.0 = closed, 0.6 = wide yawn (real MediaPipe range)
        mar_percent = int(min(100, (mar / 0.7) * 100))

        return {
            "mar":             float(round(mar, 3)),
            "mar_percent":     mar_percent,
            "is_yawning":      bool(is_yawning),
            "yawn_count":      int(self.total_yawns),
            "yawn_detected":   bool(yawn_detected),
            "mouth_landmarks": mouth_landmarks
        }


    # ---------------------------------------------------
    # Reset Counters
    # ---------------------------------------------------

    def reset(self):
        """
        Reset yawn counters.
        """

        self.total_yawns = 0
        self.frame_counter = 0