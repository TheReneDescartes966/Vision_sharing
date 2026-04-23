interface PipelineStatus {
  is_running: boolean;
  source: string;
  fps: number;
  resolution: string;
  encoder: string;
}

interface RecordingStatus {
  is_recording: boolean;
  current_file: string | null;
  start_time: string | null;
  duration_seconds: number;
}

interface SystemStatus {
  pipeline: PipelineStatus;
  recording: RecordingStatus;
  recordings_count: number;
  disk_usage_mb: number;
}

interface SystemStatusPanelProps {
  status: SystemStatus | null;
}

export function SystemStatusPanel({ status }: SystemStatusPanelProps) {
  if (!status) {
    return (
      <div className="card">
        <div className="card-header">
          <h2>System Status</h2>
        </div>
        <div className="loading">
          <div className="spinner"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header">
        <h2>System Status</h2>
      </div>
      <div className="system-status">
        <div className="status-item">
          <div className="label">Pipeline</div>
          <div className="value">{status.pipeline.is_running ? 'Running' : 'Stopped'}</div>
        </div>
        <div className="status-item">
          <div className="label">Source</div>
          <div className="value">{status.pipeline.source}</div>
        </div>
        <div className="status-item">
          <div className="label">Resolution</div>
          <div className="value">{status.pipeline.resolution}</div>
        </div>
        <div className="status-item">
          <div className="label">Encoder</div>
          <div className="value">{status.pipeline.encoder}</div>
        </div>
        <div className="status-item">
          <div className="label">FPS</div>
          <div className="value">{status.pipeline.fps}</div>
        </div>
        <div className="status-item">
          <div className="label">Recordings</div>
          <div className="value">{status.recordings_count}</div>
        </div>
        <div className="status-item">
          <div className="label">Storage</div>
          <div className="value">{status.disk_usage_mb.toFixed(1)} MB</div>
        </div>
      </div>
    </div>
  );
}