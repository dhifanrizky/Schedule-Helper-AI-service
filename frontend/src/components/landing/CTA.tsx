import Link from "next/link";

/**
 * LANDING: CTA (Call to Action) footer section
 */
export function CTA() {
  return (
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
  );
}
