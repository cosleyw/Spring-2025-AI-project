export const displayCourseHours = (...courses) => {
  console.log(courses);
  if (courses.some((course) => !('hours' in course) || course['hours'].length < 1)) {
    return `—`;
  }
  console.log(courses);
  let min_possible = courses.map((course) => Math.min(...course['hours'])).reduce((curr, prev) => curr + prev, 0);
  let max_possible = courses.map((course) => Math.max(...course['hours'])).reduce((curr, prev) => curr + prev, 0);
  console.log(min_possible, max_possible);

  if (min_possible === max_possible) {
    return min_possible;
  } else {
    return `${min_possible}-${max_possible}`;
  }
};
