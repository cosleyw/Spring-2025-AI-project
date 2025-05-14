// src/api.js
const PROXY = import.meta.env.VITE_API_PROXY ?? '/api';
//const PROXY = import.meta.env.MODE === 'development' ? (import.meta.env.VITE_API_PROXY ?? `api`) : "http://152.67.227.147"

async function post(path, body) {
  console.log("psoting with the body")
  console.log(body)
  const res = await fetch(`${PROXY}${path}`, {
    method:"POST",
    headers: new Headers({'content-type': 'application/json'}),
    body: body,
  });
  if (!res.ok) {
    let text = '';
    try { text = await res.text() } catch {}
    throw new Error(
      `API ${path} failed: ${res.status} ${res.statusText}` +
      (text ? ` – ${text}` : '')
    );
  }
  return res.json();
}

async function fetchJson(path, options = {}) {
  const res = await fetch(`${PROXY}${path}`, {
    mode:"no-cors",
  });
  if (!res.ok) {
    let text = '';
    try { text = await res.text() } catch {}
    throw new Error(
      `API ${path} failed: ${res.status} ${res.statusText}` +
      (text ? ` – ${text}` : '')
    );
  }
  return res.json();
}

/** GET /courses → [ { id, code, name, credits, … } ] */
export async function get_courses() {
  const data = await fetchJson('/courses');
  const raw  = data.courses ?? data;
  return (Array.isArray(raw) ? raw : Object.values(raw))
    .map(c => ({
      id:      c.id ?? c.code,
      code:    c.code ?? (c.dept && c.number
                    ? `${c.dept.toUpperCase()} ${c.number}`
                    : c.id),
      name:    c.name ?? c.title ?? '',
      // credit hours live in c.hours[0]
      credits: Array.isArray(c.hours) ? c.hours[0] : 0,
      ...c
    }));
}

/** GET /courses/:id → single course object */
export async function get_course(id) {
  const data = await fetchJson(`/courses/${encodeURIComponent(id)}`);
  // either data.course or raw
  return data.course ?? data;
}

/** GET /degrees → [ { id, name } ] */
export async function get_degrees() {
  const data = await fetchJson('/degrees');
  const raw  = data.degrees ?? data;
  return (Array.isArray(raw)
      ? raw
      : Object.entries(raw).map(([id,node]) => ({ id, ...node }))
    )
    .map(d => ({
      id:   d.id,
      name: d.info ?? d.name ?? d.id
    }));
}

/** GET /degrees → [ { id, ... } ] */
export async function get_degrees_full() {
  const data = await fetchJson('/degrees');
  const raw = data.degrees ?? data;
  return Object.values(raw);
}

/** GET /degrees/:id → full degree tree node */
export async function get_degree(id) {
  const data = await fetchJson(`/degrees/${encodeURIComponent(id)}`);
  return data.node ?? data;
}

/**
 * GET /schedules/generate?…
 * returns [ [], [], … ]
 */
export async function generate_schedule(form) {
  const {
    desired_degree_ids,
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

  const qp = new URLSearchParams({
    semester_count,
    min_credit_per_semester,
    max_credit_per_semester,
    starts_as_fall: start_term === 'Fall',
    start_year
  });

  if (desired_degree_ids.length) qp.set('desired_degree_ids_str', desired_degree_ids.join(';'));
  if (transfer_ids.length) qp.set('transferred_course_ids_str',   transfer_ids.join(','));
  if (block_ids.length)    qp.set('undesired_course_ids_str',     block_ids.join(','));
  if (desired_ids.length)  qp.set('desired_course_ids_str',       desired_ids.join(','));

  qp.set('first_semester_sophomore', soph_semester);
  qp.set('first_semester_junior',    jr_semester);
  qp.set('first_semester_senior',    sr_semester);

  const data = await fetchJson(`/schedules/generate?${qp}`);
  if(data.status == "failure") throw new Error(data.message);
  const arr  = Array.isArray(data) ? data : data.schedule;
  if (!Array.isArray(arr)) throw new Error('Unexpected schedule response');
  return arr;
}

export async function post_schedule(schedule) {
  const filtered_schedule = schedule.map(semester => {
    return semester["courses"].map(course => ({'id': course['id'], 'name': course['name']}))
  })
  await post(`/schedules/save`, JSON.stringify({"schedule": filtered_schedule}));
}