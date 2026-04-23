import subprocess
import threading
import os
import re
import logging
from typing import Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def detect_v4l2_format(device="/dev/video0") -> str:
    """Detect supported v4l2 format, preferring mjpeg."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-f", "v4l2", "-list_formats", "all", "-i", device],
            capture_output=True,
            text=True,
            timeout=10
        )
        output = result.stderr
        
        if "mjpeg" in output:
            logger.info("Using mjpeg format (detected)")
            return "mjpeg"
        elif "yuyv422" in output:
            logger.info("Using yuyv422 format (detected)")
            return "yuyv422"
    except Exception as e:
        logger.warning(f"Format detection failed: {e}")
    
    logger.warning("Defaulting to mjpeg format")
    return "mjpeg"


LOGO_PATH = "/app/assets/logo.png"
LOGO_OPACITY = 0.85
LOGO_MARGIN = 15


class GStreamerPipeline:
    def __init__(
        self,
        source: str = "test",
        rtsp_url: str = "rtsp://localhost:8554/stream",
        video_device: str = "/dev/video0",
        recordings_dir: str = "/app/recordings",
        hls_dir: str = "/app/hls",
        use_gpu: bool = True
    ):
        self.source = source
        self.rtsp_url = rtsp_url
        self.video_device = video_device
        self.recordings_dir = recordings_dir
        self.hls_dir = hls_dir
        self.use_gpu = use_gpu

        self.ffmpeg_process: Optional[subprocess.Popen] = None
        self.recording_process: Optional[subprocess.Popen] = None
        self.main_loop: Optional[threading.Thread] = None
        self.is_running = False

        self.fps = 30.0
        self.resolution = "1280x720"
        self.encoder = "NVENC" if use_gpu else "x264"

        self.is_recording = False
        self.current_recording_file: Optional[str] = None

        os.makedirs(hls_dir, exist_ok=True)
        os.makedirs(recordings_dir, exist_ok=True)

    LOGO_PATH = "/app/assets/logo.png"
LOGO_OPACITY = 0.9
LOGO_MARGIN = 15


class GStreamerPipeline:
    def __init__(
        self,
        source: str = "test",
        rtsp_url: str = "rtsp://localhost:8554/stream",
        video_device: str = "/dev/video0",
        recordings_dir: str = "/app/recordings",
        hls_dir: str = "/app/hls",
        use_gpu: bool = True
    ):
        self.source = source
        self.rtsp_url = rtsp_url
        self.video_device = video_device
        self.recordings_dir = recordings_dir
        self.hls_dir = hls_dir
        self.use_gpu = use_gpu

        self.ffmpeg_process: Optional[subprocess.Popen] = None
        self.recording_process: Optional[subprocess.Popen] = None
        self.main_loop: Optional[threading.Thread] = None
        self.is_running = False

        self.fps = 30.0
        self.resolution = "1280x720"
        self.encoder = "NVENC" if use_gpu else "x264"

        self.is_recording = False
        self.current_recording_file: Optional[str] = None

        os.makedirs(hls_dir, exist_ok=True)
        os.makedirs(recordings_dir, exist_ok=True)

    def _build_hls_command(self) -> list:
        if self.source == "test":
            output_path = os.path.join(self.hls_dir, "stream.m3u8")
            return [
                "ffmpeg", "-re",
                "-f", "lavfi", "-i", "testsrc2=size=1280x720:rate=30",
                "-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency",
                "-pix_fmt", "yuv420p", "-profile:v", "baseline", "-level", "3.0",
                "-g", "30", "-keyint_min", "30", "-b:v", "2M",
                "-f", "hls", "-hls_time", "1", "-hls_list_size", "3",
                "-hls_wrap", "10", "-hls_flags", "delete_segments+append_list",
                "-start_number", "0", "-hls_segment_filename",
                os.path.join(self.hls_dir, "segment_%03d.ts"), output_path
            ]
        elif self.source == "usb":
            output_path = os.path.join(self.hls_dir, "stream.m3u8")
            return [
                "ffmpeg",
                "-f", "v4l2", "-input_format", "mjpeg",
                "-video_size", "1280x720", "-framerate", "30", "-i", self.video_device,
                "-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency",
                "-pix_fmt", "yuv420p", "-profile:v", "baseline", "-level", "3.0",
                "-g", "30", "-keyint_min", "30", "-b:v", "2M",
                "-f", "hls", "-hls_time", "1", "-hls_list_size", "3",
                "-hls_wrap", "10", "-hls_flags", "delete_segments+append_list",
                "-start_number", "0", "-hls_segment_filename",
                os.path.join(self.hls_dir, "segment_%03d.ts"), output_path
            ]
        else:
            output_path = os.path.join(self.hls_dir, "stream.m3u8")
            return [
                "ffmpeg", "-re",
                "-rtsp_transport", "tcp", "-i", self.rtsp_url,
                "-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency",
                "-pix_fmt", "yuv420p", "-profile:v", "baseline", "-level", "3.0",
                "-g", "30", "-keyint_min", "30", "-b:v", "2M",
                "-f", "hls", "-hls_time", "1", "-hls_list_size", "3",
                "-hls_wrap", "10", "-hls_flags", "delete_segments+append_list",
                "-start_number", "0", "-hls_segment_filename",
                os.path.join(self.hls_dir, "segment_%03d.ts"), output_path
            ]

    def add_logo_overlay(self, input_file: str, output_file: str) -> list:
        logo_pos = f"overlay=W-w-{LOGO_MARGIN}:{LOGO_MARGIN}"
        return [
            "ffmpeg", "-y", "-i", input_file,
            "-i", LOGO_PATH,
            "-vf", f"format=rgba,setalpha={LOGO_OPACITY},{logo_pos}",
            "-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency",
            "-pix_fmt", "yuv420p",
            "-c:a", "copy",
            output_file
        ]

    def start(self):
        if self.is_running:
            logger.warning("Pipeline already running")
            return

        logger.info(f"Starting FFmpeg pipeline with source: {self.source}")
        cmd = self._build_hls_command()
        logger.info(f"Command: {' '.join(cmd)}")

        self.ffmpeg_process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        self.is_running = True
        logger.info("FFmpeg pipeline started successfully")
        self._start_monitor()

    def _start_monitor(self):
        def monitor():
            restart_count = 0
            max_restarts = 3
            
            while self.is_running and restart_count < max_restarts:
                if self.ffmpeg_process and self.ffmpeg_process.poll() is not None:
                    logger.warning(f"FFmpeg crashed, restart {restart_count + 1}/{max_restarts}")
                    restart_count += 1
                    cmd = self._build_hls_command()
                    logger.info(f"Restarting with: {' '.join(cmd)}")
                    self.ffmpeg_process = subprocess.Popen(
                        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                    )
                threading.Event().wait(2)
            
            if self.ffmpeg_process and self.ffmpeg_process.poll() is not None:
                logger.error("Max restarts exceeded, pipeline stopped")

        self.main_loop = threading.Thread(target=monitor, daemon=True)
        self.main_loop.start()

    def stop(self):
        if not self.is_running:
            return

        logger.info("Stopping FFmpeg pipeline")
        if self.ffmpeg_process:
            self.ffmpeg_process.terminate()
            try:
                self.ffmpeg_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.ffmpeg_process.kill()

        self.is_running = False
        logger.info("FFmpeg pipeline stopped")

    def start_recording(self) -> tuple[bool, str]:
        if self.is_recording:
            return False, "Recording already in progress"
        
        if not self.is_running:
            return False, "Pipeline not running"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        recording_file = f"recording_{timestamp}.mp4"
        recording_path = os.path.join(self.recordings_dir, recording_file)
        
        try:
            os.makedirs(self.recordings_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"Cannot create recordings directory: {e}")
            return False, f"Cannot create recordings directory: {e}"
        
        logger.info(f"Starting recording from HLS: {recording_file}")
        cmd = self._build_record_from_hls_command(recording_path)
        
        try:
            self.recording_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            self.is_recording = True
            self.current_recording_file = recording_file
            logger.info(f"Recording started: {recording_file}")
            return True, recording_file
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            return False, f"Failed to start recording: {e}"

    def stop_recording(self) -> tuple[bool, Optional[dict]]:
        if not self.is_recording:
            return False, None
        
        recording_file = self.current_recording_file
        
        logger.info("Stopping recording process")
        if self.recording_process:
            self.recording_process.terminate()
            try:
                self.recording_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.recording_process.kill()
                self.recording_process.wait()
        
        temp_path = os.path.join(self.recordings_dir, recording_file)
        final_path = os.path.join(self.recordings_dir, f"with_logo_{recording_file}")
        
        if os.path.exists(temp_path):
            try:
                logger.info(f"Adding logo overlay to {recording_file}")
                cmd = self.add_logo_toRecording(temp_path, final_path)
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                    os.rename(final_path, temp_path)
                    logger.info(f"Logo added to {recording_file}")
                else:
                    logger.warning(f"Logo overlay failed: {result.stderr}")
            except Exception as e:
                logger.warning(f"Could not add logo: {e}")
        
        duration = 0.0
        if os.path.exists(temp_path):
            try:
                duration = os.path.getsize(temp_path) / (1024 * 1024)
            except:
                pass
        
        self.is_recording = False
        self.current_recording_file = None
        self.recording_process = None
        
        logger.info(f"Recording stopped: {recording_file}")
        return True, {"filename": recording_file, "size_mb": round(duration, 2)}

    def _build_record_from_hls_command(self, output_path: str) -> list:
        hls_url = "http://127.0.0.1:8000/hls/stream.m3u8"
        return [
            "ffmpeg", "-y", "-re", "-i", hls_url,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "zerolatency",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            "-f", "mp4",
            output_path
        ]

    def add_logo_toRecording(self, input_file: str, output_file: str) -> list:
        logo_pos = f"overlay=W-w-{LOGO_MARGIN}:{LOGO_MARGIN}"
        return [
            "ffmpeg", "-y", "-i", input_file,
            "-i", LOGO_PATH,
            "-filter_complex", f"[1:v]format=rgba,setalpha={LOGO_OPACITY}[logo];[0:v][logo]{logo_pos}",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "zerolatency",
            "-pix_fmt", "yuv420p",
            "-c:a", "copy",
            output_file
        ]

    def get_status(self) -> dict:
        return {
            "is_running": self.is_running,
            "source": self.source,
            "fps": self.fps,
            "resolution": self.resolution,
            "encoder": self.encoder,
            "is_recording": self.is_recording,
            "current_recording": self.current_recording_file
        }