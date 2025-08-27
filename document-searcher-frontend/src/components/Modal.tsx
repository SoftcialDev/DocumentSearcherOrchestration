import React, { ReactNode } from "react";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  children: ReactNode;
  className?: string; // optional extra classes for the panel
}

export default function Modal({
  isOpen,
  onClose,
  children,
  className = "max-w-2xl", // wider default (was max-w-md)
}: ModalProps) {
  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      aria-modal="true"
      role="dialog"      
    >
      {/* backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      {/* panel */}
      <div 
        className={`relative w-full rounded-lg bg-white p-6 shadow-lg ${className}`} 
        style={{background: "#002A3E", border: "2px solid #ffffff", color: "#ffffff"}}
      >
        {children}
      </div>
    </div>
  );
}
