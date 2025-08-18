import React, { createContext, useContext, ReactNode } from "react";
import {
  useMsal,
  useIsAuthenticated,
  AuthenticatedTemplate,
  UnauthenticatedTemplate,
} from "@azure/msal-react";
import {
  PopupRequest,
  EndSessionPopupRequest,
  AuthenticationResult,
} from "@azure/msal-browser";

/** ---- shape that Header expects ---- */
interface AuthContextShape {
  account:    { username: string } | null;
  login:      () => Promise<void>;
  logout:     () => Promise<void>;
}

const AuthContext = createContext<AuthContextShape>({
  account: null,
  login: async () => {},
  logout: async () => {},
});

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const { instance, accounts } = useMsal();
  const isAuthenticated = useIsAuthenticated();

  /** helper to pick the active account */
  const account =
    isAuthenticated ? instance.getActiveAccount() ?? accounts[0] ?? null : null;

  /** ---- login & logout helpers ---- */
  const login = async () => {
    const request: PopupRequest = {
      scopes: ["User.Read", "Files.Read.All"], // add your scopes here
    };
    const resp: AuthenticationResult = await instance.loginPopup(request);
    instance.setActiveAccount(resp.account);   // keep it the default
  };

  const logout = async () => {
    const request: EndSessionPopupRequest = {
      account: instance.getActiveAccount() || undefined,
    };
    await instance.logoutPopup(request);
  };

  return (
    <AuthContext.Provider value={{ account, login, logout }}>
      {/* optional templates if you used them elsewhere */}
      <AuthenticatedTemplate>{children}</AuthenticatedTemplate>
      <UnauthenticatedTemplate>{children}</UnauthenticatedTemplate>
    </AuthContext.Provider>
  );
};

/** simple hook your components already use */
export const useAuth = () => useContext(AuthContext);
