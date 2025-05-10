import { useMemo, useRef, useState } from 'react';
import './FormMultiselect.css';

function FormMultiselect({ ids, data, handleMouseDown, classes, title, required }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [onlyActive, setOnlyActive] = useState(false);
  const selectionBox = useRef(null);

  const filtered_data = useMemo(
    () =>
      data.filter(
        (data_piece) =>
          (data_piece.id.toLowerCase().search(searchTerm.toLowerCase()) !== -1 ||
            data_piece.name.toLowerCase().search(searchTerm.toLowerCase()) !== -1) &&
          (!onlyActive || ids.includes(data_piece.id))
      ),
    [ids, data, searchTerm, onlyActive]
  );

  const options = useMemo(
    () =>
      filtered_data.map((c) => (
        <option key={c.id} value={c.id} onMouseDown={handleMouseDown}>
          {c.hasOwnProperty('code') && `${c.code} — `}
          {c.name}
        </option>
      )),
    [filtered_data]
  );

  return (
    <div className={classes}>
      <label>{title}</label>
      <div className="form-multiselect-options">
        <input
          className="form-multiselect-search"
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        ></input>
        <input
          className="form-multiselect-toggle"
          type="checkbox"
          checked={onlyActive}
          onChange={(e) => setOnlyActive(e.target.checked)}
        ></input>
      </div>
      <select multiple value={ids} ref={selectionBox} required={required}>
        {options}
      </select>
    </div>
  );
}

export default FormMultiselect;
