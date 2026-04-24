import { useState } from 'react';

interface Recording {
  filename: string;
  size_mb: number;
  created_at: string;
  duration_seconds: number | null;
}

interface DownloadsListProps {
  recordings: Recording[];
  onDelete: (filename: string) => void;
}

export function DownloadsList({ recordings, onDelete }: DownloadsListProps) {
  const [deleting, setDeleting] = useState<string | null>(null);

  const handleDownload = (filename: string) => {
    const link = document.createElement('a');
    link.href = `/api/recordings/${filename}`;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleDelete = async (filename: string) => {
    setDeleting(filename);
    try {
      await onDelete(filename);
    } finally {
      setDeleting(null);
    }
  };

  const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className="card">
      <div className="card-header">
        <h2>Recordings</h2>
        <span>{recordings.length} files</span>
      </div>
      
      {recordings.length === 0 ? (
        <div className="empty-state">
          <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
          </svg>
          <p>No recordings yet</p>
          <p style={{ fontSize: '0.75rem' }}>Click Start Recording to begin</p>
        </div>
      ) : (
        <div className="recordings-list">
          {recordings.map((recording) => (
            <div key={recording.filename} className="recording-item">
              <div className="recording-info-item">
                <div className="recording-name">{recording.filename}</div>
                <div className="recording-meta">
                  {recording.size_mb.toFixed(2)} MB • {formatDate(recording.created_at)}
                </div>
              </div>
              <div className="recording-actions">
                <button 
                  className="btn-icon" 
                  onClick={() => handleDownload(recording.filename)}
                  title="Download"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
                  </svg>
                </button>
                <button 
                  className="btn-icon delete"
                  onClick={() => handleDelete(recording.filename)}
                  disabled={deleting === recording.filename}
                  title="Delete"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                  </svg>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}