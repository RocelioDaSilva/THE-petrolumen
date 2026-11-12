import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";
import {
  AuthUser,
  fetchCurrentUser,
  registerAccount,
  requestAuthToken,
  setApiAuthToken,
} from "@/lib/api";
import AuthDialog from "@/components/AuthDialog";

interface AuthContextValue {
  user: AuthUser | null;
  isAuthDialogOpen: boolean;
  openAuthDialog: () => void;
  closeAuthDialog: () => void;
  login: (username: string, password: string) => Promise<void>;
  register: (input: {
    username: string;
    email: string;
    password: string;
    full_name?: string;
  }) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isAuthDialogOpen, setAuthDialogOpen] = useState(false);

  const establishSession = useCallback(async (username: string, password: string) => {
    const token = await requestAuthToken({ username, password });
    setApiAuthToken(token.access_token);
    try {
      setUser(await fetchCurrentUser());
      setAuthDialogOpen(false);
    } catch (error) {
      setApiAuthToken(null);
      throw error;
    }
  }, []);

  const login = useCallback(
    async (username: string, password: string) => {
      await establishSession(username, password);
    },
    [establishSession],
  );

  const register = useCallback(
    async (input: {
      username: string;
      email: string;
      password: string;
      full_name?: string;
    }) => {
      await registerAccount(input);
      await establishSession(input.username, input.password);
    },
    [establishSession],
  );

  const logout = useCallback(() => {
    setApiAuthToken(null);
    setUser(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthDialogOpen,
      openAuthDialog: () => setAuthDialogOpen(true),
      closeAuthDialog: () => setAuthDialogOpen(false),
      login,
      register,
      logout,
    }),
    [user, isAuthDialogOpen, login, register, logout],
  );

  return (
    <AuthContext.Provider value={value}>
      {children}
      <AuthDialog
        isOpen={isAuthDialogOpen}
        onClose={() => setAuthDialogOpen(false)}
        onLogin={login}
        onRegister={register}
      />
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside an <AuthProvider>.");
  }
  return context;
}
