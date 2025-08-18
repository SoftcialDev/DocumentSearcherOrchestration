import { ReactNode } from "react";
import { useAuth } from "../providers/AuthProvider"; // adjust path if needed

interface ContentWrapperProps {
  children: ReactNode;
}

export default function ContentWrapper({ children }: ContentWrapperProps) {
   const { account } = useAuth();

  if (!account) {
    return (
      <div style={{ margin: "20px", textAlign: "center" }}>
        <p>Please log in to continue.</p>
      </div>
    );
  }

  return <div style={{ margin: "20px" }}>{children}</div>;
}
