import { useEffect, useState } from 'react';

interface RecordingControlsProps {
  isRecording: boolean;
  onStartRecording: () => void;
  onStopRecording: () => void;
  durationSeconds: number;
  currentFile: string | null;
}

export function RecordingControls({
  isRecording,
  onStartRecording,
  onStopRecording,
  durationSeconds,
  currentFile
}: RecordingControlsProps) {
  const [displayTime, setDisplayTime] = useState(0);

  useEffect(() => {
    if (isRecording) {
      setDisplayTime(Math.floor(durationSeconds));
    } else {
      setDisplayTime(0);
    }
  }, [isRecording, durationSeconds]);

  const formatTime = (seconds: number): string => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hrs > 0) {
      return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="controls-section">
      <div className={`recording-info ${isRecording ? 'recording' : ''}`}>
        <div className="recording-indicator">
          {isRecording && <span className="dot"></span>}
          <span>{isRecording ? 'Recording' : 'Not Recording'}</span>
        </div>
        <div className="recording-time">{formatTime(displayTime)}</div>
        {currentFile && (
          <div className="recording-filename">{currentFile}</div>
        )}
      </div>

      {!isRecording ? (
        <button className="btn btn-success" onClick={onStartRecording}>
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <circle cx="12" cy="12" r="8" />
          </svg>
          Start Recording
        </button>
      ) : (
        <button className="btn btn-danger" onClick={onStopRecording}>
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <rect x="6" y="6" width="12" height="12" rx="2" />
          </svg>
          Stop Recording
        </button>
      )}
    </div>
  );
}