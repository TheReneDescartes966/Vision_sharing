import logging
import threading
import time
from datetime import datetime
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RecordingManager:
    def __init__(self, recordings_dir: str = "/app/recordings"):
        self.recordings_dir = recordings_dir
        self.is_recording = False
        self.current_file: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self._lock = threading.Lock()

    def start_recording(self) -> tuple[bool, str]:
        with self._lock:
            if self.is_recording:
                logger.warning("Recording already in progress")
                return False, "Recording already in progress"

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.current_file = f"recording_{timestamp}.mp4"
            self.start_time = datetime.now()
            self.is_recording = True

            logger.info(f"Recording started: {self.current_file}")
            return True, self.current_file

    def stop_recording(self) -> tuple[bool, Optional[dict]]:
        with self._lock:
            if not self.is_recording:
                logger.warning("No recording in progress")
                return False, None

            duration = (datetime.now() - self.start_time).total_seconds()
            filename = self.current_file
            self.is_recording = False
            self.current_file = None
            self.start_time = None

            logger.info(f"Recording stopped: {filename}, duration: {duration:.2f}s")
            return True, {
                "filename": filename,
                "duration_seconds": duration
            }

    def get_status(self) -> dict:
        with self._lock:
            duration = 0.0
            if self.start_time:
                duration = (datetime.now() - self.start_time).total_seconds()

            return {
                "is_recording": self.is_recording,
                "current_file": self.current_file,
                "start_time": self.start_time,
                "duration_seconds": duration if self.is_recording else 0.0
            }