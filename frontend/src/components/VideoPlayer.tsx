import { useEffect, useRef, useState } from 'react';
import videojs from 'video.js';
import Player from 'video.js/dist/types/player';

interface VideoPlayerProps {
  streamUrl: string;
  isConnected: boolean;
}

export function VideoPlayer({ streamUrl, isConnected }: VideoPlayerProps) {
  const videoRef = useRef<HTMLDivElement>(null);
  const playerRef = useRef<Player | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [streamReady, setStreamReady] = useState(false);
  const [checking, setChecking] = useState(false);
  const checkIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const checkStreamReady = async () => {
    if (checking) return;
    setChecking(true);
    
    try {
      const res = await fetch('/api/stream/ready');
      const data = await res.json();
      setStreamReady(data.ready);
    } catch {
      setStreamReady(false);
    } finally {
      setChecking(false);
    }
  };

  useEffect(() => {
    if (isConnected) {
      checkStreamReady();
      checkIntervalRef.current = setInterval(checkStreamReady, 1000);
    } else {
      if (checkIntervalRef.current) {
        clearInterval(checkIntervalRef.current);
      }
      setStreamReady(false);
    }

    return () => {
      if (checkIntervalRef.current) {
        clearInterval(checkIntervalRef.current);
      }
    };
  }, [isConnected]);

  useEffect(() => {
    if (!videoRef.current) return;

    if (playerRef.current) {
      playerRef.current.dispose();
      playerRef.current = null;
    }

    if (!isConnected || !streamReady) {
      setError('Waiting for stream...');
      return;
    }

    setError(null);

    const videoElement = document.createElement('video-js');
    videoElement.classList.add('vjs-big-play-centered');
    videoRef.current.appendChild(videoElement);

    const player = videojs(videoElement, {
      controls: true,
      responsive: true,
      fluid: true,
      playbackRates: [0.5, 1, 1.5, 2],
      sources: [
        {
          src: streamUrl,
          type: 'application/x-mpegURL'
        }
      ],
      html5: {
        vhs: {
          overrideNative: true
        }
      }
    }, () => {
      videojs.log('Player is ready');
    });

    player.on('error', () => {
      const err = player.error();
      if (err) {
        setError(`Stream error: ${err.message}`);
      }
    });

    playerRef.current = player;

    return () => {
      if (playerRef.current) {
        playerRef.current.dispose();
        playerRef.current = null;
      }
    };
  }, [streamUrl, isConnected, streamReady]);

  return (
    <div className="video-container">
      <div ref={videoRef} style={{ width: '100%', height: '100%' }} />
      {(!isConnected || !streamReady) && (
        <div className="video-placeholder">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
          </svg>
          <span>{isConnected ? 'Preparing stream...' : 'Waiting for video source...'}</span>
          <span style={{ fontSize: '0.75rem' }}>
            {isConnected ? 'This takes a few seconds...' : 'Connecting to camera...'}
          </span>
        </div>
      )}
      {error && isConnected && streamReady && (
        <div className="video-placeholder">
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}