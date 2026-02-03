import { useAuth } from "../providers/AuthProvider";

export default function Home() {
  const { account } = useAuth();
  const returnTo = encodeURIComponent(window.location.href);
  const user_hint = encodeURIComponent(account?.username || "");

  return(
    <button onClick={() => window.location.href = `http://localhost:5000/api/google/oauth/start?return_to=${returnTo}&user_hint=${user_hint}`}>
      Connect Google Drive
    </button>
  );
}
