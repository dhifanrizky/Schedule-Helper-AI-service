import React from "react";
import { FcGoogle } from "react-icons/fc";

interface GoogleOAuthButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {}

export default function GoogleOAuthButton({ className, disabled, ...props }: GoogleOAuthButtonProps) {
  return (
    <button
      type="button"
      disabled={disabled}
      className={`flex items-center justify-center w-full gap-3 px-4 py-2.5 text-sm font-medium text-gray-700 transition-colors bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-200 active:bg-gray-100 disabled:opacity-70 disabled:cursor-wait ${className || ""}`}
      {...props}
    >
      <FcGoogle className="w-5 h-5 text-xl" />
      <span>{disabled ? "Memproses..." : "Lanjutkan dengan Google"}</span>
    </button>
  );
}