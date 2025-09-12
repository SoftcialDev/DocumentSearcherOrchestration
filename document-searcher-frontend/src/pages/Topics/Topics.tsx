import { useEffect, useState } from "react";
import Button from "../../components/Button";
import ConfirmModal from "../../components/modals/ConfirmationModal";
import TopicCreateModal from "./TopicsCreateModal";
import SourcesModal from "./SourcesModal";
import poweredBySoftcial from "../../imgs/powered_by_softcial.png"
import appLogo from "../../imgs/app_logo.png"


interface Topic { name: string }

export default function Topics() {
  /* data */
  const [topics, setTopics] = useState<Topic[]>([]);
  const [refreshKey, setKey] = useState(0);

  /* confirmation modal state */
  const [confirmTopic, setConfirmTopic] = useState<string | null>(null);

  /* ---------- fetch topics list ---------- */
  useEffect(() => {
    fetch("/api/list-topics")
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
      const res = await fetch("/api/delete-topic", {
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
    <div className="min-h-screen">
      {/* <div className="flex justify-between pb-6" style={{width: "100%"}}>
        <img src={appLogo} width={"150px"} alt="" />
        <img src={poweredBySoftcial} width={"150px"} alt="" />
      </div> */}
      <div className="flex align-center items-center justify-center">
        <svg width="59" height="59" viewBox="0 0 59 59" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M49.1667 14.75H29.5L24.5834 9.83333H9.83335C7.12919 9.83333 4.94127 12.0458 4.94127 14.75L4.91669 44.25C4.91669 46.9542 7.12919 49.1667 9.83335 49.1667H49.1667C51.8709 49.1667 54.0834 46.9542 54.0834 44.25V19.6667C54.0834 16.9625 51.8709 14.75 49.1667 14.75ZM34.4167 39.3333H14.75V34.4167H34.4167V39.3333ZM44.25 29.5H14.75V24.5833H44.25V29.5Z" fill="#CCECF2"/>
        </svg>
        <h2 className="mb-4 text-4xl text-center font-bold uppercase" style={{color: "#CCECF2", margin: 0, marginLeft: "15px"}}>
          Topics
        </h2>
      </div>

      <TopicCreateModal onCreated={refresh} />

      {/* list */}
      <div className="flex flex-col gap-2 mt-6">
        <div className="flex items-center justify-between p-4 shadow-sm" style={{border: "0", background: "#024A59", borderRadius: "10px"}}>
            <span style={{color: "#ffffff"}} className="font-medium">Topic</span>
            <span style={{color: "#ffffff"}} className="font-medium">Actions</span>
          </div>
        {topics.map((t) => (
          <div
            key={t.name}
            className="flex items-center justify-between p-3 shadow-sm"
            style={{border: "0", borderBottom: "1px solid #ffffff"}}
          >
            <span style={{color: "#ffffff"}} className="font-medium">{t.name}</span>
            <div className="flex gap-2">
              <Button
                text="DELETE"
                onClick={() => askDelete(t.name)}
                type="CANCEL"
                icon="delete"
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
