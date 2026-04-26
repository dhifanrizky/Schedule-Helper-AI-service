"use client";

import { Inter } from "next/font/google";
import { Navbar } from "@/components/landing/Navbar";
import { Hero } from "@/components/landing/Hero";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { CTA } from "@/components/landing/CTA";

const inter = Inter({ subsets: ["latin"] });

/**
 * LANDING PAGE (ROOT)
 * Halaman utama aplikasi (Landing Page).
 */
export default function HomePage() {
  return (
    <div className={`min-h-screen bg-white ${inter.className}`}>
      {/* 1. Navigation Bar */}
      <Navbar />

      {/* 2. Hero Section & Main Features */}
      <Hero />

      {/* 3. Step-by-Step Guide */}
      <HowItWorks />

      {/* 4. Final Call to Action */}
      <CTA />
    </div>
  );
}
