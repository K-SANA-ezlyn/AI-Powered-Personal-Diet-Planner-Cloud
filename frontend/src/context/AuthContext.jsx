import { createContext, useContext, useState } from "react";
import { authService } from "../services/authService";

/**
 * context/AuthContext.jsx — holds the JWT + current user for the SPA.
 * The token lives in localStorage so a page refresh keeps you logged in
 * (simple demo choice; production apps often prefer refresh tokens —
 * see docs/security.md).
 */
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("dp_user") || "null");
    } catch {
      return null;
    }
  });

  const applySession = ({ access_token, user }) => {
    localStorage.setItem("dp_token", access_token);
    localStorage.setItem("dp_user", JSON.stringify(user));
    setUser(user);
  };

  const login = async (email, password) => {
    applySession(await authService.login({ email, password }));
  };

  const register = async (name, email, password) => {
    applySession(await authService.register({ name, email, password }));
  };

  const logout = async () => {
    try {
      await authService.logout();
    } catch {
      /* stateless logout — ignore server errors */
    }
    localStorage.removeItem("dp_token");
    localStorage.removeItem("dp_user");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
