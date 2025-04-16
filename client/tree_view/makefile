DATA_DIR:=../../data

all: bundle.js course_data.js cool_tree.js

bundle.js: main.js
	browserify ./main.js -p esmify -o bundle.js

course_data.js: ${DATA_DIR}/course_data.json
	echo "let data = " > $@
	cat $< >> $@

cool_tree.js: ${DATA_DIR}/cool_tree.json
	echo "let prog_data = " > $@
	cat $< >> $@

