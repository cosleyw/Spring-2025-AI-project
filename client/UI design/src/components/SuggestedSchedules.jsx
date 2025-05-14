import { useMemo, useState } from 'react';
import { post_review } from '../api';
import Modal from './Modal';
import SchedulePreview from './SchedulePreview';
import './SuggestedSchedules.css';

export default function SuggestedSchedules({ isOpen, schedules, onClose }) {
  const [feedback, setFeedback] = useState('');
  const [hasGivenFeedback, setHasGivenFeedback] = useState(false);

  const handleOnClose = (e) => {
    setHasGivenFeedback(false);
    setFeedback('');
    onClose(e);
  };

  const handleSubmit = (e) => {
    post_review(feedback);
    setHasGivenFeedback(true);

    e.preventDefault();
    return false;
  };

  const scheduleHTML = useMemo(
    () => schedules.map((schedule) => <SchedulePreview schedule={schedule}></SchedulePreview>),
    [schedules]
  );

  return (
    <Modal isOpen={isOpen}>
      <div className="suggested-schedules">
        <div className="suggested-schedules-bar">
          <h2>{schedules.length === 0 ? 'No Similar Schedules Found' : 'Similar Schedules:'}</h2>
          {!hasGivenFeedback ? (
            <form className="suggested-feedback-form" onSubmit={handleSubmit}>
              <input
                className="suggested-feedback-input"
                type="text"
                placeholder="Type a review of your schedule..."
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
              />
              <div className="suggested-feedback-form-button">
                <button type="submit">Submit Feedback</button>
              </div>
            </form>
          ) : (
            <span>Thanks for the feedback!</span>
          )}
          <button className="suggested-schedules-close-button" onClick={handleOnClose}>
            Close
          </button>
        </div>
        <div className="suggested-schedules-container">{scheduleHTML}</div>
      </div>
    </Modal>
  );
}
