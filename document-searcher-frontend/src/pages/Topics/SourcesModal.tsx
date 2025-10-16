import { useState, useRef, useEffect } from "react";
import Button from "../../components/Button";
import Modal from "../../components/Modal";
import SharePointPicker from "./SharepointPicker";
import OneDrivePicker from "./OneDrivePicker";
import SourcesTable from "./SourcesTable";
import ConfirmationModal from "../../components/modals/ConfirmationModal";
import { useAlerts } from "../../providers/AlertsProvider"; 
import { useAuth } from "../../providers/AuthProvider";
import IconButton from "../../components/IconButton";

interface Props {
  topicName: string;
}

interface Source {
  id: string;
  name: string;
  site: string;
  schedule: string;
}

interface Item {
  name: string;
  display: string;
}

export default function SourcesModal({ topicName }: Props) {
  const [isOpen, setIsOpen]   = useState(false);
  const [showMenu, setShowMenu] = useState(false);

  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  const [confirm, setConfirm] = useState<{ name: string; id: string } | null>(null);

  const menuRef = useRef<HTMLDivElement | null>(null);

  const hours: Item[] = Array.from({ length: 48 }, (_, i) => {
    const hour = Math.floor(i / 2);
    const minute = i % 2 ? 30 : 0;

    // value without colon (same as before)
    const value = String(hour * 100 + minute);

    // pretty label  -> e.g. "1:00", "12:30", "18:00"
    const display = `${hour}:${minute.toString().padStart(2, "0")}`;

    return { name: value, display };
  });
  const open  = () => setIsOpen(true);
  const close = () => { setIsOpen(false); setShowMenu(false); };

  const { push } = useAlerts();
  const { apiFetch } = useAuth();

  const askSourceRemove = (name: string, id: string) => {
    setConfirm({ name, id });
  };

  const confirmRemove = async () => {
    if (!confirm) return;
    const { name, id } = confirm;
    try {
      const res = await apiFetch("/api/remove-source", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic_name: topicName,
          source_id: id,
        }),
      });
      if (!res.ok) {
        const msg = await res.text().catch(() => "");
        throw new Error(msg || `HTTP ${res.status}`);
      }
      push({
        message: "Success: Source removed",
        variant: "success",
        duration: 5000,
      })
      setSources((prev) => prev.filter((s) => s.id !== id));
    } catch (err) {
      push({
        message: "Error: Could not remove source: " + err,
        variant: "error",
        duration: 5000,
      })
    } finally {
      setConfirm(null);
    }
  };

  const cancelRemove = () => setConfirm(null);

  useEffect(() => {
    if (!showMenu) return;
    const handleClick = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowMenu(false);
      }
    };
    window.addEventListener("mousedown", handleClick);
    return () => window.removeEventListener("mousedown", handleClick);
  }, [showMenu]);

  const loadSources = (fromRefresh: boolean) => {
    setLoading(true);
    setError(null);

    if (fromRefresh){
      push({
        message: "Success: Source added",
        variant: "success",
        duration: 5000,
      });
    }

    apiFetch(`/api/list-sources?topic=${encodeURIComponent(topicName)}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(r.statusText)))
      .then(setSources)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  };

  const manualUpload = () => {
    const input = document.createElement("input");
    input.type = "file";
    // limit to PDF & DOCX (include MIME + extensions for best browser coverage)
    input.accept = [
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      ".pdf",
      ".docx",
    ].join(",");

    input.onchange = async () => {
      const file = input.files?.[0];
      if (!file) return;

      const isPdf = file.name.toLowerCase().endsWith(".pdf");
      const isDocx = file.name.toLowerCase().endsWith(".docx");
      if (!isPdf && !isDocx) {
        push({
          message: "Error: File format not allowed",
          variant: "error",
          duration: 5000,
        });
        return;
      }

      try {
        const form = new FormData();
        form.append("file", file, file.name);
        form.append("topic", topicName);

        const res = await apiFetch("/api/upload-source", {
          method: "POST",
          body: form,
        });

        if (res.ok) {
          loadSources(true);
        }
      } catch (err) {}
    };

    // trigger it
    input.click();
  };

  useEffect(() => {
    if (!isOpen) return;
    loadSources(false);
  }, [isOpen, topicName]);

  const handleScheduleChange = async (sourceId: string, newSchedule: string) => {
    const previous = sources;
    setSources((prev) =>
      prev.map((s) => (s.id === sourceId ? { ...s, schedule: newSchedule } : s))
    );

    try {
      const res = await apiFetch("/api/update-source", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          topic: topicName,
          id: sourceId,
          schedule: newSchedule,
        }),
      });
      if (!res.ok) {
        const msg = await res.text().catch(() => "");
        throw new Error(msg || `HTTP ${res.status}`);
      }
      push({
        message: "Success: Schedule updated for selected source",
        variant: "success",
        duration: 5000,
      })
    } catch (err) {
      push({
        message: "Error: " + err,
        variant: "error",
        duration: 5000,
      })
      setSources(previous);
    }
  };

  return (
    <>
      <Button text="Sources" onClick={open} type="ACCEPT"  icon="sources"/>

      <Modal isOpen={isOpen} onClose={close} className="max-w-4xl">
        <div style={{display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1rem" }}>
            <div style={{ display: "flex", alignItems: "center" }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none"
                  xmlns="http://www.w3.org/2000/svg">
                <path d="M18.8213 3.17773C19.5159 3.49128 20 4.18841 20 5V21C20 22.1046 19.1046 23 18 23H8C7.18841 23 6.49128 22.5159 6.17773 21.8213C6.42879 21.9348 6.70656 22 7 22H17C18.1046 22 19 21.1046 19 20V4C19 3.70656 18.9348 3.42879 18.8213 3.17773Z" fill="white"/>
                <path d="M12 11.5C12.2761 11.5 12.5 11.7239 12.5 12C12.5 12.2761 12.2761 12.5 12 12.5H8C7.72386 12.5 7.5 12.2761 7.5 12C7.5 11.7239 7.72386 11.5 8 11.5H12Z" fill="white"/>
                <path d="M16 8.5C16.2761 8.5 16.5 8.72386 16.5 9C16.5 9.27614 16.2761 9.5 16 9.5H8C7.72386 9.5 7.5 9.27614 7.5 9C7.5 8.72386 7.72386 8.5 8 8.5H16Z" fill="white"/>
                <path d="M16 5.5C16.2761 5.5 16.5 5.72386 16.5 6C16.5 6.27614 16.2761 6.5 16 6.5H8C7.72386 6.5 7.5 6.27614 7.5 6C7.5 5.72386 7.72386 5.5 8 5.5H16Z" fill="white"/>
                <path fillRule="evenodd" clipRule="evenodd" d="M16 1C17.1046 1 18 1.89543 18 3V19C18 20.1046 17.1046 21 16 21H6C4.89543 21 4 20.1046 4 19V3C4 1.89543 4.89543 1 6 1H16ZM7 10.5C6.72386 10.5 6.5 10.7239 6.5 11C6.5 11.2761 6.72386 11.5 7 11.5H11C11.2761 11.5 11.5 11.2761 11.5 11C11.5 10.7239 11.2761 10.5 11 10.5H7ZM7 7.5C6.72386 7.5 6.5 7.72386 6.5 8C6.5 8.27614 6.72386 8.5 7 8.5H15C15.2761 8.5 15.5 8.27614 15.5 8C15.5 7.72386 15.2761 7.5 15 7.5H7ZM7 4.5C6.72386 4.5 6.5 4.72386 6.5 5C6.5 5.27614 6.72386 5.5 7 5.5H15C15.2761 5.5 15.5 5.27614 15.5 5C15.5 4.72386 15.2761 4.5 15 4.5H7Z" fill="white"/>
              </svg>

              <h3 className="text-xl font-semibold mb-4"
                  style={{ margin: 0, paddingLeft: "5px" }}>
                Sources - {topicName}
              </h3>
            </div>

          <Button
            icon="none"
            onClick={close}
            text="X"
            type="CANCEL"
          />
        </div>

        <div className="relative mb-4 flex justify-end">
          <Button text="ADD" onClick={() => setShowMenu(!showMenu)} type="ACCEPT"  icon="add"/>

        {showMenu && (
          <div
            ref={menuRef}
            className="absolute right-0 mt-1 flex bg-white border border-black border-[0.5px] rounded-md shadow-md z-10" style={{flexDirection: "column", background: "#024A59", border: "2px solid #ffffff"}}
          >
            <div className="p-1">
              <SharePointPicker 
                topicName={topicName} 
                onPicked={()=>{loadSources(true);}}
              />
            </div>
            <div className="p-1">
              <OneDrivePicker 
                topicName={topicName} 
                onPicked={()=>{loadSources(true);}}
              />
            </div>
            <div className="p-1">
              <IconButton
                iconSvg='<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M19.41 7.41L14.58 2.58C14.21 2.21 13.7 2 13.17 2H6C4.9 2 4.01 2.9 4.01 4L4 20C4 21.1 4.89 22 5.99 22H18C19.1 22 20 21.1 20 20V8.83C20 8.3 19.79 7.79 19.41 7.41ZM14.8 15H13V18C13 18.55 12.55 19 12 19C11.45 19 11 18.55 11 18V15H9.21C8.76 15 8.54 14.46 8.86 14.15L11.66 11.36C11.86 11.17 12.17 11.17 12.37 11.36L15.16 14.15C15.46 14.46 15.24 15 14.8 15ZM14 9C13.45 9 13 8.55 13 8V3.5L18.5 9H14Z" fill="white"/></svg>'
                alt="Add topic"
                size={24}
                onClick={()=>{manualUpload();}}
                name="Upload file"
              />
            </div>
          </div>
        )}
        </div>
        <SourcesTable
          loading={loading}
          error={error}
          sources={sources}
          hours={hours}
          onScheduleChange={handleScheduleChange}
          onRemove={askSourceRemove}
        />
      </Modal>
      {confirm && (
        <ConfirmationModal
          isOpen={true}
          title={`Delete source '${confirm.name}'?`}
          message="This action cannot be undone."
          onAccept={confirmRemove}
          onCancel={cancelRemove}
          className="max-w-md"
        />
      )}
    </>
  );
}
