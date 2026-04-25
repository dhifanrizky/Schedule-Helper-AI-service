export function AnalyzingState() {
  return (
    <main className="flex-1 flex flex-col items-center justify-center h-full bg-[#FFFFFF] animate-in fade-in duration-500">
      <div className="flex flex-col items-center justify-center text-center">
        <img
          src="/images-homepage/AI%20Clarifies%20&%20Prioritizes.webp"
          alt="Analyzing"
          className="w-[64px] h-[64px] object-contain mb-6 animate-pulse"
        />
        <h2 className="text-[20px] font-bold text-[#0A0A0A] font-inter mb-2">
          Analyzing Your Tasks
        </h2>
        <p className="text-[14px] text-[#717182] font-inter">
          Prioritizing based on your context and available time...
        </p>
      </div>
    </main>
  );
}
