import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { VideoPlayer } from './components/VideoPlayer';
import { RecordingControls } from './components/RecordingControls';
import { SystemStatusPanel } from './components/SystemStatusPanel';
import { DownloadsList } from './components/DownloadsList';

const HLS_URL = '/hls/stream.m3u8';

interface RecordingStatus {
  is_recording: boolean;
  current_file: string | null;
  start_time: string | null;
  duration_seconds: number;
}

interface PipelineStatus {
  is_running: boolean;
  source: string;
  fps: number;
  resolution: string;
  encoder: string;
}

interface SystemStatus {
  pipeline: PipelineStatus;
  recording: RecordingStatus;
  recordings_count: number;
  disk_usage_mb: number;
}

interface Recording {
  filename: string;
  size_mb: number;
  created_at: string;
  duration_seconds: number | null;
}

interface RecordingState {
  isRecording: boolean;
  filename: string | null;
  duration: number;
}

interface BackendRecordingState {
  is_recording: boolean;
  current_file: string | null;
  duration_seconds: number;
}

function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [recordings, setRecordings] = useState<Recording[]>([]);
  const [recordingState, setRecordingState] = useState<RecordingState>({
    isRecording: false,
    filename: null,
    duration: 0
  });
  const recordingTimerRef = useRef<number | null>(null);

  const fetchStatus = async () => {
    try {
      const response = await axios.get<SystemStatus>('/api/status');
      setStatus(response.data);
      setIsConnected(response.data.pipeline.is_running);
    } catch (error) {
      setIsConnected(false);
    }
  };

  const fetchRecordingState = async () => {
    try {
      const response = await axios.get<BackendRecordingState>('/api/recording/status');
      const isRecording = response.data.is_recording;
      setRecordingState(prev => ({
        ...prev,
        isRecording: isRecording,
        filename: isRecording ? response.data.current_file : null
      }));
    } catch (error) {
      console.error('Failed to fetch recording state:', error);
    }
  };

  const fetchRecordings = async () => {
    try {
      const response = await axios.get<Recording[]>('/api/recordings');
      setRecordings(response.data);
    } catch (error) {
      console.error('Failed to fetch recordings:', error);
    }
  };

  const startRecording = async () => {
    try {
      await axios.post('/api/recording/start');
    } catch (error) {
      console.error('Failed to start recording:', error);
    }
  };

  const stopRecording = async () => {
    try {
      await axios.post('/api/recording/stop');
      await fetchRecordings();
    } catch (error) {
      console.error('Failed to stop recording:', error);
    }
  };

  const deleteRecording = async (filename: string) => {
    try {
      await axios.delete(`/api/recordings/${filename}`);
      await fetchRecordings();
    } catch (error) {
      console.error('Failed to delete recording:', error);
    }
  };

  const startRecordingTimer = () => {
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current);
    }
    recordingTimerRef.current = window.setInterval(() => {
      setRecordingState(prev => ({
        ...prev,
        duration: prev.duration + 1
      }));
    }, 1000);
  };

  const stopRecordingTimer = () => {
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current);
      recordingTimerRef.current = null;
    }
  };

  useEffect(() => {
    fetchStatus();
    fetchRecordingState();
    fetchRecordings();

    const statusInterval = setInterval(fetchStatus, 2000);
    const recordingInterval = setInterval(fetchRecordingState, 1000);

    return () => {
      clearInterval(statusInterval);
      clearInterval(recordingInterval);
      stopRecordingTimer();
    };
  }, []);

  useEffect(() => {
    if (recordingState.isRecording) {
      startRecordingTimer();
    } else {
      stopRecordingTimer();
      setRecordingState(prev => ({ ...prev, duration: 0 }));
    }
  }, [recordingState.isRecording]);

  return (
    <div className="app">
      <header className="header">
        <div className="header-brand">
          <img src="/logo.png" alt="Vison" className="header-logo" />
          <h1>Vison</h1>
        </div>
        <div className="status-indicator">
          <span className={`status-dot ${isConnected ? 'active' : ''}`}></span>
          <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
        </div>
      </header>

      <main className="main-content">
        <div className="video-section">
          <VideoPlayer streamUrl={HLS_URL} isConnected={isConnected} />
          <RecordingControls
            isRecording={recordingState.isRecording}
            onStartRecording={startRecording}
            onStopRecording={stopRecording}
            durationSeconds={recordingState.duration}
            currentFile={recordingState.filename}
          />
        </div>

        <aside className="sidebar">
          <SystemStatusPanel status={status} />
          <DownloadsList
            recordings={recordings}
            onDelete={deleteRecording}
          />
        </aside>
      </main>
    </div>
  );
}

export default App;