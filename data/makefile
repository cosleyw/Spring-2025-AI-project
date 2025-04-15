
all: course_data.json cool_tree.json

course_data.json: scrape.js fix_course.js
	node scrape.js
	node fix_course.js > course_data.json

cool_tree.json: program_reqs.js
	node program_reqs.js > cool_tree.json
