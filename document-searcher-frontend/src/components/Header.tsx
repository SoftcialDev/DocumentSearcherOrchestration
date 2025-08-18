import { Link } from "react-router-dom";
import { useAuth } from "../providers/AuthProvider"; // adjust path if needed

export default function Header() {
  const { account, login, logout } = useAuth();

  const navStyle = {
    padding: "10px",
    background: "#6c4aa5", // purple tone
    color: "white",
    marginBottom: "20px",
    display: "flex",
    justifyContent: account ? "space-between" : "flex-end",
    alignItems: "center",
  };

  const linkStyle = {
    marginRight: "10px",
    color: "#e9d8fd", // light lavender
    textDecoration: "none",
  };

  if (!account) {
    return (
      <nav style={navStyle}>
        <button
          style={{
            background: "#b794f4",
            border: "none",
            padding: "6px 12px",
            borderRadius: "4px",
            cursor: "pointer",
            color: "#2d1b4e",
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
            background: "#b794f4",
            border: "none",
            padding: "6px 12px",
            borderRadius: "4px",
            cursor: "pointer",
            color: "#2d1b4e",
          }}
          onClick={logout}
        >
          Log Out
        </button>
      </div>
    </nav>
  );
}
