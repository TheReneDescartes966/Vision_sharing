# Vison - Robot Video Streaming System

Real-time video streaming and recording system for robots (Unitree G1) with web interface.

## Features

- Live HLS video streaming (web browser compatible)
- Recording to MP4 with logo overlay
- Download/Delete recordings via API
- Multiple video sources: USB camera, RTSP, test pattern
- Docker containerized (easy deployment)
- GPU acceleration support (NVENC)

## Requirements

- Docker 20.10+
- Docker Compose v2
- NVIDIA GPU (optional, for hardware encoding)

## Quick Start

```bash
cd vison_release

# Option 1: Use launch script (recommended)
./launch.sh

# Option 2: Manual
docker compose up -d --build

# Access web UI
# http://localhost:3000
```

## Usage

### Web Interface
- **URL**: http://localhost:3000
- **API**: http://localhost:8000

### Video Sources

Configure in `docker-compose.yml`:
```yaml
environment:
  - VIDEO_SOURCE=usb    # USB camera (default)
  - VIDEO_SOURCE=test    # Test pattern
  - VIDEO_SOURCE=rtsp   # RTSP stream
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/status` | GET | System status |
| `/stream/ready` | GET | Stream status |
| `/recording/start` | POST | Start recording |
| `/recording/stop` | POST | Stop recording |
| `/recordings` | GET | List recordings |
| `/download/{filename}` | GET | Download recording |
| `/recordings/{filename}` | DELETE | Delete recording |

### Examples

```bash
# Check status
curl http://localhost:8000/status

# Start recording
curl -X POST http://localhost:8000/recording/start
# ... record ...
curl -X POST http://localhost:8000/recording/stop

# List recordings
curl http://localhost:8000/recordings

# Download recording
curl -O http://localhost:8000/records/my_video.mp4
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| VIDEO_SOURCE | usb | Video source (test/usb/rtsp) |
| VIDEO_DEVICE | /dev/video0 | USB camera device |
| RTSP_URL | rtsp://... | RTSP stream URL |
| USE_GPU | true | Use GPU encoding |
| RECORDINGS_DIR | /app/recordings | Recordings path |
| HLS_DIR | /app/hls | HLS segments path |

### Port Mappings

| Port | Service |
|------|--------|
| 3000 | Web UI |
| 8000 | Video API |
| 8554 | RTSP (optional) |

## Building without Docker

### Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run build
# Serve static/ with nginx
```

## Troubleshooting

### Black screen / No video
- Check VIDEO_SOURCE in docker-compose.yml
- For USB: verify /dev/video0 exists

### UI downloads file instead of rendering
- Rebuild web-ui: `docker compose build web-ui`

### Camera permission denied
- Add to docker-compose.yml:
```yaml
devices:
  - /dev/video0:/dev/video0
cap_add:
  - CAP_SYS_ADMIN
```

### Test pattern showing instead of real video
- Set in docker-compose.yml: `VIDEO_SOURCE=usb` or `VIDEO_SOURCE=rtsp`
- Rebuild: `docker compose up -d --force-recreate video-service`

## Project Structure

```
vison_release/
├── backend/           # FastAPI + FFmpeg
│   ├── app/        # Python application
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/         # React + Vite + Nginx
│   ├── src/       # React components
│   ├── public/    # Static assets
│   ├── nginx.conf
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── launch.sh        # Quick start script
├── .env.example
└���─ README.md
```

## License

MIT