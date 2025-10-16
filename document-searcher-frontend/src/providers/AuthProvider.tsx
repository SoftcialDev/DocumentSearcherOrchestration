import React, { createContext, useContext, ReactNode, useEffect } from "react";
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
  InteractionRequiredAuthError,
} from "@azure/msal-browser";

/** ---- configure your API scope (IMPORTANT) ----
 * Replace <API_APP_GUID> with your API app's Application (client) ID (GUID).
 * Your backend expects tokens targeted to this resource.
 */
const API_SCOPES = [`api://botidd8c01861-4bc1-45bc-8778-23691418878d/MyAccessScope`];

interface AuthContextShape {
  account:    { username: string } | null;
  login:      () => Promise<void>;
  logout:     () => Promise<void>;
  /** new: fetch an access token for your API */
  getApiToken: () => Promise<string>;
  /** new: fetch wrapper that auto-attaches the bearer token */
  apiFetch:   (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;
}

const AuthContext = createContext<AuthContextShape>({
  account: null,
  login: async () => {},
  logout: async () => {},
  getApiToken: async () => "",
  apiFetch: async () => new Response(null, { status: 500 }),
});

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const { instance, accounts } = useMsal();
  const isAuthenticated = useIsAuthenticated();

  // pick an active account once signed-in
  useEffect(() => {
    if (!instance.getActiveAccount() && accounts.length > 0) {
      instance.setActiveAccount(accounts[0]);
    }
  }, [accounts, instance]);

  const account = isAuthenticated
    ? instance.getActiveAccount() ?? accounts[0] ?? null
    : null;

  /** ---- login & logout helpers (kept as-is) ---- */
  const login = async () => {
    const request: PopupRequest = {
      // keep your existing Graph/SharePoint scopes
      scopes: ["User.Read", "Files.Read.All"],
    };
    const resp: AuthenticationResult = await instance.loginPopup(request);
    instance.setActiveAccount(resp.account);
  };

  const logout = async () => {
    const request: EndSessionPopupRequest = {
      account: instance.getActiveAccount() || undefined,
    };
    await instance.logoutPopup(request);
  };

  /** ---- new: acquire API token on demand (silent → popup fallback) ---- */
  const getApiToken = async (): Promise<string> => {
    let acc = instance.getActiveAccount() ?? accounts[0];
    if (!acc) {
      // Not signed in yet → interactive sign-in requesting API scope (will also get Graph consent if needed)
      const resp = await instance.loginPopup();
      instance.setActiveAccount(resp.account);
      acc = resp.account;
    }

    try {
      const res = await instance.acquireTokenSilent({ account: acc, scopes: API_SCOPES });
      return res.accessToken;
    } catch (err) {
      if (err instanceof InteractionRequiredAuthError) {
        const res = await instance.acquireTokenPopup({ account: acc, scopes: API_SCOPES });
        return res.accessToken;
      }
      throw err;
    }
  };

  /** ---- new: token-aware fetch wrapper ---- */
  const apiFetch: AuthContextShape["apiFetch"] = async (input, init = {}) => {
    const token = await getApiToken();
    const headers = new Headers(init.headers || {});
    headers.set("Authorization", `Bearer ${token}`);
    // set content-type automatically for JSON bodies
    const bodyIsFormData = typeof FormData !== "undefined" && init.body instanceof FormData;
    if (!headers.has("Content-Type") && !bodyIsFormData) {
      headers.set("Content-Type", "application/json");
    }
    return fetch(input, { ...init, headers });
  };

  return (
    <AuthContext.Provider value={{ account, login, logout, getApiToken, apiFetch }}>
      {/* Render app only when authenticated; show a simple sign-in fallback otherwise */}
      <AuthenticatedTemplate>{children}</AuthenticatedTemplate>
      <UnauthenticatedTemplate>{children}</UnauthenticatedTemplate>
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
