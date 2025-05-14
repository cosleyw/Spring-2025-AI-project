import './Modal.css';

export default function Modal({ isOpen, children }) {
  if (!isOpen) return;

  return (
    <div className="modal-buffer">
      <div>{children}</div>
    </div>
  );
}
