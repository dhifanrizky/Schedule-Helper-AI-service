/**
 * LANDING: How It Works section component
 */
export function HowItWorks() {
  const steps = [
    {
      title: "Dump Your Thoughts",
      description: "Write everything on your mind freely. No structure needed.",
      icon: "/images-homepage/Dump%20Your%20Thoughts.webp"
    },
    {
      title: "AI Clarifies & Prioritizes",
      description: "Our AI asks questions and understands your context to prioritize tasks.",
      icon: "/images-homepage/AI%20Clarifies%20&%20Prioritizes.webp"
    },
    {
      title: "Get Your Schedule",
      description: "Receive a personalized, actionable schedule based on your energy and time.",
      icon: "/images-homepage/Get%20Your%20Schedule.webp"
    }
  ];

  return (
    <section className="bg-white py-24 px-6 sm:px-16 text-center flex flex-col items-center">
      <h2 className="text-[32px] sm:text-[36px] font-medium text-[#0A0A0A]">
        How It Works
      </h2>
      <p className="text-[16px] text-[#717182] mt-4 mb-16 max-w-3xl">
        Three simple steps to transform your thoughts into organized action
      </p>

      <div className="container mx-auto grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl">
        {steps.map((step, idx) => (
          <div 
            key={idx} 
            className="bg-white p-8 sm:p-10 rounded-2xl shadow-[0_4px_25px_rgb(0,0,0,0.03)] border border-gray-100 flex flex-col items-start text-left hover:shadow-[0_8px_30px_rgb(0,0,0,0.06)] transition-all"
          >
            <div className="mb-6 bg-purple-50 p-3 rounded-2xl inline-block">
              <img
                src={step.icon}
                alt={step.title}
                className="w-[32px] h-[32px] object-contain"
              />
            </div>
            <h3 className="text-[18px] font-semibold text-[#0A0A0A] mb-3">
              {step.title}
            </h3>
            <p className="text-[15px] text-[#717182] leading-relaxed">
              {step.description}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
