import Modal from './Modal';
import ScheduleGenerator from './ScheduleGenerator';

export default function SettingsModal({ isOpen, onClose }) {
  return (
    <Modal isOpen={isOpen}>
      <ScheduleGenerator
        title="Update Settings (Changes here will be saved, but won't show up until regenerating)"
        showGenerate={false}
        handleClose={onClose}
      ></ScheduleGenerator>
    </Modal>
  );
}
