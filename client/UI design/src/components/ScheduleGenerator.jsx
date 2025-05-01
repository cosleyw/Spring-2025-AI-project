// src/components/ScheduleGenerator.jsx
import React, { useState, useEffect } from 'react';
import ScheduleViewer                 from './ScheduleViewer';
import { get_degrees, get_courses, generate_schedule } from '../api';
import './ScheduleGenerator.css';

export default function ScheduleGenerator() {
  const [degrees,    setDegrees]    = useState([]);
  const [allCourses, setAllCourses] = useState([]);

  const [form, setForm] = useState({
    desired_degree_ids_str:   '',
    semester_count:           8,
    start_term:               'Fall',
    start_year:               new Date().getFullYear(),
    min_credit_per_semester:  12,
    max_credit_per_semester:  18,
    transfer_ids:             [],
    block_ids:                [],
    soph_semester:            3,
    jr_semester:              5,
    sr_semester:              7,
    desired_ids:              []
  });

  const [schedule, setSchedule] = useState(null);
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState('');

  useEffect(() => {
    get_degrees().then(setDegrees).catch(console.error);
    get_courses().then(setAllCourses).catch(console.error);
  }, []);

  const handleChange = key => e => {
    const val = e.target.type === 'number'
      ? +e.target.value
      : e.target.value;
    setForm(f => ({ ...f, [key]: val }));
  };
  const handleMulti = key => e => {
    const vals = Array.from(e.target.selectedOptions).map(o => o.value);
    setForm(f => ({ ...f, [key]: vals }));
  };

  const handleSubmit = async e => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const sched = await generate_schedule(form);
      setSchedule(sched);
    } catch (err) {
      console.error(err);
      setError('Failed to generate schedule: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // once we have a schedule array, hand off to the viewer
  if (Array.isArray(schedule)) {
    return (
      <ScheduleViewer
        schedule={schedule}
        allCourses={allCourses}
      />
    );
  }

  // —————————————————
  // FORM LAYOUT UNCHANGED
  // —————————————————
  return (
    <div className="schedule-generator">
      <h2>Schedule Configuration</h2>
      {error && <div className="error">{error}</div>}
      <form onSubmit={handleSubmit}>
        {/* … all of my labels / selects / fieldsets exactly as before … */}

        <label>
          Degree:
          <select
            required
            value={form.desired_degree_ids_str}
            onChange={handleChange('desired_degree_ids_str')}
          >
            <option value="">— select degree —</option>
            {degrees.map(d => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          # Semesters:
          <input
            type="number"
            min={1}
            value={form.semester_count}
            onChange={handleChange('semester_count')}
          />
        </label>

        <label>
          Start Term &amp; Year:
          <select
            value={form.start_term}
            onChange={handleChange('start_term')}
          >
            {['Fall','Spring','Summer'].map(t => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
          <input
            type="number"
            min={2023}
            value={form.start_year}
            onChange={handleChange('start_year')}
          />
        </label>

        <fieldset>
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

        <label>
          Transfer Courses:
          <select
            multiple
            value={form.transfer_ids}
            onChange={handleMulti('transfer_ids')}
          >
            {allCourses.map(c => (
              <option key={c.id} value={c.id}>
                {c.code} — {c.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          Blocked Courses:
          <select
            multiple
            value={form.block_ids}
            onChange={handleMulti('block_ids')}
          >
            {allCourses.map(c => (
              <option key={c.id} value={c.id}>
                {c.code} — {c.name}
              </option>
            ))}
          </select>
        </label>

        <fieldset>
          <legend>Standing Transitions</legend>
          <label>
            Sophomore from Sem#:
            <input
              type="number"
              min={1}
              value={form.soph_semester}
              onChange={handleChange('soph_semester')}
            />
          </label>
          <label>
            Junior from Sem#:
            <input
              type="number"
              min={1}
              value={form.jr_semester}
              onChange={handleChange('jr_semester')}
            />
          </label>
          <label>
            Senior from Sem#:
            <input
              type="number"
              min={1}
              value={form.sr_semester}
              onChange={handleChange('sr_semester')}
            />
          </label>
        </fieldset>

        <label>
          Desired Courses (any term):
          <select
            multiple
            value={form.desired_ids}
            onChange={handleMulti('desired_ids')}
          >
            {allCourses.map(c => (
              <option key={c.id} value={c.id}>
                {c.code} — {c.name}
              </option>
            ))}
          </select>
        </label>

        <button type="submit" disabled={loading}>
          {loading ? 'Generating…' : 'Generate Schedule'}
        </button>
      </form>
    </div>
  );
}
