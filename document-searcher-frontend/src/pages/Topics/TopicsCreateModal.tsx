import { useState } from "react";
import TextBox from "../../components/TextBox";
import Button  from "../../components/Button";
import Modal   from "../../components/Modal";
import { useAlerts } from "../../providers/AlertsProvider"; 
import { useAuth } from "../../providers/AuthProvider";

interface Props {
  onCreated: () => void;
}

export default function TopicCreateModal({ onCreated }: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [text, setText]     = useState("");

  const open  = () => setIsOpen(true);
  const close = () => setIsOpen(false);

  const { push } = useAlerts();
  const { apiFetch } = useAuth();

  const handleCreate = async () => {
    if (!text.trim()) return alert("Please enter a topic name");

    try {
      const res  = await apiFetch("/api/topics/create-topic", {
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
      } else {
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
        <Button onClick={open} text="ADD" type="ACCEPT"  icon="add"/>        
        {/* <Button onClick={open} text="DELETE" type="CANCEL"  icon="delete"/> */}
      </div>

      {/* modal */}
      <Modal isOpen={isOpen} onClose={close}>
        <div className="flex items-center justify-between mb-3">
          <div style={{ display: "flex", alignItems: "center" }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M20 6H12L10 4H4C2.9 4 2.01 4.9 2.01 6L2 18C2 19.1 2.9 20 4 20H20C21.1 20 22 19.1 22 18V8C22 6.9 21.1 6 20 6ZM14 16H6V14H14V16ZM18 12H6V10H18V12Z" fill="white"/>
              <circle cx="19" cy="18" r="5" fill="white"/>
              <path fill-rule="evenodd" clip-rule="evenodd" d="M15.6667 18C15.6667 16.159 17.1591 14.6667 19.0001 14.6667C20.8411 14.6667 22.3334 16.159 22.3334 18C22.3334 19.841 20.8411 21.3333 19.0001 21.3333C17.1591 21.3333 15.6667 19.841 15.6667 18ZM19.0001 15.3333C18.2928 15.3333 17.6146 15.6143 17.1145 16.1144C16.6144 16.6145 16.3334 17.2928 16.3334 18C16.3334 18.7072 16.6144 19.3855 17.1145 19.8856C17.6146 20.3857 18.2928 20.6667 19.0001 20.6667C19.7073 20.6667 20.3856 20.3857 20.8857 19.8856C21.3858 19.3855 21.6667 18.7072 21.6667 18C21.6667 17.2928 21.3858 16.6145 20.8857 16.1144C20.3856 15.6143 19.7073 15.3333 19.0001 15.3333Z" fill="#002A3E"/>
              <path fill-rule="evenodd" clip-rule="evenodd" d="M19.3332 16.3333C19.3332 16.2449 19.2981 16.1601 19.2356 16.0976C19.1731 16.0351 19.0883 16 18.9999 16C18.9115 16 18.8267 16.0351 18.7642 16.0976C18.7017 16.1601 18.6665 16.2449 18.6665 16.3333V17.6667H17.3332C17.2448 17.6667 17.16 17.7018 17.0975 17.7643C17.035 17.8268 16.9999 17.9116 16.9999 18C16.9999 18.0884 17.035 18.1732 17.0975 18.2357C17.16 18.2982 17.2448 18.3333 17.3332 18.3333H18.6665V19.6667C18.6665 19.7551 18.7017 19.8399 18.7642 19.9024C18.8267 19.9649 18.9115 20 18.9999 20C19.0883 20 19.1731 19.9649 19.2356 19.9024C19.2981 19.8399 19.3332 19.7551 19.3332 19.6667V18.3333H20.6665C20.7549 18.3333 20.8397 18.2982 20.9022 18.2357C20.9648 18.1732 20.9999 18.0884 20.9999 18C20.9999 17.9116 20.9648 17.8268 20.9022 17.7643C20.8397 17.7018 20.7549 17.6667 20.6665 17.6667H19.3332V16.3333Z" fill="#002A3E"/>
            </svg>

            <h2 className="text-lg font-semibold m-0 ml-1">New Topic(s)</h2>
          </div>

          <Button
            icon="none"
            onClick={close}
            text="X"
            type="CANCEL"
          />
        </div>

        <p className="text-sm mb-3" style={{color: "#CCECF2"}}>You can add multiple topics separated by comma​</p>

        <div className="flex flex-col gap-4 w-full">
          <TextBox
            value={text}
            onChange={setText}
            placeholder="New topic 1, New topic 2, ..."
            className="w-full"
          />

          <div className="flex justify-end gap-2">
            <Button text="CANCEL" onClick={close}  type="CANCEL" icon="cancel" />
            <Button text="CONFIRM" onClick={handleCreate} type="ACCEPT"  icon="confirm"/>
          </div>
        </div>
      </Modal>
    </>
  );
}
