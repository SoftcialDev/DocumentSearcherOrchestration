import { PublicClientApplication } from "@azure/msal-browser";
import { msalConfig, loginRequest } from "../../authConfig";

const msalInstance = new PublicClientApplication(msalConfig);

export default function LinkAccounts() {
  const handleLogin = async () => {
    try {
      await msalInstance.initialize();
      const result = await msalInstance.loginPopup(loginRequest);

      // Access token for Graph API
      const token = result.accessToken;

      alert("Connected to SharePoint/OneDrive!");

      // Store token for API calls
      sessionStorage.setItem("graphToken", token);
    } catch (error) {
      console.error(error);
      alert("Login failed");
    }
  };

  return <button onClick={handleLogin}>Link SharePoint / OneDrive</button>;
}
