import os
import asyncio
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .models import (
    SystemStatus, RecordingInfo, StartRecordingResponse,
    StopRecordingResponse, DeleteRecordingResponse, VideoSource
)
from .recording import RecordingManager
from .gst_pipeline import GStreamerPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VIDEO_SOURCE = os.getenv("VIDEO_SOURCE", "test")
RTSP_URL = os.getenv("RTSP_URL", "rtsp://localhost:8554/stream")
VIDEO_DEVICE = os.getenv("VIDEO_DEVICE", "/dev/video0")
RECORDINGS_DIR = os.getenv("RECORDINGS_DIR", "/app/recordings")
HLS_DIR = os.getenv("HLS_DIR", "/app/hls")
USE_GPU = os.getenv("USE_GPU", "true").lower() == "true"

recording_manager = RecordingManager(recordings_dir=RECORDINGS_DIR)
gst_pipeline: Optional[GStreamerPipeline] = None
stream_ready = False


class StreamReadyResponse(BaseModel):
    ready: bool
    playlist_exists: bool
    segments_count: int
    hls_dir: str


def check_hls_ready() -> tuple[bool, bool, int]:
    """Check if HLS stream is ready."""
    global stream_ready
    playlist_path = Path(HLS_DIR) / "stream.m3u8"
    segments = list(Path(HLS_DIR).glob("segment_*.ts"))
    has_playlist = playlist_path.exists()
    has_segments = len(segments) > 0
    is_ready = has_playlist and has_segments
    
    if is_ready and not stream_ready:
        logger.info(f"Stream is now ready! Playlist exists, {len(segments)} segments")
        stream_ready = True
    elif not is_ready:
        stream_ready = False
    
    return stream_ready, has_playlist, len(segments)
stream_ready = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    global gst_pipeline

    logger.info("Starting Vison Video Service")
    logger.info(f"Video source: {VIDEO_SOURCE}")
    logger.info(f"Recording directory: {RECORDINGS_DIR}")
    logger.info(f"GPU acceleration: {USE_GPU}")

    os.makedirs(RECORDINGS_DIR, exist_ok=True)
    os.makedirs(HLS_DIR, exist_ok=True)

    gst_pipeline = GStreamerPipeline(
        source=VIDEO_SOURCE,
        rtsp_url=RTSP_URL,
        video_device=VIDEO_DEVICE,
        recordings_dir=RECORDINGS_DIR,
        hls_dir=HLS_DIR,
        use_gpu=USE_GPU
    )

    gst_thread = __import__('threading').Thread(target=gst_pipeline.start, daemon=True)
    gst_thread.start()

    yield

    logger.info("Shutting down Vison Video Service")
    if gst_pipeline:
        gst_pipeline.stop()


app = FastAPI(
    title="Vison Video Service",
    description="Real-time video streaming and recording service for Unitree G1 robots",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.delete("/recordings/{filename}", response_model=DeleteRecordingResponse)
async def delete_recording(filename: str):
    file_path = Path(RECORDINGS_DIR) / filename

    if not file_path.exists():
        return DeleteRecordingResponse(
            success=False,
            message="Recording not found"
        )

    try:
        file_path.unlink()
        return DeleteRecordingResponse(
            success=True,
            message=f"Recording {filename} deleted successfully"
        )
    except Exception as e:
        return DeleteRecordingResponse(
            success=False,
            message=f"Error deleting recording: {str(e)}"
        )


app.mount("/recordings", StaticFiles(directory=RECORDINGS_DIR), name="recordings")

from fastapi import Response

@app.get("/hls/{filename}")
async def serve_hls(filename: str, response: Response):
    if not filename.endswith('.m3u8') and not filename.endswith('.ts'):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    file_path = Path(HLS_DIR) / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="HLS segment not found")
    
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Expose-Headers"] = "*"
    
    if filename.endswith('.m3u8'):
        return Response(content=file_path.read_text(), media_type="application/vnd.apple.mpegurl")
    else:
        return FileResponse(path=str(file_path), media_type="video/mp2t")

@app.get("/hls/stream.m3u8")
async def serve_hls_playlist(response: Response):
    playlist_path = Path(HLS_DIR) / "stream.m3u8"
    if not playlist_path.exists():
        raise HTTPException(status_code=404, detail="HLS playlist not found")
    
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Expose-Headers"] = "*"
    return Response(content=playlist_path.read_text(), media_type="application/vnd.apple.mpegurl")

os.makedirs(RECORDINGS_DIR, exist_ok=True)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "vison-video-service"}


@app.get("/stream/ready", response_model=StreamReadyResponse)
async def stream_ready_endpoint():
    """Check if HLS stream is ready to play."""
    is_ready, has_playlist, segments_count = check_hls_ready()
    
    return StreamReadyResponse(
        ready=is_ready,
        playlist_exists=has_playlist,
        segments_count=segments_count,
        hls_dir=HLS_DIR
    )


