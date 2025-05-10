// src/components/ScheduleGenerator.jsx

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { generate_schedule, get_courses, get_degrees } from '../api';
import { useConfig } from '../context/GeneratorConfigContext';
import { useSchedule } from '../context/ScheduleContext';
import CourseMultiselect from './CourseMutliselect';
import DegreeAccordion from './DegreeAccordion';
import './ScheduleGenerator.css';

export default function ScheduleGenerator() {
  // pull both the current schedule & setter from context
  const navigate = useNavigate();
  const { setNewSchedule } = useSchedule();

  const [degrees, setDegrees] = useState([]);
  const [allCourses, setAllCourses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { form, setForm } = useConfig();

  // load the dropdown data
  useEffect(() => {
    get_degrees().then(setDegrees).catch(console.error);
    get_courses().then(setAllCourses).catch(console.error);
  }, []);

  const handleChange = (key) => (e) => {
    const val = e.target.type === 'number' ? +e.target.value : e.target.value;
    setForm((f) => ({ ...f, [key]: val }));
  };

  const handleSelect = (key) => (e) => {
    e.preventDefault();
    if (e.target.selected) {
      // If currently selected, we will remove it
      setForm((f) => ({ ...f, [key]: f[key].filter((t) => t != e.target.value) }));
    } else {
      // If not selected, we will add it
      setForm((f) => ({ ...f, [key]: [...f[key], e.target.value] }));
    }
    // This fixes a super annoying issue where selecting things scrolls the input select to the top
    const scrollTop = e.target.parentNode.scrollTop;
    setTimeout(() => e.target.parentNode.scrollTo(0, scrollTop), 10);
    return false;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const raw = await generate_schedule(form);
      setNewSchedule(raw, form.start_year, form.start_term, allCourses, false);
      navigate('/');
    } catch (err) {
      console.error(err);
      setError('Failed to generate schedule: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="schedule-generator">
      <h2>Schedule Configuration</h2>
      {/* form.desired_degree_ids_str && <DegreeTree degreeId={form.desired_degree_ids_str} /> */}
      {error && <div className="error">{error}</div>}

      <form onSubmit={handleSubmit}>
        {/*  Row 1  */}
        <div className="form-group">
          <label>Degree:</label>
          <select required value={form.desired_degree_ids_str} onChange={handleChange('desired_degree_ids_str')}>
            <option value="">— select degree —</option>
            {degrees.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group requirements-group">
          <label>Requirements:</label>
          <div className="tree-wrapper">
            <DegreeAccordion degreeId={form.desired_degree_ids_str} />
          </div>
        </div>

        <div className="form-group">
          <label># Semesters:</label>
          <input type="number" min={1} value={form.semester_count} onChange={handleChange('semester_count')} />
        </div>

        <div className="form-group">
          <label>Start Term &amp; Year:</label>
          <div className="inline-fields">
            <select value={form.start_term} onChange={handleChange('start_term')}>
              {['Fall', 'Spring'].map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
            <input type="number" min={2023} value={form.start_year} onChange={handleChange('start_year')} />
          </div>
        </div>

        {/*  Row 2 */}
        <CourseMultiselect
          ids={form.transfer_ids}
          courses={allCourses}
          handleMouseDown={handleSelect('transfer_ids')}
          classes="form-group transfer-group"
          title="Transfer Courses:"
        />

        <CourseMultiselect
          ids={form.block_ids}
          courses={allCourses}
          handleMouseDown={handleSelect('block_ids')}
          classes="form-group blocked-group"
          title="Blocked Courses:"
        />

        <fieldset className="form-group standing-group">
          <legend>Standing Transitions</legend>
          <label>
            Sophomore from Sem#:
            <input type="number" min={1} value={form.soph_semester} onChange={handleChange('soph_semester')} />
          </label>
          <label>
            Junior from Sem#:
            <input type="number" min={1} value={form.jr_semester} onChange={handleChange('jr_semester')} />
          </label>
          <label>
            Senior from Sem#:
            <input type="number" min={1} value={form.sr_semester} onChange={handleChange('sr_semester')} />
          </label>
        </fieldset>

        <fieldset className="form-group credit-group">
          <legend>Credits per Semester</legend>
          <label>
            Min:
            <input
              type="number"
              min={0}
              value={form.min_credit_per_semester}
              onChange={handleChange('min_credit_per_semester')}
            />
          </label>
          <label>
            Max:
            <input
              type="number"
              min={0}
              value={form.max_credit_per_semester}
              onChange={handleChange('max_credit_per_semester')}
            />
          </label>
        </fieldset>

        {/* Row 3  */}
        <CourseMultiselect
          ids={form.desired_ids}
          courses={allCourses}
          handleMouseDown={handleSelect('desired_ids')}
          classes="form-group desired-group"
          title="Desired Courses (any term):"
        />

        <button type="submit" className="generate-button" disabled={loading}>
          {loading ? 'Generating…' : 'Save and Generate Schedule'}
        </button>
      </form>
    </div>
  );
}
