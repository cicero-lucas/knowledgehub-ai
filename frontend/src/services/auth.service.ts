import { api } from "./api";
import type { TokenResponse, User } from "@/types";

export const authService = {
  async register(data: {
    email: string;
    full_name: string;
    password: string;
  }): Promise<User> {
    const res = await api.post<User>("/auth/register", data);
    return res.data;
  },

  async login(email: string, password: string): Promise<TokenResponse> {
    const res = await api.post<TokenResponse>("/auth/login", { email, password });
    return res.data;
  },

  async logout(): Promise<void> {
    await api.post("/auth/logout");
  },

  /**
   * Fetch the current user profile.
   * Accepts an optional token so it can be called right after login
   * before the token is stored in localStorage (avoids the interceptor race).
   */
  async getMe(token?: string): Promise<User> {
    const res = await api.get<User>("/users/me", {
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    });
    return res.data;
  },
};
