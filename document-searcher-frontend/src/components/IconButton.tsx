import React from "react";

interface IconButtonProps {
  iconSrc: string;         // path or URL to .svg
  alt?: string;            // accessible description
  onClick: () => void;
  size?: number;           // icon size in px (default: 20)
  name?: string;
}

export default function IconButton({
  iconSrc,
  alt = "icon button",
  onClick,
  size = 20,
  name = ""
}: IconButtonProps) {
  const style: React.CSSProperties = {
    background: "none",
    border: "none",
    padding: "5px 10px",
    cursor: "pointer",
    display: "flex",
    // display: "inline-flex",
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
      <span style={{marginLeft: "10px"}}>{name}</span>
    </button>
  );
}
