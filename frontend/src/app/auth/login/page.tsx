"use client";

import { Inter } from "next/font/google";
import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { MailIcon, LockIcon, ArrowLeftIcon, InfoIcon } from "@/components/auth/AuthIcons";
import { validateEmail } from "@/utils/validation";
import { authService } from "@/services/authService";

const inter = Inter({ subsets: ["latin"] });

/**
 * LOGIN PAGE
 * Menangani proses masuk pengguna ke aplikasi.
 */
export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [emailError, setEmailError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [generalError, setGeneralError] = useState("");

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setEmail(val);
    setEmailError(validateEmail(val));
  };

  const handleEmailBlur = () => {
    setEmailError(validateEmail(email));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setGeneralError("");
    
    // Validasi ulang sebelum kirim
    const error = validateEmail(email);
    if (error) {
      setEmailError(error);
      return;
    }

    setIsSubmitting(true);
    try {
      // === INTEGRASI BE: Proses login melalui service ===
      await authService.login(email, password);
      
      // Redirect ke dashboard setelah sukses
      router.push("/dashboard");
    } catch (err: any) {
      setGeneralError(err.message || "Invalid email or password");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className={`min-h-screen bg-[#fafafa] flex flex-col justify-center py-12 sm:px-6 lg:px-8 ${inter.className}`}>
      <div className="sm:mx-auto sm:w-full sm:max-w-[440px]">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-[16px] font-medium text-[#717182] hover:text-[#0A0A0A] transition-colors mb-6 ml-2"
        >
          <ArrowLeftIcon className="w-5 h-5" />
          Back to Home
        </Link>

        <div className="bg-white py-10 px-8 shadow-[0_8px_30px_rgb(0,0,0,0.04)] rounded-2xl border border-gray-100">
          <div className="text-center mb-8">
            <h2 className="text-[28px] font-semibold tracking-tight text-[#0A0A0A]">Welcome Back</h2>
            <p className="mt-2 text-[16px] text-[#717182]">Sign in to your account</p>
          </div>

          {generalError && (
            <div className="mb-6 p-4 bg-red-50 border border-red-100 rounded-xl flex items-start gap-3 text-red-600 text-[14px]">
              <InfoIcon className="w-5 h-5 shrink-0 mt-0.5" />
              <span>{generalError}</span>
            </div>
          )}

          <form className="space-y-5" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="email" className="block text-[16px] font-medium text-[#0A0A0A]">Email</label>
              <div className="relative mt-2">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5">
                  <MailIcon className="h-5 w-5 text-[#0A0A0A]/50" />
                </div>
                <input
                  id="email"
                  type="email"
                  required
                  value={email}
                  onChange={handleEmailChange}
                  onBlur={handleEmailBlur}
                  className={`block w-full rounded-xl border-0 py-3.5 pl-11 text-[16px] text-[#0A0A0A] ring-1 ring-inset ${emailError ? "ring-red-400 focus:ring-red-500 bg-red-50" : "ring-gray-200 focus:ring-[#8A38F5]"} placeholder:text-[#717182] transition-all`}
                  placeholder="you@example.com"
                />
              </div>
              {emailError && (
                <p className="mt-2 text-[14px] text-red-500 flex items-start gap-1.5 leading-snug">
                  <InfoIcon className="w-[18px] h-[18px] shrink-0 mt-[2px]" />
                  <span>{emailError}</span>
                </p>
              )}
            </div>

            <div>
              <label htmlFor="password" className="block text-[16px] font-medium text-[#0A0A0A]">Password</label>
              <div className="relative mt-2">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5">
                  <LockIcon className="h-5 w-5 text-[#0A0A0A]/50" />
                </div>
                <input
                  id="password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full rounded-xl border-0 py-3.5 pl-11 text-[16px] text-[#0A0A0A] ring-1 ring-inset ring-gray-200 focus:ring-2 focus:ring-[#8A38F5] transition-all"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <div className="pt-3">
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex w-full justify-center rounded-xl bg-[#8A38F5] px-3 py-3.5 text-[16px] font-semibold text-[#FFFFFF] shadow-sm hover:bg-[#7b32db] transition-all disabled:opacity-70 disabled:cursor-not-allowed"
              >
                {isSubmitting ? "Signing In..." : "Sign In"}
              </button>
            </div>
          </form>

          <p className="mt-8 text-center text-[16px] text-[#717182]">
            Don't have an account?{" "}
            <Link href="/auth/register" className="font-semibold text-[#030213] hover:text-[#8A38F5] transition-colors">
              Sign up
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
