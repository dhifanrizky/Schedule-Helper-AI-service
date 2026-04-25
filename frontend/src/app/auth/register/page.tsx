"use client";

import { Inter } from "next/font/google";
import Link from "next/link";
import type React from "react";
import { useState } from "react";

const inter = Inter({ subsets: ["latin"] });

const UserIcon = ({ className }: { className?: string }) => (
  <svg
    className={className}
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path>
    <circle cx="12" cy="7" r="4"></circle>
  </svg>
);

const MailIcon = ({ className }: { className?: string }) => (
  <svg
    className={className}
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <rect width="20" height="16" x="2" y="4" rx="2"></rect>
    <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"></path>
  </svg>
);

const LockIcon = ({ className }: { className?: string }) => (
  <svg
    className={className}
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <rect width="18" height="11" x="3" y="11" rx="2" ry="2"></rect>
    <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
  </svg>
);

const ArrowLeftIcon = ({ className }: { className?: string }) => (
  <svg
    className={className}
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="m12 19-7-7 7-7"></path>
    <path d="M19 12H5"></path>
  </svg>
);

const InfoIcon = ({ className }: { className?: string }) => (
  <svg
    className={className}
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <circle cx="12" cy="12" r="10"></circle>
    <path d="M12 16v-4"></path>
    <path d="M12 8h.01"></path>
  </svg>
);

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [emailError, setEmailError] = useState("");

  const validateEmail = (val: string) => {
    if (!val) {
      setEmailError("");
      return;
    }
    const atCount = (val.match(/@/g) || []).length;
    if (atCount !== 1) {
      setEmailError("An email address must contain a single @");
      return;
    }
    const domainPart = val.split("@")[1];
    if (
      !domainPart.includes(".") ||
      domainPart.split(".").pop()?.trim() === ""
    ) {
      setEmailError(
        "Please ensure the email address ends with a valid domain (e.g. .com).",
      );
      return;
    }
    setEmailError("");
  };

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setEmail(val);
    validateEmail(val);
  };

  const handleEmailBlur = () => {
    validateEmail(email);
  };

  return (
    <div
      className={`min-h-screen bg-[#fafafa] flex flex-col justify-center py-12 sm:px-6 lg:px-8 ${inter.className}`}
    >
      <div className="sm:mx-auto sm:w-full sm:max-w-[440px]">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-[16px] font-medium text-[#717182] hover:text-[#0A0A0A] transition-colors mb-6 ml-2"
        >
          <ArrowLeftIcon className="w-5 h-5" />
          Back to Home
        </Link>

        <div className="bg-white py-10 px-8 shadow-[0_8px_30px_rgb(0,0,0,0.04)] rounded-2xl border border-gray-100 transition-all duration-300">
          <div className="text-center mb-8">
            <h2 className="text-[28px] font-semibold tracking-tight text-[#0A0A0A]">
              Create Account
            </h2>
            <p className="mt-2 text-[16px] text-[#717182]">
              Start organizing your tasks today
            </p>
          </div>

          {/* === INTEGRASI BE: SUBMIT FORM REGISTRASI === */}
          {/* [PENJELASAN]: Saat form disubmit, kirim data user baru ke API registrasi. */}
          {/* [METHOD]: POST | [ENDPOINT]: /api/auth/register */}
          {/* [BODY]: { name: string, email: string, password: string } */}
          {/* [RESPONSE]: { token: string, user: { id, name, email, createdAt } } */}
          {/* [AKSI SETELAH SUKSES]: Simpan token, simpan user ke sessionStorage, redirect ke /dashboard */}
          {/* [AKSI JIKA GAGAL]: Tampilkan pesan error "Email sudah terdaftar" */}
          <form className="space-y-5" action="#" method="POST">
            <div>
              <label
                htmlFor="name"
                className="block text-[16px] font-medium text-[#0A0A0A]"
              >
                Name
              </label>
              <div className="relative mt-2">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5">
                  <UserIcon className="h-5 w-5 text-[#0A0A0A]/50" />
                </div>
                <input
                  id="name"
                  name="name"
                  type="text"
                  required
                  className="block w-full rounded-xl border-0 py-3.5 pl-11 text-[16px] text-[#0A0A0A] ring-1 ring-inset ring-gray-200 placeholder:text-[#717182] focus:ring-2 focus:ring-inset focus:ring-[#8A38F5] transition-all"
                  placeholder="Your name"
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="email"
                className="block text-[16px] font-medium text-[#0A0A0A]"
              >
                Email
              </label>
              <div className="relative mt-2">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5">
                  <MailIcon className="h-5 w-5 text-[#0A0A0A]/50" />
                </div>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={handleEmailChange}
                  onBlur={handleEmailBlur}
                  className={`block w-full rounded-xl border-0 py-3.5 pl-11 text-[16px] text-[#0A0A0A] ring-1 ring-inset ${emailError ? "ring-red-400 focus:ring-red-500 bg-red-50" : "ring-gray-200 focus:ring-[#8A38F5]"} placeholder:text-[#717182] focus:ring-2 focus:ring-inset transition-all`}
                  placeholder="you@example.com"
                />
              </div>
              {emailError && (
                <p className="mt-2 text-[14px] text-red-500 flex flex-row items-start gap-1.5 leading-snug">
                  <InfoIcon className="w-[18px] h-[18px] shrink-0 mt-[2px]" />
                  <span>{emailError}</span>
                </p>
              )}
            </div>

            <div>
              <label
                htmlFor="password"
                className="block text-[16px] font-medium text-[#0A0A0A]"
              >
                Password
              </label>
              <div className="relative mt-2">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5">
                  <LockIcon className="h-5 w-5 text-[#0A0A0A]/50" />
                </div>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="new-password"
                  required
                  className="block w-full rounded-xl border-0 py-3.5 pl-11 text-[16px] text-[#0A0A0A] ring-1 ring-inset ring-gray-200 placeholder:text-[#717182] focus:ring-2 focus:ring-inset focus:ring-[#8A38F5] transition-all"
                  placeholder="••••••••"
                />
              </div>
            </div>

            <div className="pt-3">
              {/* === INTEGRASI BE: TOMBOL SUBMIT REGISTRASI === */}
              {/* [PENJELASAN]: Tambahkan onSubmit async handler pada elemen <form> */}
              {/* Setelah registrasi berhasil, redirect ke /dashboard */}
              {/* Field 'member_since' otomatis diisi dari createdAt di response server */}
              <button
                type="submit"
                className="flex w-full justify-center rounded-xl bg-[#8A38F5] px-3 py-3.5 text-[16px] font-semibold text-[#FFFFFF] shadow-sm hover:bg-[#7b32db] hover:shadow-md focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#8A38F5] transition-all"
              >
                Create Account
              </button>
            </div>
          </form>

          <p className="mt-8 text-center text-[16px] text-[#717182]">
            Already have an account?{" "}
            <Link
              href="/auth/login"
              className="font-semibold text-[#030213] hover:text-[#8A38F5] transition-colors"
            >
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
