import { useState, useRef, useEffect } from "react";
import Button from "../../components/Button";
import Modal from "../../components/Modal";
import SharePointPicker from "./SharepointPicker";
import OneDrivePicker from "./OneDrivePicker";
import SourcesTable from "./SourcesTable";
import ConfirmationModal from "../../components/modals/ConfirmationModal";
import { useAlerts } from "../../providers/AlertsProvider"; 

interface Props {
  topicName: string;
}

interface Source {
  id: string;
  name: string;
  site: string;
  schedule: string;
}

interface Item { name: string }

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
    return { name: String(hour * 100 + minute) };
  });

  const open  = () => setIsOpen(true);
  const close = () => { setIsOpen(false); setShowMenu(false); };

  const { push } = useAlerts();

  const askSourceRemove = (name: string, id: string) => {
    setConfirm({ name, id });
  };

  const confirmRemove = async () => {
    if (!confirm) return;
    const { name, id } = confirm;
    try {
      const res = await fetch("http://localhost:5000/remove-source", {
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

    fetch(`http://localhost:5000/list-sources?topic=${encodeURIComponent(topicName)}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(r.statusText)))
      .then(setSources)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
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
      const res = await fetch("http://localhost:5000/update-source", {
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
      <Button text="Sources" onClick={open} type="ACCEPT" />

      <Modal isOpen={isOpen} onClose={close} className="max-w-4xl">
        <h3 className="text-xl font-semibold mb-4">
          Sources for &ldquo;{topicName}&rdquo;
        </h3>

        <div className="relative mb-4 flex justify-end">
          <Button text="Add" onClick={() => setShowMenu(!showMenu)} type="ACCEPT" />

        {showMenu && (
          <div
            ref={menuRef}
            className="absolute right-0 mt-1 flex flex-row bg-white border border-black border-[0.5px] rounded-md shadow-md z-10"
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
