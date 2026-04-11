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

export const api = getAlphaAPI(authAxios);
