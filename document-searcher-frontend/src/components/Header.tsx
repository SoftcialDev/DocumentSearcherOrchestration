import { Link } from "react-router-dom";
import { useAuth } from "../providers/AuthProvider"; // adjust path if needed
import poweredBySoftcial from "../imgs/powered_by_softcial.png"
import appLogo from "../imgs/app_logo.png"

export default function Header() {
  const { account, login, logout } = useAuth();

  const navStyle = {
    padding: "20px",
    background: "#002A3E", // purple tone
    color: "white",
    display: "flex",
    justifyContent: account ? "space-between" : "flex-end",
    alignItems: "center",
  };
  const welcomeStyle = {
    padding: "10px",
    background: "#002231ff", // purple tone
    color: "white",
  };

  const linkStyle = {
    marginRight: "30px",
    color: "#ffffff", // light lavender
    textDecoration: "none",
  };

  if (!account) {
    return (
      <nav style={navStyle}>
        {/* <button
          style={{
            background: "#09CAC7",
            border: "none",
            padding: "6px 12px",
            borderRadius: "4px",
            cursor: "pointer",
            color: "#002A3E",
          }}
          onClick={login}
        >
          Log In
        </button> */}
      </nav>
    );
  }

  return (
    <div>
      <nav style={navStyle}>
        <img src={appLogo} width={"150px"} alt="" />        
        <div>
          <Link to="/home" style={linkStyle}>Home</Link>
          <Link to="/chat" style={linkStyle}>Chat</Link>
          <Link to="/topics" style={linkStyle}>Topics</Link>
          <button
            style={{
              background: "#09CAC7",
              border: "none",
              padding: "6px 12px",
              borderRadius: "4px",
              cursor: "pointer",
              color: "#002A3E",
            }}
            onClick={logout}
          >
            Log Out
          </button>
        </div>
        <img src={poweredBySoftcial} width={"150px"} alt="" />
      </nav>
      <div style={welcomeStyle}>
        <p style={{ textAlign: "center", width: "100%" }}>Welcome, {account.username}!</p>
      </div>      
    </div>
  );
}
