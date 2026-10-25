import React, { useRef, useState, useEffect } from "react";
import { Play, Pause, RotateCcw, Volume2, FastForward } from "lucide-react";

interface CustomAudioPlayerProps {
  src: string;
  title?: string;
  className?: string;
}

export const CustomAudioPlayer: React.FC<CustomAudioPlayerProps> = ({
  src,
  title,
  className = "",
}) => {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1.0);

  // Normalize path to backend static mount /assets/audio/
  let normalizedSrc = src;
  if (normalizedSrc.includes("content/assets/audio/")) {
    normalizedSrc = normalizedSrc.replace(/^.*content\/assets\/audio\//, "/assets/audio/");
  } else if (normalizedSrc.includes("assets/audio/")) {
    normalizedSrc = normalizedSrc.replace(/^.*assets\/audio\//, "/assets/audio/");
  } else if (!normalizedSrc.startsWith("http") && !normalizedSrc.startsWith("/")) {
    normalizedSrc = `/assets/audio/${normalizedSrc}`;
  }

  const rates = [0.8, 1.0, 1.2, 1.5];

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
  }, []);

  const togglePlay = () => {
    const audio = audioRef.current;
    if (!audio) return;
    if (isPlaying) {
      audio.pause();
      setIsPlaying(false);
    } else {
      audio.play().then(() => setIsPlaying(true)).catch((e) => console.warn("Audio play blocked:", e));
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const audio = audioRef.current;
    if (!audio) return;
    const time = Number(e.target.value);
    audio.currentTime = time;
    setCurrentTime(time);
  };

  const handleRateChange = () => {
    const audio = audioRef.current;
    if (!audio) return;
    const nextIdx = (rates.indexOf(playbackRate) + 1) % rates.length;
    const nextRate = rates[nextIdx];
    audio.playbackRate = nextRate;
    setPlaybackRate(nextRate);
  };

  const handleRestart = () => {
    const audio = audioRef.current;
    if (!audio) return;
    audio.currentTime = 0;
    setCurrentTime(0);
  };

  const formatTime = (seconds: number) => {
    if (isNaN(seconds) || seconds < 0) return "00:00";
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  };

  return (
    <div
      className={`my-3 px-4 py-3 bg-gradient-to-r from-blue-50/70 to-indigo-50/50 dark:from-[#1e2330] dark:to-[#1a1d26] border border-blue-200/60 dark:border-blue-900/40 rounded-2xl shadow-sm flex flex-col sm:flex-row sm:items-center gap-3 transition ${className}`}
    >
      <audio ref={audioRef} src={normalizedSrc} preload="metadata" />

      {/* Main Controls */}
      <div className="flex items-center gap-2 flex-shrink-0">
        <button
          type="button"
          onClick={togglePlay}
          className="w-10 h-10 rounded-xl bg-apple-blue hover:bg-apple-blueHover text-white flex items-center justify-center shadow-sm transition active:scale-95"
          title={isPlaying ? "Tạm dừng" : "Phát audio"}
        >
          {isPlaying ? <Pause className="w-4 h-4 fill-current" /> : <Play className="w-4 h-4 ml-0.5 fill-current" />}
        </button>

        <button
          type="button"
          onClick={handleRestart}
          className="p-2 text-gray-500 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-white/80 dark:hover:bg-gray-800 rounded-lg transition"
          title="Phát lại từ đầu"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>

      {/* Time & Progress Slider */}
      <div className="flex-1 flex items-center gap-2.5">
        <span className="text-xs font-mono text-gray-600 dark:text-gray-300 w-10 text-right select-none">
          {formatTime(currentTime)}
        </span>

        <input
          type="range"
          min={0}
          max={duration || 100}
          step={0.1}
          value={currentTime}
          onChange={handleSeek}
          className="flex-1 h-1.5 bg-blue-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-apple-blue"
        />

        <span className="text-xs font-mono text-gray-400 dark:text-gray-500 w-10 select-none">
          {formatTime(duration)}
        </span>
      </div>

      {/* Speed & Audio Pill */}
      <div className="flex items-center gap-2 justify-end flex-shrink-0">
        <button
          type="button"
          onClick={handleRateChange}
          className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-white/80 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-200 hover:text-apple-blue transition"
          title="Điều chỉnh tốc độ phát"
        >
          {playbackRate}x
        </button>

        {title && (
          <span className="hidden md:inline-flex text-[11px] font-medium text-gray-500 dark:text-gray-400 max-w-[140px] truncate">
            {title}
          </span>
        )}
      </div>
    </div>
  );
};
