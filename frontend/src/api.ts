import axios from "axios";
import { getAlphaAPI } from "./generated/endpoints";
import { useAuthStore } from "./store/useAuthStore";

export const authAxios = axios.create();

authAxios.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

authAxios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = "/app/login";
    }
    return Promise.reject(error);
  },
);

export const api = getAlphaAPI(authAxios);
