import './SchedulePreview.css';
import SemesterPreview from './SemesterPreview';

export default function SchedulePreview({ schedule }) {
  return (
    <div className="schedule-preview">
      {schedule.map((semester, idx) => (
        <SemesterPreview courses={semester} id={idx + 1} />
      ))}
    </div>
  );
}
