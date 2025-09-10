import { ReactNode } from "react";
import { useAuth } from "../providers/AuthProvider"; // adjust path if needed
import poweredBySoftcial from "../imgs/powered_by_softcial.png"
import appLogo from "../imgs/app_logo.png"

interface ContentWrapperProps {
  children: ReactNode;
}

export default function ContentWrapper({ children }: ContentWrapperProps) {
   const { account, login, logout } = useAuth();

  if (!account) {
    return (
      <div style={{ margin: "20px", textAlign: "center", color: "#FFFFFF", height: "89.2svh", display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center" }}>
        <h1 style={{position: "absolute", top: "15svh", fontSize: "2em", fontWeight: "700"}}>DOCUMENT SEARCHER</h1>
        <p>Please log in to continue.</p>
        <button
          style={{
            background: "#09CAC7",
            border: "none",
            padding: "6px 12px",
            borderRadius: "4px",
            cursor: "pointer",
            color: "#002A3E",
            width: "fit-content",
            margin: "10px auto"
          }}
          onClick={login}
        >
          Log In
        </button>
        <img style={{position: "absolute", bottom: "5svh"}} src={poweredBySoftcial} width={"150px"} alt="" /> 
      </div>
    );
  }

  return <div style={{ margin: "20px" }}>{children}</div>;
}
