"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import Hls from "hls.js";
import { updateProgress } from "@/lib/api/courses.api";

interface VideoPlayerProps {
  hlsUrl: string;
  title?: string;
  courseId: string;
  lessonId: string;
  lastPositionSeconds?: number;
  onComplete?: () => void;
}

const PROGRESS_SAVE_INTERVAL = 30; // seconds
const COMPLETION_THRESHOLD = 90; // percent

export function VideoPlayer({
  hlsUrl,
  title = "Course video",
  courseId,
  lessonId,
  lastPositionSeconds = 0,
  onComplete,
}: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const hlsRef = useRef<Hls | null>(null);
  const completionMarked = useRef(false);
  const lastSavedTime = useRef(0);
  const [error, setError] = useState<string | null>(null);
  const [isReady, setIsReady] = useState(false);
  const isEmbeddedVideo =
    hlsUrl.includes("youtube.com/embed/") ||
    hlsUrl.includes("youtube-nocookie.com/embed/") ||
    hlsUrl.includes("player.vimeo.com/");

  const saveProgress = useCallback(
    async (percentage: number, positionSeconds: number) => {
      try {
        await updateProgress(courseId, lessonId, percentage, positionSeconds);
      } catch {
        // Progress saving is best-effort. Do not interrupt playback.
      }
    },
    [courseId, lessonId]
  );

  useEffect(() => {
    if (isEmbeddedVideo) return;
    const video = videoRef.current;
    if (!video || !hlsUrl) return;

    if (Hls.isSupported()) {
      const hls = new Hls({
        enableWorker: true,
        lowLatencyMode: false,
      });
      hlsRef.current = hls;
      hls.loadSource(hlsUrl);
      hls.attachMedia(video);
      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        setIsReady(true);
        if (lastPositionSeconds > 0) {
          video.currentTime = lastPositionSeconds;
        }
      });
      hls.on(Hls.Events.ERROR, (_, data) => {
        if (data.fatal) {
          setError("Video could not be loaded. Please try again.");
        }
      });
    } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
      // Safari native HLS support
      video.src = hlsUrl;
      video.addEventListener("loadedmetadata", () => {
        setIsReady(true);
        if (lastPositionSeconds > 0) {
          video.currentTime = lastPositionSeconds;
        }
      });
    } else {
      setError("Your browser does not support this video format.");
    }

    return () => {
      hlsRef.current?.destroy();
    };
  }, [hlsUrl, isEmbeddedVideo, lastPositionSeconds]);

  const handleTimeUpdate = useCallback(() => {
    const video = videoRef.current;
    if (!video || !video.duration) return;

    const percentage = Math.round((video.currentTime / video.duration) * 100);
    const now = video.currentTime;

    // Save progress every 30 seconds
    if (now - lastSavedTime.current >= PROGRESS_SAVE_INTERVAL) {
      lastSavedTime.current = now;
      saveProgress(percentage, Math.round(now));
    }

    // Mark complete at 90%
    if (!completionMarked.current && percentage >= COMPLETION_THRESHOLD) {
      completionMarked.current = true;
      saveProgress(100, Math.round(video.duration));
      onComplete?.();
    }
  }, [saveProgress, onComplete]);

  if (error) {
    return (
      <div className="aspect-video bg-black flex items-center justify-center">
        <div className="text-center text-white">
          <p className="text-sm">{error}</p>
          <button
            onClick={() => {
              setError(null);
              completionMarked.current = false;
            }}
            className="mt-2 text-xs underline opacity-70"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  if (isEmbeddedVideo) {
    return (
      <div className="aspect-video bg-black">
        <iframe
          src={hlsUrl}
          title={title}
          className="h-full w-full"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
          allowFullScreen
        />
      </div>
    );
  }

  return (
    <div className="aspect-video bg-black relative">
      {!isReady && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-8 h-8 border-2 border-white border-t-transparent rounded-full animate-spin" />
        </div>
      )}
      <video
        ref={videoRef}
        className="w-full h-full"
        controls
        playsInline
        onTimeUpdate={handleTimeUpdate}
        style={{ opacity: isReady ? 1 : 0, transition: "opacity 0.3s" }}
      />
    </div>
  );
}
