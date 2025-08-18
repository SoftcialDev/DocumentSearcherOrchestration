import React from "react";

interface IconButtonProps {
  iconSrc: string;         // path or URL to .svg
  alt?: string;            // accessible description
  onClick: () => void;
  size?: number;           // icon size in px (default: 20)
}

export default function IconButton({
  iconSrc,
  alt = "icon button",
  onClick,
  size = 20,
}: IconButtonProps) {
  const style: React.CSSProperties = {
    background: "none",
    border: "none",
    padding: 0,
    cursor: "pointer",
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
  };

  return (
    <button style={style} onClick={onClick}>
      <img
        src={iconSrc}
        alt={alt}
        style={{ width: size, height: size, display: "block" }}
      />
    </button>
  );
}
