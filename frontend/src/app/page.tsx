"use client";

import { Inter } from "next/font/google";
import Link from "next/link";

const inter = Inter({ subsets: ["latin"] });

export default function HomePage() {
  return (
    <div className={`min-h-screen bg-white ${inter.className}`}>
      {/* Header */}
      <header className="flex justify-between items-center px-6 md:px-12 lg:px-16 py-5 w-full">
        <div className="text-[20px] font-bold text-[#0A0A0A]">
          Schedule Helper
        </div>
        <div className="flex items-center gap-6">
          <Link
            href="/auth/login"
            className="text-[15px] font-medium text-[#0A0A0A] hover:text-[#8A38F5] transition-colors"
          >
            Login
          </Link>
          <Link
            href="/auth/register"
            className="bg-[#B597FF] hover:opacity-90 transition-opacity text-white text-[15px] font-medium px-5 py-2.5 rounded-lg shadow-sm"
          >
            Sign Up
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <section
        className="relative w-full overflow-hidden min-h-[calc(100vh-80px)] flex items-center"
        style={{
          backgroundImage: "url('/images-homepage/Background%20homepage.webp')",
          backgroundSize: "cover",
          backgroundPosition: "center",
          backgroundRepeat: "no-repeat",
        }}
      >
        <div className="container mx-auto px-6 sm:px-16 py-16 flex flex-col md:flex-row items-center justify-between gap-12 relative z-10">
          {/* Left Text */}
          <div className="md:w-[55%] flex flex-col items-start gap-5">
            <h1 className="text-[40px] sm:text-[46px] font-bold leading-[1.15] text-[#0A0A0A] max-w-lg">
              Turn Mind Dumps into Actionable Schedules
            </h1>
            <p className="text-[16px] leading-[1.6] text-[#717182] max-w-[420px] mt-2">
              AI-powered productivity assistant that understands your chaos,
              prioritizes your tasks, and creates schedules that actually work
              for you.
            </p>
            <div className="flex flex-wrap items-center gap-4 mt-6">
              <Link
                href="/demo"
                className="flex items-center justify-center gap-2 bg-[#8A38F5] hover:opacity-90 text-white px-6 py-3.5 rounded-xl text-[16px] font-medium shadow-md transition-all"
              >
                Try Demo
                <img
                  src="/images-homepage/Arrow.webp"
                  alt="arrow"
                  className="w-[18px] h-[18px] object-contain"
                />
              </Link>
              <Link
                href="/auth/register"
                className="flex items-center justify-center bg-[#000000]/10 hover:bg-[#000000]/15 text-[#0A0A0A] px-6 py-3.5 rounded-xl text-[16px] font-medium transition-all"
              >
                Get Started Free
              </Link>
            </div>
          </div>

          {/* Right Floating Card */}
          <div className="md:w-[45%] flex justify-center md:justify-end mt-10 md:mt-0">
            <div className="bg-white p-10 sm:p-12 rounded-[24px] shadow-[0_12px_45px_rgb(0,0,0,0.06)] border border-[#000000]/10 flex flex-col gap-8 w-full max-w-[540px]">
              {/* Feature 1 */}
              <div className="flex items-center gap-6">
                <img
                  src="/images-homepage/AI-Powered%20Analysis.webp"
                  alt="AI Analysis"
                  className="w-[52px] h-[52px] object-contain shrink-0"
                />
                <div className="flex flex-col">
                  <h3 className="font-semibold text-[18px] text-[#0A0A0A]">
                    AI-Powered Analysis
                  </h3>
                  <p className="text-[16px] text-[#717182] mt-1">
                    Understands context and priorities
                  </p>
                </div>
              </div>
              {/* Feature 2 */}
              <div className="flex items-center gap-6">
                <img
                  src="/images-homepage/Smart%20Prioritization.webp"
                  alt="Smart Prioritization"
                  className="w-[52px] h-[52px] object-contain shrink-0"
                />
                <div className="flex flex-col">
                  <h3 className="font-semibold text-[18px] text-[#0A0A0A]">
                    Smart Prioritization
                  </h3>
                  <p className="text-[16px] text-[#717182] mt-1">
                    Focuses on what matters most
                  </p>
                </div>
              </div>
              {/* Feature 3 */}
              <div className="flex items-center gap-6">
                <img
                  src="/images-homepage/Actionable%20Schedules.webp"
                  alt="Actionable Schedules"
                  className="w-[52px] h-[52px] object-contain shrink-0"
                />
                <div className="flex flex-col">
                  <h3 className="font-semibold text-[18px] text-[#0A0A0A]">
                    Actionable Schedules
                  </h3>
                  <p className="text-[16px] text-[#717182] mt-1">
                    Realistic timelines that fit your life
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="bg-white py-24 px-6 sm:px-16 text-center flex flex-col items-center">
        <h2 className="text-[32px] sm:text-[36px] font-medium text-[#0A0A0A]">
          How It Works
        </h2>
        <p className="text-[16px] text-[#717182] mt-4 mb-16 max-w-3xl">
          Three simple steps to transform your thoughts into organized action
        </p>

        <div className="container mx-auto grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl">
          {/* Step 1 */}
          <div className="bg-white p-8 sm:p-10 rounded-2xl shadow-[0_4px_25px_rgb(0,0,0,0.03)] border border-gray-100 flex flex-col items-start text-left hover:shadow-[0_8px_30px_rgb(0,0,0,0.06)] transition-all">
            <div className="mb-6 bg-purple-50 p-3 rounded-2xl inline-block">
              <img
                src="/images-homepage/Dump%20Your%20Thoughts.webp"
                alt="Dump Thoughts"
                className="w-[32px] h-[32px] object-contain"
              />
            </div>
            <h3 className="text-[18px] font-semibold text-[#0A0A0A] mb-3">
              Dump Your Thoughts
            </h3>
            <p className="text-[15px] text-[#717182] leading-relaxed">
              Write everything on your mind freely. No structure needed.
            </p>
          </div>

          {/* Step 2 */}
          <div className="bg-white p-8 sm:p-10 rounded-2xl shadow-[0_4px_25px_rgb(0,0,0,0.03)] border border-gray-100 flex flex-col items-start text-left hover:shadow-[0_8px_30px_rgb(0,0,0,0.06)] transition-all">
            <div className="mb-6 bg-purple-50 p-3 rounded-2xl inline-block">
              <img
                src="/images-homepage/AI%20Clarifies%20&%20Prioritizes.webp"
                alt="AI Clarifies"
                className="w-[32px] h-[32px] object-contain"
              />
            </div>
            <h3 className="text-[18px] font-semibold text-[#0A0A0A] mb-3">
              AI Clarifies & Prioritizes
            </h3>
            <p className="text-[15px] text-[#717182] leading-relaxed">
              Our AI asks questions and understands your context to prioritize
              tasks.
            </p>
          </div>

          {/* Step 3 */}
          <div className="bg-white p-8 sm:p-10 rounded-2xl shadow-[0_4px_25px_rgb(0,0,0,0.03)] border border-gray-100 flex flex-col items-start text-left hover:shadow-[0_8px_30px_rgb(0,0,0,0.06)] transition-all">
            <div className="mb-6 bg-purple-50 p-3 rounded-2xl inline-block">
              <img
                src="/images-homepage/Get%20Your%20Schedule.webp"
                alt="Get Schedule"
                className="w-[32px] h-[32px] object-contain"
              />
            </div>
            <h3 className="text-[18px] font-semibold text-[#0A0A0A] mb-3">
              Get Your Schedule
            </h3>
            <p className="text-[15px] text-[#717182] leading-relaxed">
              Receive a personalized, actionable schedule based on your energy
              and time.
            </p>
          </div>
        </div>
      </section>

      {/* CTA Footer Section */}
      <section className="bg-[#fafafa] sm:bg-transparent py-20 px-6 sm:px-16 text-center flex flex-col items-center">
        <h2 className="text-[28px] sm:text-[32px] font-medium text-[#0A0A0A]">
          Ready to Get Organized?
        </h2>
        <p className="text-[16px] text-[#717182] mt-3 mb-10 max-w-3xl mx-auto">
          Start turning your mind dumps into actionable schedules today
        </p>

        <div className="flex flex-wrap items-center justify-center gap-4">
          <Link
            href="/demo"
            className="flex items-center justify-center bg-white border border-gray-200 hover:bg-gray-50 text-[#0A0A0A] px-7 py-3.5 rounded-xl text-[15px] font-medium shadow-sm transition-all"
          >
            Try Demo First
          </Link>
          <Link
            href="/auth/register"
            className="flex items-center justify-center gap-2 bg-[#B597FF] hover:opacity-90 text-white px-7 py-3.5 rounded-xl text-[15px] font-medium shadow-sm transition-all"
          >
            Sign Up Free
            <img
              src="/images-homepage/Arrow.webp"
              alt="arrow"
              className="w-[18px] h-[18px] object-contain"
            />
          </Link>
        </div>
      </section>
    </div>
  );
}
