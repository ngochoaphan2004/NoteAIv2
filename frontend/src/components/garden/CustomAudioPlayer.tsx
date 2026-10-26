import React, { useRef, useState, useEffect } from "react";
import { Play, Pause, RotateCcw, FastForward, Volume2, VolumeX } from "lucide-react";

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
  const [isMuted, setIsMuted] = useState(false);

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
    setIsPlaying(false);
    setCurrentTime(0);
    const audio = audioRef.current;
    if (audio) {
      audio.load();
    }
  }, [normalizedSrc]);

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
  }, [normalizedSrc]);

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
      className={`my-3 px-4 py-3 bg-gradient-to-r from-blue-50/80 to-indigo-50/60 dark:from-[#1e2330] dark:to-[#1a1d26] border border-blue-200/70 dark:border-blue-900/50 rounded-2xl shadow-sm flex flex-col sm:flex-row sm:items-center gap-3 transition ${className}`}
    >
      <audio ref={audioRef} src={normalizedSrc} preload="metadata" />

      {/* Main Controls */}
      <div className="flex items-center gap-1.5 flex-shrink-0">
        <button
          type="button"
          onClick={() => handleSkip(-5)}
          className="p-1.5 text-gray-500 hover:text-apple-blue dark:text-gray-400 dark:hover:text-gray-200 hover:bg-white/80 dark:hover:bg-gray-800 rounded-lg transition"
          title="Tua lại 5 giây (-5s)"
        >
          <RotateCcw className="w-4 h-4" />
        </button>

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
          onClick={() => handleSkip(5)}
          className="p-1.5 text-gray-500 hover:text-apple-blue dark:text-gray-400 dark:hover:text-gray-200 hover:bg-white/80 dark:hover:bg-gray-800 rounded-lg transition"
          title="Tua tới 5 giây (+5s)"
        >
          <FastForward className="w-4 h-4" />
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
          className="px-2.5 py-1 text-xs font-mono font-bold rounded-lg bg-white/90 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-200 hover:text-apple-blue transition"
          title="Điều chỉnh tốc độ phát"
        >
          {playbackRate}x
        </button>

        <button
          type="button"
          onClick={toggleMute}
          className="p-1.5 rounded-lg bg-white/90 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300 hover:text-apple-blue transition"
          title={isMuted ? "Bật âm thanh" : "Tắt âm thanh"}
        >
          {isMuted ? <VolumeX className="w-4 h-4 text-red-500" /> : <Volume2 className="w-4 h-4" />}
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
