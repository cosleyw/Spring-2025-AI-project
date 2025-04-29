import React, { useState, useEffect } from 'react';
import { get_degrees, get_courses } from '../api';
import './ScheduleSetup.css';

export default function ScheduleSetup({ onSubmit }) {
  const [degrees, setDegrees]   = useState([]);
  const [allCourses, setAll]    = useState([]);
  const [form, setForm]         = useState({
    degreeId: '',
    semesters: 8,
    startTerm: 'Fall',
    startYear: new Date().getFullYear(),
    minCredits: 12,
    maxCredits: 18,
    transferIds: [],
    blockIds: [],
    sophSem: 3,
    jrSem: 5,
    srSem: 7,
    desiredIds: []
  });

  useEffect(() => {
    get_degrees().then(setDegrees).catch(console.error);
    get_courses().then(setAll).catch(console.error);
  }, []);

  const handleChange = (key) => (e) => {
    const val = e.target.type === 'number'
      ? +e.target.value
      : e.target.value;
    setForm(f => ({ ...f, [key]: val }));
  };

  const handleMulti = (key) => (e) => {
    const opts = Array.from(e.target.selectedOptions).map(o => o.value);
    setForm(f => ({ ...f, [key]: opts }));
  };

  const submit = (e) => {
    e.preventDefault();
    onSubmit(form);
  };

  return (
    <form className="setup" onSubmit={submit}>
      <h2>Schedule Configuration</h2>

      <label>
        Degree:
        <select value={form.degreeId} onChange={handleChange('degreeId')} required>
          <option value="" disabled>— pick one —</option>
          {degrees.map(d => (
            <option key={d.id} value={d.id}>{d.name}</option>
          ))}
        </select>
      </label>

      <label>
        # Semesters:
        <input
          type="number"
          min={1}
          value={form.semesters}
          onChange={handleChange('semesters')}
        />
      </label>

      <label>
        Start Term:
        <select value={form.startTerm} onChange={handleChange('startTerm')}>
          {['Fall','Spring','Summer'].map(t => <option key={t}>{t}</option>)}
        </select>
      </label>

      <label>
        Start Year:
        <input
          type="number"
          min={2023}
          value={form.startYear}
          onChange={handleChange('startYear')}
        />
      </label>

      <label>
        Credits per Sem: min
        <input
          type="number"
          min={0}
          value={form.minCredits}
          onChange={handleChange('minCredits')}
        />
        max
        <input
          type="number"
          min={0}
          value={form.maxCredits}
          onChange={handleChange('maxCredits')}
        />
      </label>

      <label>
        Transfer Courses:
        <select multiple value={form.transferIds} onChange={handleMulti('transferIds')}>
          {allCourses.map(c => <option key={c.id} value={c.id}>{c.code}</option>)}
        </select>
      </label>

      <label>
        Blocked Courses:
        <select multiple value={form.blockIds} onChange={handleMulti('blockIds')}>
          {allCourses.map(c => <option key={c.id} value={c.id}>{c.code}</option>)}
        </select>
      </label>

      <fieldset>
        <legend>Classification Semesters</legend>
        <label>
          Sophomore starts at sem #
          <input
            type="number"
            min={1}
            value={form.sophSem}
            onChange={handleChange('sophSem')}
          />
        </label>
        <label>
          Junior starts at sem #
          <input
            type="number"
            min={1}
            value={form.jrSem}
            onChange={handleChange('jrSem')}
          />
        </label>
        <label>
          Senior starts at sem #
          <input
            type="number"
            min={1}
            value={form.srSem}
            onChange={handleChange('srSem')}
          />
        </label>
      </fieldset>

      <label>
        Desired Courses (any sem):
        <select multiple value={form.desiredIds} onChange={handleMulti('desiredIds')}>
          {allCourses.map(c => <option key={c.id} value={c.id}>{c.code}</option>)}
        </select>
      </label>

      <button type="submit">Generate Schedule</button>
    </form>
  );
}
