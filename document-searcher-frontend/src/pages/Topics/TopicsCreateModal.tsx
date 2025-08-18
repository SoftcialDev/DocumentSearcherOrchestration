import { useState } from "react";
import TextBox from "../../components/TextBox";
import Button  from "../../components/Button";
import Modal   from "../../components/Modal";
import { useAlerts } from "../../providers/AlertsProvider"; 

interface Props {
  onCreated: () => void;
}

export default function TopicCreateModal({ onCreated }: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [text, setText]     = useState("");

  const open  = () => setIsOpen(true);
  const close = () => setIsOpen(false);

  const { push } = useAlerts();

  const handleCreate = async () => {
    if (!text.trim()) return alert("Please enter a topic name");

    try {
      const res  = await fetch("http://localhost:5000/create-topic", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic_name: text }),
      });
      const data = await res.json();

      if (data.status === "success") {
        setText("");
        close();
        onCreated();
        push({
          message: "SUCCESS: " + data.message,
          variant: "success",
          duration: 5000,
        })
      } else if (data.status === "error") {
        setText("");
        close();
        push({
          message: "ERROR: " + data.message,
          variant: "error",
          duration: 5000,
        })
      }
    } catch {
      push({
        message: "Error: Unable to create topic",
        variant: "error",
        duration: 5000,
      })
    }
  };

  return (
    <>
      {/* button that opens the modal */}
      <div className="flex justify-end w-full">
        <Button onClick={open} text="New Topic" type="ACCEPT" />
      </div>

      {/* modal */}
      <Modal isOpen={isOpen} onClose={close}>
        <div className="flex flex-col gap-4 w-full">
          <TextBox
            value={text}
            onChange={setText}
            placeholder="New Topic Name..."
            className="w-full"
          />

          <div className="flex justify-end gap-2">
            <Button text="Cancel" onClick={close}  type="CANCEL" />
            <Button text="Create" onClick={handleCreate} type="ACCEPT" />
          </div>
        </div>
      </Modal>
    </>
  );
}
