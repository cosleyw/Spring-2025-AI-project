// src/api.js
const PROXY = '/api';

async function fetchJson(path) {
  const res = await fetch(`${PROXY}${path}`);
  if (!res.ok) throw new Error(`API ${path} failed: ${res.status}`);
  return res.json();
}

/**
 * GET /courses
 * Supports both:
 *   • { courses: { [id]: {...} } }
 *   • [ { id, … }, … ]
 * Normalizes into:
 *   [ { id, code, name, … }, … ]
 */
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

/**
 * GET /courses/:id
 * Fetch a single course by id.
 */
export async function get_course(id) {
  const data = await fetchJson(`/courses/${encodeURIComponent(id)}`);
  return data.course ?? data;
}

/**
 * GET /degrees
 * Supports both:
 *   • { degrees: { [id]: node, … } }
 *   • { [id]: node, … }
 * Normalizes into:
 *   [ { id, name }, … ]
 */
export async function get_degrees() {
  const data = await fetchJson('/degrees');
  const raw  = data.degrees ?? data;

  return Object.entries(raw).map(([id, node]) => ({
    id,
    // prefer node.name if present, then node.info, then fallback to id
    name: node.name ?? node.info ?? id,
  }));
}

/**
 * GET /degrees/:id
 * Returns the full tree node for a particular degree.
 */
export async function get_degree(id) {
  const data = await fetchJson(`/degrees/${encodeURIComponent(id)}`);
  return data.node ?? data;
}
