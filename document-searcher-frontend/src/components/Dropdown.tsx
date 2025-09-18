import { useEffect, useState } from "react";

interface Item {
  name: string;
  display: string;
}

interface DropdownProps {
  source: string | Item[];       // URL or list
  defaultValue?: string;         // initial selected value (e.g., "0630")
  onChange?: (value: string) => void; // callback
}

export default function Dropdown({
  source,
  defaultValue = "",
  onChange,
}: DropdownProps) {
  const [items, setItems] = useState<Item[]>([]);
  const [selected, setSelected] = useState<string>("");

  // Load items from URL or use given array
  useEffect(() => {
    if (typeof source === "string") {
      fetch(source)
        .then((res) => res.json())
        .then((data: Item[]) => setItems(data))
        .catch((err) => console.error("Failed to load data:", err));
    } else if (Array.isArray(source)) {
      setItems(source);
    }
  }, [source]);

  // Sync defaultValue to internal state
  useEffect(() => {
    setSelected(defaultValue ?? "");
  }, [defaultValue]);

  // Local change handler: update state and notify parent
  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const v = e.target.value;
    setSelected(v);
    onChange?.(v);
  };

  return (
    <div>
      <select id="dropdown" value={selected} onChange={handleChange} style={{color: "#ffffff", background: "#024A59", borderRadius: "5px"}}>
        {items.map((item, index) => (
          <option key={index} value={item.name}>
            {item.display}
          </option>
        ))}
      </select>
    </div>
  );
}
