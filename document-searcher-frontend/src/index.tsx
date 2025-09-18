import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import { AuthProvider } from './providers/AuthProvider';
import { PublicClientApplication } from "@azure/msal-browser";
import { MsalProvider } from "@azure/msal-react";
import { AlertsProvider } from './providers/AlertsProvider';

const msalConfig = {
  auth: {
    clientId: "d8c01861-4bc1-45bc-8778-23691418878d",
    authority: "https://login.microsoftonline.com/a080ad22-43aa-4696-b40b-9b68b702c9f3",
    redirectUri: "http://localhost:3000",
  },
  cache: { cacheLocation: "sessionStorage" }
};

const pca = new PublicClientApplication(msalConfig);

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);
root.render(
  <React.StrictMode>
    <MsalProvider instance={pca}>
      <AlertsProvider>
        <AuthProvider>
          <App />
        </AuthProvider>
      </AlertsProvider>
    </MsalProvider>
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
