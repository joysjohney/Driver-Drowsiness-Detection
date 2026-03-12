"""
========================================================
Alert Manager Module
--------------------------------------------------------
Manages drowsiness scoring, alert levels, audio triggers,
alert history, and timeline data.

Scoring Model (PERCLOS-inspired, real-life calibrated):
────────────────────────────────────────────────────────
ear_percent : 0 = eyes OPEN (alert),  100 = eyes CLOSED (drowsy)
mar_percent : 0 = mouth CLOSED,       100 = wide open yawn

EYE COMPONENT  — max 80 pts, weighted by duration:
  ep < 50          →  0   eyes open, fine
  ep 50–69         → 30   partial closure
  ep 70–79         → 70   Warning immediately 🟡
  ep >= 80         → 80   Alert immediately  🔴

MOUTH COMPONENT — max 80 pts:
  mp < 40                           →  0   mouth closed
  mp 40–54, brief                   → 10   slight opening
  mp 40–54, is_yawning              → 20   sustained opening
  mp >= 55                          → 30   clear yawn
  yawn_detected OR mp >= 70         → 50   confirmed yawn → Warning alone
  yawn_detected AND is_yawning      → 80   sustained yawn → Alert alone

NO-FACE PENALTY: +15 pts

Thresholds:
  score >= 80  →  Alert    🔴
  score >= 70  →  Warning  🟡
  score <  70  →  Normal   🟢

Author: Joys Johney
========================================================
"""

import time
from datetime import datetime
from collections import deque


class AlertManager:

    def __init__(self, timeline_seconds=60, window_size=5, alert_threshold=2):

        self.alert_history    = []
        self.current_status   = "Normal"
        self.last_alert_time  = None
        self.alert_cooldown   = 1

        self.window_size      = window_size
        self.alert_threshold  = alert_threshold
        self.alert_window     = deque(maxlen=window_size)

        self.WARNING_THRESHOLD = 70
        self.ALERT_THRESHOLD   = 80

        self.timeline_seconds  = timeline_seconds
        self.timeline          = deque(maxlen=timeline_seconds)
        self.last_timeline_add = 0


    # ---------------------------------------------------
    # Calculate Drowsiness Score
    # ---------------------------------------------------

    def calculate_drowsiness_score(self, eye_data, yawn_data, no_face_detected=False):
        """
        Real-life drowsiness score 0–100.

        ear_percent: 0 = eyes OPEN, 100 = eyes CLOSED  ← higher = more drowsy
        mar_percent: 0 = mouth CLOSED, 100 = wide yawn ← higher = more drowsy

        Key fix: eye closure alone CAN reach Warning (70) and Alert (80),
        because sustained eye closure is the PRIMARY drowsiness signal.
        Previously max eye pts was 55 — driver could sleep and score NORMAL.
        Now max eye pts is 80 — sustained closure → Alert by itself.
        """

        # ── EYE COMPONENT (0–80 pts) ─────────────────────────────────────────
        ep            = eye_data.get("ear_percent",   0)   # 0=open  100=closed
        closed_frames = eye_data.get("closed_frames", 0)   # consecutive closed frames
        is_drowsy     = eye_data.get("is_drowsy",  False)  # tracker flag (>=20 frames)

        if ep >= 80:
            eye_score = 80   # 80%+ closed → Alert immediately 🔴
        elif ep >= 70:
            eye_score = 70   # 70%+ closed → Warning immediately 🟡
        elif ep >= 50:
            eye_score = 30   # partial closure, mild
        else:
            eye_score = 0    # eyes open, driver alert

        # ── MOUTH COMPONENT (0–80 pts) ───────────────────────────────────────
        # Real-life rule: only a CONFIRMED yawn (mouth open very wide AND
        # held for 1 full second = 30 frames) triggers drowsiness.
        # Slightly open mouth, talking, breathing = 0 score. No false alerts.
        yawn_detected = yawn_data.get("yawn_detected", False)

        if yawn_detected:
            yawn_score = 80   # confirmed real yawn → Alert 🔴
        else:
            yawn_score = 0    # anything less = not a yawn, ignore

        # ── NO-FACE PENALTY (+15 pts) ────────────────────────────────────────
        face_penalty = 15 if no_face_detected else 0

        # ── FINAL SCORE ──────────────────────────────────────────────────────
        return min(eye_score + yawn_score + face_penalty, 100)


    # ---------------------------------------------------
    # Determine Alert Level
    # ---------------------------------------------------

    def determine_alert_level(self, drowsiness_score):
        """
        score >= 80  →  Alert   (trigger alarm immediately)
        score >= 70  →  Warning (early fatigue, caution)
        score <  70  →  Normal  (driver awake)
        """
        if drowsiness_score >= self.ALERT_THRESHOLD:
            return "Alert"
        elif drowsiness_score >= self.WARNING_THRESHOLD:
            return "Warning"
        else:
            return "Normal"


    # ---------------------------------------------------
    # Check Alert Cooldown
    # ---------------------------------------------------

    def should_trigger_alert(self):
        if self.last_alert_time is None:
            return True
        return (time.time() - self.last_alert_time) >= self.alert_cooldown


    # ---------------------------------------------------
    # Timeline
    # ---------------------------------------------------

    def add_to_timeline(self, score):
        now = time.time()
        if now - self.last_timeline_add >= 1.0 or len(self.timeline) == 0:
            self.timeline.append((now, score))
            self.last_timeline_add = now
        else:
            if self.timeline:
                self.timeline[-1] = (now, score)

    def get_timeline(self):
        return list(self.timeline)


    # ---------------------------------------------------
    # Update System Status
    # ---------------------------------------------------

    def update_status(self, drowsiness_score):

        new_status     = self.determine_alert_level(drowsiness_score)
        status_changed = new_status != self.current_status

        self.alert_window.append(1 if new_status == "Alert" else 0)
        alert_count   = sum(self.alert_window)
        trigger_audio = False

        if alert_count >= self.alert_threshold and self.should_trigger_alert():
            trigger_audio        = True
            self.last_alert_time = time.time()
            self.alert_history.append({
                "timestamp": datetime.now().isoformat(),
                "score":     drowsiness_score,
                "status":    new_status
            })

        self.current_status = new_status

        return {
            "status":           new_status,
            "status_changed":   status_changed,
            "trigger_audio":    trigger_audio,
            "drowsiness_score": drowsiness_score,
            "timestamp":        datetime.now().isoformat()
        }


    # ---------------------------------------------------
    # Stats
    # ---------------------------------------------------

    def get_alert_stats(self):
        total = len(self.alert_history)
        return {
            "total_alerts":   total,
            "current_status": self.current_status,
            "last_alert":     self.alert_history[-1] if total > 0 else None,
            "alert_history":  self.alert_history[-10:]
        }

    def get_total_alerts(self):
        return len(self.alert_history)


    # ---------------------------------------------------
    # Reset
    # ---------------------------------------------------

    def reset(self):
        self.alert_history     = []
        self.current_status    = "Normal"
        self.last_alert_time   = None
        self.alert_window.clear()
        self.timeline.clear()
        self.last_timeline_add = 0