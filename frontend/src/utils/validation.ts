/**
 * UTILS: Validasi input form
 */

export const validateEmail = (val: string): string => {
  if (!val) return "";
  
  const atCount = (val.match(/@/g) || []).length;
  if (atCount !== 1) {
    return "An email address must contain a single @";
  }
  
  const domainPart = val.split("@")[1];
  if (
    !domainPart.includes(".") ||
    domainPart.split(".").pop()?.trim() === ""
  ) {
    return "Please ensure the email address ends with a valid domain (e.g. .com).";
  }
  
  return "";
};
