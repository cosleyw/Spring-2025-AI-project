
all: course_data.json cool_tree.json

course_data.json: scrape.js fix_course.js
	# rm -f structured_data.json data.json
	node scrape.js
	node fix_course.js > course_data.json

cool_tree.json: program_reqs.js
	node program_reqs.js > cool_tree.json
