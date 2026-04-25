import Link from "next/link";

/**
 * LANDING: Hero section component
 */
export function Hero() {
  return (
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
            {/* Feature Item Component */}
            <div className="flex items-center gap-6">
              <img
                src="/images-homepage/AI-Powered%20Analysis.webp"
                alt="AI Analysis"
                className="w-[52px] h-[52px] object-contain shrink-0"
              />
              <div className="flex flex-col">
                <h3 className="font-semibold text-[18px] text-[#0A0A0A]">AI-Powered Analysis</h3>
                <p className="text-[16px] text-[#717182] mt-1">Understands context and priorities</p>
              </div>
            </div>

            <div className="flex items-center gap-6">
              <img
                src="/images-homepage/Smart%20Prioritization.webp"
                alt="Smart Prioritization"
                className="w-[52px] h-[52px] object-contain shrink-0"
              />
              <div className="flex flex-col">
                <h3 className="font-semibold text-[18px] text-[#0A0A0A]">Smart Prioritization</h3>
                <p className="text-[16px] text-[#717182] mt-1">Focuses on what matters most</p>
              </div>
            </div>

            <div className="flex items-center gap-6">
              <img
                src="/images-homepage/Actionable%20Schedules.webp"
                alt="Actionable Schedules"
                className="w-[52px] h-[52px] object-contain shrink-0"
              />
              <div className="flex flex-col">
                <h3 className="font-semibold text-[18px] text-[#0A0A0A]">Actionable Schedules</h3>
                <p className="text-[16px] text-[#717182] mt-1">Realistic timelines that fit your life</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
