import React, { useRef, useState, useEffect } from "react";
import {
  Play,
  Pause,
  RotateCcw,
  FastForward,
  Volume2,
  VolumeX,
  Headphones,
} from "lucide-react";

export interface AudioTrack {
  id: string;
  title: string;
  src: string;
}

interface StickyListeningAudioBarProps {
  tracks: AudioTrack[];
  currentTrackIdx?: number;
  onTrackChange?: (index: number) => void;
  className?: string;
}

export const normalizeAudioSrc = (src: string): string => {
  let normalized = src;
  if (normalized.includes("content/assets/audio/")) {
    normalized = normalized.replace(/^.*content\/assets\/audio\//, "/assets/audio/");
  } else if (normalized.includes("assets/audio/")) {
    normalized = normalized.replace(/^.*assets\/audio\//, "/assets/audio/");
  } else if (!normalized.startsWith("http") && !normalized.startsWith("/")) {
    normalized = `/assets/audio/${normalized}`;
  }
  return normalized;
};

export const extractAudioTracksFromMarkdown = (rawMarkdown: string): AudioTrack[] => {
  const tracks: AudioTrack[] = [];
  const audioTagRegex = /<audio[\s\S]*?>([\s\S]*?)<\/audio>/gi;
  let match: RegExpExecArray | null;

  while ((match = audioTagRegex.exec(rawMarkdown)) !== null) {
    const fullAudioTag = match[0];
    const inner = match[1] || "";
    let src = "";

    const directSrc = fullAudioTag.match(/src=["']([^"']+)["']/i);
    if (directSrc) {
      src = directSrc[1];
    } else {
      const sourceSrc = inner.match(/<source[\s\S]*?src=["']([^"']+)["']/i);
      if (sourceSrc) src = sourceSrc[1];
    }

    if (src) {
      const partMatch = src.match(/part[-_]?(\d+)/i);
      const testMatch = src.match(/test[-_]?(\d+)/i);
      let title = `Audio ${tracks.length + 1}`;
      if (partMatch) {
        title = `Part ${partMatch[1]}`;
        if (testMatch) title = `Test ${testMatch[1]} (P${partMatch[1]})`;
      }
      tracks.push({
        id: `track-${tracks.length}`,
        title,
        src: normalizeAudioSrc(src),
      });
    }
  }

  // Fallback: search for any .mp3 references if no audio tags matched
  if (tracks.length === 0) {
    const mp3Regex = /(?:["'(\s])([^"'()\s]+\.mp3)(?:["')\s])/gi;
    let mp3Match: RegExpExecArray | null;
    while ((mp3Match = mp3Regex.exec(rawMarkdown)) !== null) {
      const src = mp3Match[1];
      const partMatch = src.match(/part[-_]?(\d+)/i);
      const title = partMatch ? `Part ${partMatch[1]}` : `Track ${tracks.length + 1}`;
      tracks.push({
        id: `track-${tracks.length}`,
        title,
        src: normalizeAudioSrc(src),
      });
    }
  }

  return tracks;
};

export const StickyListeningAudioBar: React.FC<StickyListeningAudioBarProps> = ({
  tracks,
  currentTrackIdx = 0,
  onTrackChange,
  className = "",
}) => {
  const [activeIdx, setActiveIdx] = useState(currentTrackIdx);
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1.0);
  const [isMuted, setIsMuted] = useState(false);

  useEffect(() => {
    setActiveIdx(currentTrackIdx);
  }, [currentTrackIdx]);

  const activeTrack = tracks[activeIdx] || tracks[0];
  const rates = [0.8, 1.0, 1.2, 1.5];

  useEffect(() => {
    setIsPlaying(false);
    setCurrentTime(0);
    const audio = audioRef.current;
    if (audio) {
      audio.load();
    }
  }, [activeTrack?.src]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const onTimeUpdate = () => setCurrentTime(audio.currentTime);
    const onLoadedMetadata = () => setDuration(audio.duration || 0);
    const onEnded = () => setIsPlaying(false);

    audio.addEventListener("timeupdate", onTimeUpdate);
    audio.addEventListener("loadedmetadata", onLoadedMetadata);
    audio.addEventListener("ended", onEnded);

    return () => {
      audio.removeEventListener("timeupdate", onTimeUpdate);
      audio.removeEventListener("loadedmetadata", onLoadedMetadata);
      audio.removeEventListener("ended", onEnded);
    };
  }, [activeTrack?.src]);

  if (!tracks || tracks.length === 0) return null;

  const togglePlay = () => {
    const audio = audioRef.current;
    if (!audio) return;
    if (isPlaying) {
      audio.pause();
      setIsPlaying(false);
    } else {
      audio.play().then(() => setIsPlaying(true)).catch((e) => console.warn("Audio blocked:", e));
    }
  };

  const handleSkip = (seconds: number) => {
    const audio = audioRef.current;
    if (!audio) return;
    const target = Math.min(duration || 1000, Math.max(0, audio.currentTime + seconds));
    audio.currentTime = target;
    setCurrentTime(target);
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const audio = audioRef.current;
    if (!audio) return;
    const val = Number(e.target.value);
    audio.currentTime = val;
    setCurrentTime(val);
  };

  const handleRateChange = () => {
    const audio = audioRef.current;
    if (!audio) return;
    const nextIdx = (rates.indexOf(playbackRate) + 1) % rates.length;
    const nextRate = rates[nextIdx];
    audio.playbackRate = nextRate;
    setPlaybackRate(nextRate);
  };

  const toggleMute = () => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.muted = !isMuted;
    setIsMuted(!isMuted);
  };

  const formatTime = (seconds: number) => {
    if (isNaN(seconds) || seconds < 0) return "00:00";
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  };

  return (
    <div
      className={`sticky top-0 z-30 px-3.5 py-2.5 bg-gradient-to-r from-blue-50/95 via-indigo-50/90 to-blue-50/95 dark:from-[#161a24]/95 dark:via-[#1e2330]/90 dark:to-[#161a24]/95 border-b border-blue-200/60 dark:border-blue-900/40 backdrop-blur-md shadow-sm transition flex flex-col md:flex-row md:items-center gap-2.5 ${className}`}
    >
      {activeTrack && (
        <audio ref={audioRef} src={activeTrack.src} preload="metadata" />
      )}

      {/* Track Selector Tabs */}
      <div className="flex items-center gap-1.5 flex-shrink-0">
        <span className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-blue-600 text-white text-[11px] font-bold shadow-xs">
          <Headphones className="w-3 h-3" />
          <span>AUDIO</span>
        </span>

        {tracks.length > 1 && (
          <div className="flex items-center bg-white/80 dark:bg-gray-800/80 p-0.5 rounded-lg border border-blue-200/50 dark:border-gray-700">
            {tracks.map((t, idx) => (
              <button
                key={t.id}
                type="button"
                onClick={() => {
                  setActiveIdx(idx);
                  if (onTrackChange) onTrackChange(idx);
                }}
                className={`px-2.5 py-0.5 text-xs font-semibold rounded-md transition ${
                  idx === activeIdx
                    ? "bg-apple-blue text-white shadow-xs"
                    : "text-gray-600 dark:text-gray-300 hover:text-apple-blue"
                }`}
              >
                {t.title}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Play Controls & Seek Bar */}
      <div className="flex-1 flex items-center gap-2 min-w-0">
        {/* Rewind 5s */}
        <button
          type="button"
          onClick={() => handleSkip(-5)}
          title="Lùi 5 giây (-5s)"
          className="p-1 text-gray-500 hover:text-apple-blue dark:text-gray-400 dark:hover:text-gray-200 rounded-md transition flex-shrink-0"
        >
          <RotateCcw className="w-4 h-4" />
        </button>

        {/* Play/Pause Button */}
        <button
          type="button"
          onClick={togglePlay}
          className="w-8 h-8 rounded-lg bg-apple-blue hover:bg-apple-blueHover text-white flex items-center justify-center shadow-xs transition active:scale-95 flex-shrink-0"
          title={isPlaying ? "Tạm dừng" : "Phát audio"}
        >
          {isPlaying ? (
            <Pause className="w-3.5 h-3.5 fill-current" />
          ) : (
            <Play className="w-3.5 h-3.5 ml-0.5 fill-current" />
          )}
        </button>

        {/* Forward 5s */}
        <button
          type="button"
          onClick={() => handleSkip(5)}
          title="Tiến 5 giây (+5s)"
          className="p-1 text-gray-500 hover:text-apple-blue dark:text-gray-400 dark:hover:text-gray-200 rounded-md transition flex-shrink-0"
        >
          <FastForward className="w-4 h-4" />
        </button>

        {/* Time display current */}
        <span className="text-[11px] font-mono text-gray-600 dark:text-gray-300 w-10 text-right select-none flex-shrink-0">
          {formatTime(currentTime)}
        </span>

        {/* Timeline Slider */}
        <input
          type="range"
          min={0}
          max={duration || 100}
          step={0.1}
          value={currentTime}
          onChange={handleSeek}
          className="flex-1 h-1.5 bg-blue-200/80 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-apple-blue min-w-[80px]"
        />

        {/* Time display total */}
        <span className="text-[11px] font-mono text-gray-400 dark:text-gray-500 w-10 select-none flex-shrink-0">
          {formatTime(duration)}
        </span>
      </div>

      {/* Speed & Mute Controls */}
      <div className="flex items-center gap-1.5 justify-end flex-shrink-0">
        <button
          type="button"
          onClick={handleRateChange}
          className="px-2 py-0.5 text-xs font-mono font-bold rounded-md bg-white/90 dark:bg-gray-800 border border-gray-200/70 dark:border-gray-700 text-gray-700 dark:text-gray-200 hover:text-apple-blue transition"
          title="Tốc độ phát (0.8x, 1.0x, 1.2x, 1.5x)"
        >
          {playbackRate}x
        </button>

        <button
          type="button"
          onClick={toggleMute}
          className="p-1.5 rounded-md bg-white/90 dark:bg-gray-800 border border-gray-200/70 dark:border-gray-700 text-gray-600 dark:text-gray-300 hover:text-apple-blue transition"
          title={isMuted ? "Bật âm thanh" : "Tắt âm thanh"}
        >
          {isMuted ? <VolumeX className="w-3.5 h-3.5 text-red-500" /> : <Volume2 className="w-3.5 h-3.5" />}
        </button>
      </div>
    </div>
  );
};
