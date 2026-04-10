import axios from "axios";
import { getAlphaAPI } from "./generated/endpoints";

export const authAxios = axios.create();

authAxios.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const api = getAlphaAPI(authAxios);
