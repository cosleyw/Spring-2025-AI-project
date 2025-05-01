// src/api.js
const PROXY = import.meta.env.VITE_API_PROXY ?? '/api';

async function fetchJson(path, options = {}) {
  const res = await fetch(`${PROXY}${path}`, options);
  if (!res.ok) {
    let text = '';
    try { text = await res.text(); } catch {}
    throw new Error(
      `API ${path} failed: ${res.status} ${res.statusText}` +
      (text ? ` – ${text}` : '')
    );
  }
  return res.json();
}

/** GET /courses → [ { id, code, name, … } ] */
export async function get_courses() {
  const data = await fetchJson('/courses');
  const raw  = data.courses ?? data;
  if (Array.isArray(raw)) {
    return raw.map(c => ({
      ...c,
      code: c.code ?? (c.dept && c.number
        ? `${c.dept.toUpperCase()} ${c.number}`
        : c.id),
      name: c.name ?? c.title ?? '',
    }));
  }
  return Object.entries(raw).map(([id, c]) => ({
    id,
    code: c.code ?? (c.dept && c.number
      ? `${c.dept.toUpperCase()} ${c.number}`
      : id),
    name: c.name ?? c.title ?? '',
    ...c,
  }));
}

/** GET /courses/:id → single course object */
export async function get_course(id) {
  const data = await fetchJson(`/courses/${encodeURIComponent(id)}`);
  return data.course ?? data;
}

/** GET /degrees → [ { id, name } ] */
export async function get_degrees() {
  const data = await fetchJson('/degrees');
  const raw  = data.degrees ?? data;
  if (Array.isArray(raw)) {
    return raw.map(d => ({
      id:   d.id,
      name: d.info ?? d.name ?? d.id,
    }));
  }
  return Object.entries(raw).map(([id, node]) => ({
    id,
    name: node.info ?? node.name ?? id,
  }));
}

/** GET /degrees/:id → full degree tree node */
export async function get_degree(id) {
  const data = await fetchJson(`/degrees/${encodeURIComponent(id)}`);
  // the API returns { node: … } or just the node directly
  return data.node ?? data;
}

/**
 * GET /schedules/generate?…
 * Builds exactly the backend’s query-string, fetches, and returns the array.
 */
export async function generate_schedule(form) {
  const {
    desired_degree_ids_str,
    semester_count,
    min_credit_per_semester,
    max_credit_per_semester,
    start_term,
    start_year,
    transfer_ids,
    block_ids,
    desired_ids,
    soph_semester,
    jr_semester,
    sr_semester,
  } = form;

  const qp = new URLSearchParams();
  qp.set('desired_degree_ids_str',      desired_degree_ids_str);
  qp.set('semester_count',              semester_count);
  qp.set('min_credit_per_semester',     min_credit_per_semester);
  qp.set('max_credit_per_semester',     max_credit_per_semester);
  qp.set('starts_as_fall',              start_term === 'Fall');
  qp.set('start_year',                  start_year);

  if (transfer_ids.length) qp.set('transferred_course_ids_str', transfer_ids.join(','));
  if (block_ids.length)    qp.set('undesired_course_ids_str',   block_ids.join(','));
  if (desired_ids.length)  qp.set('desired_course_ids_str',     desired_ids.join(','));

  qp.set('first_semester_sophomore', soph_semester);
  qp.set('first_semester_junior',    jr_semester);
  qp.set('first_semester_senior',    sr_semester);

  const url  = `/schedules/generate?${qp.toString()}`;
  console.debug('[api] GET →', url);

  const data = await fetchJson(url);

  // accept either a bare array or { schedule: [...] }
  if (Array.isArray(data))        return data;
  if (Array.isArray(data.schedule)) return data.schedule;

  throw new Error('Unexpected schedule response format');
}
