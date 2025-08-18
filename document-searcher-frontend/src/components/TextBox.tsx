import React from "react";
import clsx from "clsx";

interface TextBoxProps {
  value: string;
  onChange: (newValue: string) => void;
  placeholder?: string;
  className?: string;          // NEW (optional)
}

export default function TextBox({
  value,
  onChange,
  placeholder = "Enter text…",
  className = "",              // default = empty
}: TextBoxProps) {
  return (
    <input
      type="text"
      value={value}
      placeholder={placeholder}
      onChange={(e) => onChange(e.target.value)}
      className={clsx(
        "w-full px-3 py-2 border border-gray-300 rounded-md text-base",
        "focus:outline-none focus:ring-2 focus:ring-blue-500",
        className
      )}
    />
  );
}
