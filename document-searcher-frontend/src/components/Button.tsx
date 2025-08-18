import React from "react";

type ButtonType = "ACCEPT" | "CANCEL";

interface ButtonProps {
  text: string;
  onClick: () => void;
  type: ButtonType;
}

export default function Button({ text, onClick, type }: ButtonProps) {
  const baseStyle: React.CSSProperties = {
    padding: "10px 20px",
    border: "none",
    borderRadius: "20px",
    color: "#fff",
    cursor: "pointer",
    margin: "5px",
  };

  const typeStyle: React.CSSProperties =
    type === "ACCEPT"
      ? { backgroundColor: "#007bff" } // blue
      : { backgroundColor: "#6c757d" }; // gray

  return (
    <button style={{ ...baseStyle, ...typeStyle }} onClick={onClick}>
      {text}
    </button>
  );
}
