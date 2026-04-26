interface ProfileFieldProps {
  label: string;
  value: string;
  icon: string;
  isLoading?: boolean;
}

/**
 * Komponen untuk menampilkan satu field informasi di halaman profil (Versi List).
 */
export function ProfileField({ label, value, icon, isLoading }: ProfileFieldProps) {
  return (
    <div className="border border-[#E5E7EB] rounded-[12px] p-5 flex flex-col gap-1.5 w-full">
      <div className="flex items-center gap-2.5 text-[#717182]">
        <img src={icon} alt={label} className="w-[18px] h-[18px]" />
        <span className="text-[14px]">{label}</span>
      </div>
      {isLoading ? (
        <div className="w-32 h-5 bg-gray-200 rounded animate-pulse ml-7"></div>
      ) : (
        <p className="text-[15px] font-medium text-[#0A0A0A] ml-7">
          {value || "Not provided"}
        </p>
      )}
    </div>
  );
}
