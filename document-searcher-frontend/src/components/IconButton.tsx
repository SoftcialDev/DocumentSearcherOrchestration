import React from "react";

interface IconButtonProps {
  iconSrc?: string;         // path or URL to .svg
  iconSvg?: string;         // html code of the icon
  alt?: string;            // accessible description
  onClick: () => void;
  size?: number;           // icon size in px (default: 20)
  name?: string;
}

export default function IconButton({
  iconSrc,
  iconSvg,
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

  // Build the icon element depending on what was provided
  let iconEl: React.ReactNode;
  if (iconSvg) {
    // Render raw SVG markup; the wrapper controls sizing
    iconEl = (
      <span
        aria-hidden
        style={{ width: size, height: size, lineHeight: 0, display: "block" }}
        dangerouslySetInnerHTML={{ __html: iconSvg }}
      />
    );
  } else if (iconSrc) {
    iconEl = (
      <img
        src={iconSrc}
        alt=""                  // decorative, label goes on the button
        style={{ width: size, height: size, display: "block" }}
        aria-hidden
      />
    );
  } else {
    iconEl = null;
  }

  return (
    <button style={style} onClick={onClick} aria-label={alt}>
      {iconEl}
      {name ? <span style={{ marginLeft: "10px" }}>{name}</span> : null}
    </button>
  );
}