@app.get("/status", response_model=SystemStatus)
async def get_status():
    pipeline_status = gst_pipeline.get_status() if gst_pipeline else {
        "is_running": False,
        "source": VIDEO_SOURCE,
        "fps": 0.0,
        "resolution": "unknown",
        "encoder": "unknown"
    }

    recording_status = recording_manager.get_status()

    recordings_count = 0
    disk_usage = 0.0
    try:
        recordings_path = Path(RECORDINGS_DIR)
        if recordings_path.exists():
            recordings_count = len(list(recordings_path.glob("*.mp4")))
            disk_usage = sum(f.stat().st_size for f in recordings_path.glob("*.mp4")) / (1024 * 1024)
    except Exception as e:
        logger.error(f"Error getting recordings info: {e}")

    return SystemStatus(
        pipeline={
            "is_running": pipeline_status["is_running"],
            "source": VideoSource(pipeline_status["source"]),
            "fps": pipeline_status["fps"],
            "resolution": pipeline_status["resolution"],
            "encoder": pipeline_status["encoder"]
        },
        recording={
            "is_recording": recording_status["is_recording"],
            "current_file": recording_status["current_file"],
            "start_time": recording_status["start_time"],
            "duration_seconds": recording_status["duration_seconds"]
        },
        recordings_count=recordings_count,
        disk_usage_mb=round(disk_usage, 2)
    )


@app.post("/recording/start", response_model=StartRecordingResponse)
async def start_recording():
    if not gst_pipeline:
        return StartRecordingResponse(
            success=False,
            message="Pipeline not initialized",
            filename=None
        )
    
    success, result = gst_pipeline.start_recording()

    if success:
        return StartRecordingResponse(
            success=True,
            message="Recording started successfully",
            filename=result
        )
    else:
        return StartRecordingResponse(
            success=False,
            message=result,
            filename=None
        )


@app.post("/recording/stop", response_model=StopRecordingResponse)
async def stop_recording():
    if not gst_pipeline:
        return StopRecordingResponse(
            success=False,
            message="Pipeline not initialized",
            filename=None,
            duration_seconds=None,
            size_mb=None
        )
    
    success, result = gst_pipeline.stop_recording()

    if success and result:
        filename = result["filename"]
        size_mb = result.get("size_mb", 0.0)

        return StopRecordingResponse(
            success=True,
            message="Recording stopped successfully",
            filename=filename,
            duration_seconds=result.get("duration_seconds"),
            size_mb=size_mb
        )
    else:
        return StopRecordingResponse(
            success=False,
            message="No recording in progress",
            filename=None,
            duration_seconds=None,
            size_mb=None
        )


@app.get("/recordings", response_model=list[RecordingInfo], tags=["Recordings"])
async def list_recordings():
    recordings = []
    recordings_path = Path(RECORDINGS_DIR)

    if recordings_path.exists():
        for file_path in sorted(recordings_path.glob("*.mp4")):
            stat = file_path.stat()
            recordings.append(RecordingInfo(
                filename=file_path.name,
                size_mb=round(stat.st_size / (1024 * 1024), 2),
                created_at=datetime.fromtimestamp(stat.st_mtime),
                duration_seconds=None
            ))

    return recordings


@app.get("/downloads", tags=["Recordings"])
async def list_recordings_for_download():
    recordings = []
    recordings_path = Path(RECORDINGS_DIR)

    if recordings_path.exists():
        for file_path in sorted(recordings_path.glob("*.mp4")):
            recordings.append({
                "filename": file_path.name,
                "size_mb": round(file_path.stat().st_size / (1024 * 1024), 2),
                "download_url": f"/download/{file_path.name}"
            })

    return recordings


@app.get("/recordings/{filename}")
async def download_recording(filename: str):
    file_path = Path(RECORDINGS_DIR) / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Recording not found")

    if not filename.endswith(".mp4"):
        raise HTTPException(status_code=400, detail="Invalid file type")

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="video/mp4",
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
    )


@app.get("/download/{filename}")
async def download_recording(filename: str):
    file_path = Path(RECORDINGS_DIR) / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Recording not found")

    if not filename.endswith(".mp4"):
        raise HTTPException(status_code=400, detail="Invalid file type")

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="video/mp4",
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
    )


@app.get("/recording/status")
async def recording_status():
    if not gst_pipeline:
        return {"is_recording": False, "current_file": None, "duration_seconds": 0}
    
    status = gst_pipeline.get_status()
    return {
        "is_recording": status.get("is_recording", False),
        "current_file": status.get("current_recording"),
        "duration_seconds": 0
    }


@app.delete("/recordings/{filename}", response_model=DeleteRecordingResponse)
async def delete_recording(filename: str):
    file_path = Path(RECORDINGS_DIR) / filename

    if not file_path.exists():
        return DeleteRecordingResponse(
            success=False,
            message="Recording not found"
        )

    try:
        file_path.unlink()
        return DeleteRecordingResponse(
            success=True,
            message=f"Recording {filename} deleted successfully"
        )
    except Exception as e:
        return DeleteRecordingResponse(
            success=False,
            message=f"Error deleting recording: {str(e)}"
        )


@app.get("/hls/{filename}")
async def serve_hls(filename: str):
    if not filename.endswith('.m3u8') and not filename.endswith('.ts'):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    file_path = Path(HLS_DIR) / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="HLS segment not found")
    
    if filename.endswith('.m3u8'):
        return FileResponse(path=str(file_path), media_type="application/vnd.apple.mpegurl")
    else:
        return FileResponse(path=str(file_path), media_type="video/mp2t")

@app.get("/hls/stream.m3u8")
async def serve_hls_playlist():
    playlist_path = Path(HLS_DIR) / "stream.m3u8"
    if not playlist_path.exists():
        raise HTTPException(status_code=404, detail="HLS playlist not found")
    return FileResponse(path=str(playlist_path), media_type="application/vnd.apple.mpegurl")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)