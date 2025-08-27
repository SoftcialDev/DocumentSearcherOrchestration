import React, { ReactNode } from "react";
import Button from "./Button";

interface CardProps {
  icon: ReactNode;
  title: string;
  description: string;
  buttonText: string;
  onButtonClick: () => void;
  buttonType: "ACCEPT" | "CANCEL";
}

export default function Card({ icon, title, description, buttonText, onButtonClick, buttonType }: CardProps) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "10% 80% 10%",
        alignItems: "center",
        padding: "15px",
        margin: "10px 0",
        border: "1px solid #ccc",
        borderRadius: "8px",
        width: "100%"
      }}
    >
      {/* Icon */}
      <div style={{ display: "flex", justifyContent: "center" }}>{icon}</div>

      {/* Title + Description */}
      <div style={{ display: "flex", flexDirection: "column", justifyContent: "center" }}>
        <h3 style={{ margin: "0 0 5px 0" }}>{title}</h3>
        <p style={{ margin: 0 }}>{description}</p>
      </div>

      {/* Button */}
      <div style={{ display: "flex", justifyContent: "center" }}>
        <Button text={buttonText} onClick={onButtonClick} type={buttonType}  icon="none"/>
      </div>
    </div>
  );
}
