from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class VideoSource(str, Enum):
    TEST = "test"
    RTSP = "rtsp"
    USB = "usb"


class RecordingStatus(BaseModel):
    is_recording: bool
    current_file: Optional[str] = None
    start_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None


class PipelineStatus(BaseModel):
    is_running: bool
    source: VideoSource
    fps: float
    resolution: str
    encoder: str


class SystemStatus(BaseModel):
    pipeline: PipelineStatus
    recording: RecordingStatus
    recordings_count: int
    disk_usage_mb: float


class RecordingInfo(BaseModel):
    filename: str
    size_mb: float
    created_at: datetime
    duration_seconds: Optional[float] = None


class StartRecordingResponse(BaseModel):
    success: bool
    message: str
    filename: Optional[str] = None


class StopRecordingResponse(BaseModel):
    success: bool
    message: str
    filename: Optional[str] = None
    duration_seconds: Optional[float] = None
    size_mb: Optional[float] = None


class DeleteRecordingResponse(BaseModel):
    success: bool
    message: str