import { useEffect, useState } from "react";
import Button from "../../components/Button";
import ConfirmModal from "../../components/modals/ConfirmationModal";
import TopicCreateModal from "./TopicsCreateModal";
import SourcesModal from "./SourcesModal";


interface Topic { name: string }

export default function Topics() {
  /* data */
  const [topics, setTopics] = useState<Topic[]>([]);
  const [refreshKey, setKey] = useState(0);

  /* confirmation modal state */
  const [confirmTopic, setConfirmTopic] = useState<string | null>(null);

  /* ---------- fetch topics list ---------- */
  useEffect(() => {
    fetch("http://localhost:5000/list-topics")
      .then((r) => r.json())
      .then(setTopics)
      .catch((err) => console.error("Error fetching topics:", err));
  }, [refreshKey]);

  const refresh = () => setKey((k) => k + 1);

  /* ---------- open confirm dialog ---------- */
  const askDelete = (name: string) => setConfirmTopic(name);

  /* ---------- accept deletion ---------- */
  const confirmDelete = async () => {
    if (!confirmTopic) return;

    try {
      const res = await fetch("http://localhost:5000/delete-topic", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic_name: confirmTopic }),
      });
      const data = await res.json();
      if (data.status === "success") refresh();
      else alert(`${data.status.toUpperCase()}: ${data.message}`);
    } catch {
      alert("Error: Unable to delete topic");
    } finally {
      setConfirmTopic(null); // close modal
    }
  };

  /* ---------- cancel deletion ---------- */
  const cancelDelete = () => setConfirmTopic(null);

  return (
    <div className="min-h-screen bg-purple-50 text-purple-900 p-6">
      <h2 className="mb-4 text-4xl text-center font-bold text-purple-800">
        Topics
      </h2>

      <TopicCreateModal onCreated={refresh} />

      {/* list */}
      <div className="flex flex-col gap-2 mt-6">
        {topics.map((t) => (
          <div
            key={t.name}
            className="flex items-center justify-between p-3 border border-purple-300 bg-white/60 rounded-md shadow-sm"
          >
            <span className="font-medium">{t.name}</span>
            <div className="flex gap-2">
              <Button
                text="Delete"
                onClick={() => askDelete(t.name)}
                type="CANCEL"
              />
              <SourcesModal
                topicName={t.name}
              />
            </div>
          </div>
        ))}
      </div>

      {/* confirmation modal */}
      {confirmTopic && (
        <ConfirmModal
          isOpen={true}
          title={`Delete topic '${confirmTopic}'?`}
          message="This action cannot be undone."
          onAccept={confirmDelete}
          onCancel={cancelDelete}
          className="max-w-md bg-purple-100 text-purple-900"
        />
      )}
    </div>
  );
}
