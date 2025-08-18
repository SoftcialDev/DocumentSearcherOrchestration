import Modal from "../Modal";
import Button from "../Button";

interface ConfirmModalProps {
  isOpen: boolean;
  title?: string;
  message: string;
  onCancel: () => void;
  onAccept: () => void;
  className?: string;
}

export default function ConfirmModal({
  isOpen,
  title = "Are you sure?",
  message,
  onCancel,
  onAccept,
  className,
}: ConfirmModalProps) {
  return (
    <Modal isOpen={isOpen} onClose={onCancel} className={className}>
      <h2 className="text-lg font-semibold mb-3">{title}</h2>
      <p className="text-sm text-gray-700">{message}</p>

      <div className="mt-6 flex justify-end gap-3">
        <Button text="Cancel" onClick={onCancel} type="CANCEL" />
        <Button text="Accept" onClick={onAccept} type="ACCEPT" />
      </div>
    </Modal>
  );
}
