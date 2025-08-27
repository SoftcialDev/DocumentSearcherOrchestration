import { Link } from "react-router-dom";
import { useAuth } from "../providers/AuthProvider"; // adjust path if needed

export default function Header() {
  const { account, login, logout } = useAuth();

  const navStyle = {
    padding: "10px",
    background: "#002A3E", // purple tone
    color: "white",
    display: "flex",
    justifyContent: account ? "space-between" : "flex-end",
    alignItems: "center",
  };

  const linkStyle = {
    marginRight: "10px",
    color: "#ffffff", // light lavender
    textDecoration: "none",
  };

  if (!account) {
    return (
      <nav style={navStyle}>
        <button
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
        </button>
      </nav>
    );
  }

  return (
    <nav style={navStyle}>
      <div>
        <Link to="/" style={linkStyle}>Home</Link>
        <Link to="/chat" style={linkStyle}>Chat</Link>
        <Link to="/topics" style={linkStyle}>Topics</Link>
      </div>
      <div>
        <span style={{ marginRight: "10px" }}>{account.username}</span>
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
    </nav>
  );
}
