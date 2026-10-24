import React, { useState } from "react";
import { api } from "../services/api";
import { Logo } from "./Logo";
import {
  Lock,
  User,
  Eye,
  EyeOff,
  ArrowRight,
  ShieldCheck,
  AlertCircle,
  RotateCw,
  Sparkles,
} from "lucide-react";

interface LoginPageProps {
  onLoginSuccess: (user: { username: string; role: string }) => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setErrorMessage("Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu.");
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const res = await api.login(username, password);
      onLoginSuccess(res.user);
    } catch (err: any) {
      setErrorMessage(
        err.message || "Đăng nhập thất bại. Vui lòng kiểm tra lại thông tin."
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleFillDemo = () => {
    setUsername("admin");
    setPassword("noteai2026");
    setErrorMessage(null);
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center p-4 bg-[#f5f5f7] dark:bg-[#1c1c1e] text-[#1d1d1f] dark:text-[#f5f5f7] relative overflow-hidden selection:bg-apple-blue selection:text-white">
      {/* Background Ambient Glow */}
      <div className="absolute -top-40 -left-40 w-96 h-96 bg-blue-500/10 dark:bg-blue-500/20 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-40 -right-40 w-96 h-96 bg-purple-500/10 dark:bg-purple-500/20 rounded-full blur-3xl pointer-events-none" />

      {/* Main Login Card */}
      <div className="w-full max-w-md relative z-10 animate-fadeIn">
        <div className="bg-white/90 dark:bg-[#2c2c2e]/90 backdrop-blur-xl border border-gray-200/80 dark:border-gray-800/80 shadow-2xl rounded-3xl p-8 sm:p-10 space-y-6 transition">
          {/* Brand Header */}
          <div className="flex flex-col items-center text-center space-y-2">
            <div className="p-3 bg-gray-100/80 dark:bg-gray-800/80 rounded-2xl shadow-inner mb-1">
              <Logo size={42} showText={false} />
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
              NoteAI.v2
            </h1>
            <p className="text-xs text-apple-subtextLight dark:text-apple-subtextDark max-w-xs leading-relaxed">
              Khu Vườn Tri Thức & Luyện Thi IELTS Tự Trị
              <br />
              <span className="text-[11px] opacity-75">
                (Bảo mật truy cập qua Cloudflare Tunnel)
              </span>
            </p>
          </div>

          {/* Error Banner */}
          {errorMessage && (
            <div className="p-3.5 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 rounded-2xl flex items-start gap-2.5 text-xs text-red-600 dark:text-red-400 animate-fadeIn">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-red-500" />
              <span className="flex-1">{errorMessage}</span>
            </div>
          )}

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Username Input */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-gray-700 dark:text-gray-300 flex items-center justify-between">
                <span>Tên Đăng Nhập</span>
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-gray-400">
                  <User className="w-4 h-4" />
                </span>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Nhập tên đăng nhập..."
                  autoComplete="username"
                  required
                  className="w-full pl-10 pr-4 py-2.5 bg-gray-50 dark:bg-gray-800/80 border border-gray-200 dark:border-gray-700 rounded-xl text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-apple-blue focus:border-transparent transition"
                />
              </div>
            </div>

            {/* Password Input */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-gray-700 dark:text-gray-300 flex items-center justify-between">
                <span>Mật Khẩu</span>
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-gray-400">
                  <Lock className="w-4 h-4" />
                </span>
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Nhập mật khẩu..."
                  autoComplete="current-password"
                  required
                  className="w-full pl-10 pr-10 py-2.5 bg-gray-50 dark:bg-gray-800/80 border border-gray-200 dark:border-gray-700 rounded-xl text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-apple-blue focus:border-transparent transition"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition"
                  tabIndex={-1}
                >
                  {showPassword ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>

            {/* Remember Me & Quick fill hint */}
            <div className="flex items-center justify-between text-xs pt-1">
              <label className="flex items-center gap-2 cursor-pointer text-gray-600 dark:text-gray-400 select-none">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-3.5 h-3.5 rounded border-gray-300 text-apple-blue focus:ring-apple-blue"
                />
                <span>Ghi nhớ phiên đăng nhập</span>
              </label>

              <button
                type="button"
                onClick={handleFillDemo}
                className="text-[11px] font-medium text-apple-blue hover:underline flex items-center gap-1"
                title="Điền tự động tài khoản mặc định"
              >
                <Sparkles className="w-3 h-3" />
                <span>Mặc định (admin)</span>
              </button>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-2 py-3 bg-apple-blue hover:bg-apple-blueHover text-white rounded-xl text-sm font-semibold shadow-md hover:shadow-lg transition flex items-center justify-center gap-2 disabled:opacity-60 cursor-pointer disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <RotateCw className="w-4 h-4 animate-spin" />
                  <span>Đang xác thực...</span>
                </>
              ) : (
                <>
                  <span>Đăng Nhập NoteAI</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Security & Cloudflare Info Badge */}
          <div className="pt-2 border-t border-gray-100 dark:border-gray-800/80">
            <div className="p-3 bg-gray-50 dark:bg-gray-800/40 rounded-2xl border border-gray-100 dark:border-gray-800 flex items-start gap-2.5 text-[11px] text-gray-500 dark:text-gray-400">
              <ShieldCheck className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
              <div className="leading-relaxed">
                <strong className="text-gray-700 dark:text-gray-300">
                  Bảo Vệ Đa Lớp:
                </strong>{" "}
                Cổng mạng nội bộ được khóa cục bộ (127.0.0.1). Mọi truy cập công
                cộng đều được định tuyến an toàn qua Cloudflare Zero Trust
                Tunnel.
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-[11px] text-gray-400 dark:text-gray-500 mt-6">
          NoteAI.v2 &bull; Local Autonomous PKM &bull; IELTS 2026
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
