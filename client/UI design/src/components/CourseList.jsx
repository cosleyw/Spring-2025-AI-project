import { Droppable } from '@hello-pangea/dnd';
import { useEffect, useMemo, useState } from 'react';
import { generate_schedule } from '../api';
import { useConfig } from '../context/GeneratorConfigContext';
import { useSchedule } from '../context/ScheduleContext';
import CourseDisplayList from './CourseDisplayList';
import './CourseList.css';
import TrashCan from './TrashCan';

export default function CourseList({ courses, onSelectCourse }) {
  const [search, setSearch] = useState('');
  const { schedule, setNewSchedule } = useSchedule();
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(false);
  const { form } = useConfig();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      let desired_courses = {};
      // Load the new, session-specific desired courses
      schedule.map((semester, i) =>
        semester['courses']
          .filter((course) => course.hasOwnProperty('desired'))
          .forEach((course) => (desired_courses[course['id']] = `${course['id']}@${i + 1}`))
      );
      // Load the settings desired courses
      form.desired_ids.forEach((id) => {
        if (!(id in desired_courses)) {
          desired_courses[id] = id;
        }
      });
      const raw = await generate_schedule({ ...form, desired_ids: Object.values(desired_courses) });
      setNewSchedule(raw, form.start_year, form.start_term, courses);
    } catch (err) {
      console.error(err);
      alert('Failed to generate schedule: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // If search changes, reset page number
  useEffect(() => setPage(0), [search]);

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    let unscheduledCourses = courses.filter(
      (c) =>
        !form.transfer_ids.includes(c.id) &&
        !form.block_ids.includes(c.id) &&
        !schedule
          .map((sem) => sem['courses'])
          .flat()
          .map((schedule_course) => schedule_course['id'])
          .includes(c.id)
    );
    if (!q) return unscheduledCourses;
    return unscheduledCourses.filter((c) => c.code.toLowerCase().includes(q) || c.name.toLowerCase().includes(q));
  }, [search, courses, schedule, form]);

  return (
    <div className="left-panel course-list-container">
      {/* — fixed header — */}
      <TrashCan />
      <div className="course-list-header">
        <button className="regenerate-button" disabled={loading} onClick={handleSubmit}>
          {loading ? 'Regenerating…' : 'Regenerate From Here'}
        </button>
        <input
          className="course-search"
          type="text"
          placeholder="Search courses…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {/* — only this area scrolls — */}
      <div className="course-list-scroller">
        <Droppable droppableId="courses" isDropDisabled={false}>
          {(provided) => (
            <div className="course-list" ref={provided.innerRef} key={filtered} {...provided.droppableProps}>
              <CourseDisplayList
                courses={filtered}
                page_size={50}
                onClick={onSelectCourse}
                page={page}
                setPage={setPage}
              />
              {provided.placeholder}
            </div>
          )}
        </Droppable>
      </div>
    </div>
  );
}
