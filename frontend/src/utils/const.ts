export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000/api";

export const getAppToken = () => {
	if (typeof window === "undefined") return null;
	return sessionStorage.getItem("app_token");
};