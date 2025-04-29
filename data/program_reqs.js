let Course = (dept, number) => ({type: "course", dept, number});
let All = (...req) => ({type: "all", req});
let AtleastNCourses = (n, m) => (...options) => ({type: "course-range", n, m, options});
let AtleastNCredits = (n, m) => (...options) => ({type: "credit-range", n, m, options});
let Tag = (info, node) => ({type:"tag", info, node});
let True = () => ({type:"true"});
let False = () => ({type:"false"});




let hash = a => a.toLowerCase().match(/[a-z0-9]/g).join("");

let fs = require("node:fs");
let list_files = path => fs.readdirSync(path);
let read_file = path => fs.readFileSync(path);
let write_file = (path, str) => fs.writeFileSync(path, str);

let courses = JSON.parse(read_file("./course_data.json"));

let des_course = (name) => [
	name.match(/^[^0-9]+/)[0].trim()
		.replaceAll(/[^a-zA-Z]+/g, " ")
		.toLowerCase(), 
	name.match(/[0-9]+/g)
];


let every_course = () => courses.map(v => Course(v.dept, v.number));

let course_wildcard = (dept, wc) => {
	let set = courses.filter(v => v.dept == dept).map(v => v.number).flat().filter(v => v.length == wc.length);

	for(let i = 0; i < wc.length; i++)
		set = set.filter(v => v[i] == wc[i] || wc[i] == "#");

	if(set.length == 0){
		console.error(dept, wc);
		console.error(set);
	}

	return AtleastNCourses(1,1)(...set.map(v => Course(dept, number.toString().trim())));
}


let csv_to_tree = (table, nodes, leaves) => {
	let tr = {};

	nodes = nodes.map(v => Object.keys(table[0])[v]);
	leaves = leaves.map(v => Object.keys(table[0])[v]);
	table.map(v => {
		let cur = tr;
		nodes.map(k => {
			cur[v[k]] ??= {};
			cur = cur[v[k]];
		});


		cur.nodes ??= []
		cur.nodes.push(leaves.map(k => v[k]));
	});

	return tr;
}



let get_line_type = (line_descr) => line_descr.split(/\n|\.|(\([^()]*\))/g).map(v => v?.trim()).filter(v => v)[0];

let type_map = {
	'If chosen, complete 2 courses PLUS project course: CS 4550 Translation of Programming Languages': (...x) => AtleastNCourses(3,3)(AtleastNCourses(2,2)(...x.slice(0,3),...x.slice(3+1)),x[3]),
	'If chosen, complete 2 courses PLUS project course: CS 4620 Intelligent Systems': (...x) => AtleastNCourses(3,3)(AtleastNCourses(2,2)(...x.slice(0,4),...x.slice(4+1)),x[4]),
	'If chosen, complete 2 courses PLUS project course: CS 4740 Real-Time Embedded Systems': (...x) => AtleastNCourses(3,3)(AtleastNCourses(2,2)(...x.slice(0,3),...x.slice(3+1)),x[3]),

	'If chosen, complete 2 courses PLUS one project course: CS 4410 System Security OR CS 4420 Applied Systems Forensics': (...x) => AtleastNCourses(3,3)(AtleastNCourses(2,2)(...x.slice(0,4),...x.slice(4+2)),AtleastNCourses(1,1)(x[4],x[5])),


	'If chosen, complete 3 courses, including project course: CS 4620 Intelligent Systems': (...x) => AtleastNCourses(3,3)(AtleastNCourses(2,2)(...x.slice(0,4),...x.slice(4+1)),x[4]),
	'If chosen, complete 2 courses PLUS  one project course: CS 4410 System Security OR CS 4420 Applied Systems Forensics': (...x) => AtleastNCourses(3,3)(AtleastNCourses(2,2)(...x.slice(0,4),...x.slice(4+2)),AtleastNCourses(1,1)(x[4],x[5])),




	'Piano Proficiency, Senior Recital AND Foreign Language': (...x) => AtleastNCourses(3,3)(AtleastNCourses(1,1)(x[0],x[1]),x[2],x[3]),
	'Piano Proficiency AND Senior Recital': (...x) => AtleastNCourses(2,2)(AtleastNCourses(1,1)(x[0],x[1]), x[2]),
	'Piano Proficiency AND Recitals': (...x) => AtleastNCourses(3,3)(AtleastNCourses(1,1)(x[0],x[1]),x[2],x[3]),

	'3 Courses Required from ONE of the 4 areas: Foundations, OR Data and Applications, OR Software Engineering, OR Systems': AtleastNCourses(3,3),
	'3 Courses Required from ONE of the 3 areas: Data and Applications, OR Software Engineering, OR Systems': AtleastNCourses(3,3),
	'0-1 Course Required': AtleastNCourses(0,1),
	'Pick courses from each of the three categories': AtleastNCredits(26,26),
	'Choose at least 1 course from each category: A, B, and C': AtleastNCredits(20,20),
	'Choose any Geography course in consultation with a Geography faculty advisor': AtleastNCredits(21,21),


	'(select ANTH 2005 & ANTH 2006 OR ANTH 3450)': AtleastNCredits(3,4), //lil broken
	'(LN-020)': AtleastNCredits(6,6),
	'(LN-010)': AtleastNCourses(1,1),
	'Additional Electives to reach minimum of 21 units': AtleastNCredits(21,21),
	'Must have grade of C- or better': AtleastNCourses(1, 1), //line numbers that end with 5 mean its an or
	'(LN-030)': AtleastNCourses(1,1),
	'Must have grade of C or better': AtleastNCourses(1,1), //this guy is a lil bit broken
	'Students can choose from courses not used above or from the following courses in religion': AtleastNCredits(18,18),
	'Students can choose from courses not used listed above or from the following courses in Philosophy': AtleastNCredits(9, 9),
	'Additional units to meet the 16 unit requirement': (...reqs) => Tag("fixme!", AtleastNCredits(0,8)(...reqs)), //this guy sucks lmao

	'1 Course Required': AtleastNCourses(1,1),
	'12 Units Required': AtleastNCredits(12,12),
	'4 Units Required': AtleastNCredits(4,4),
	'3 Units Required': AtleastNCredits(3,3),
	'3-4 Units Required': AtleastNCredits(3,4),
	'9-11 Units from Category A, B, or C above that have not already been taken to fulfill Category A, B, or C': AtleastNCredits(9,11),
	'9 Units Required': AtleastNCredits(9,9),
	'3 Units  Required': AtleastNCredits(3,3),
	'2 Unit Required': AtleastNCredits(2,2),
	'2 Units Required': AtleastNCredits(2,2),
	'1 Unit Required': AtleastNCredits(1,1),
	'3  Units Required': AtleastNCredits(3,3),
	'5 Units Required': AtleastNCredits(5,5),
	'6 Units Required': AtleastNCredits(6,6),
	'2 Courses Required': AtleastNCourses(2,2),
	'(select one of the following)': AtleastNCourses(1,1),
	'21 Units Required': AtleastNCredits(21,21),
	'18 Units Required': AtleastNCredits(18,18),
	'3 Units': AtleastNCredits(3,3),
	'10 Units Required': AtleastNCredits(10,10),
	'7 Units Required': AtleastNCredits(7,7),
	'9 Units Required from  POL AMER, POL COMP, POL GEN, POL INTL,  POL THRY Courses': AtleastNCredits(9,9),
	'4-5 Units Required': AtleastNCredits(4,5),
	'Level II - 7 Units Required': AtleastNCredits(7,7),
	'Level III - 3 Units Required': AtleastNCredits(3,3),
	'6 Units Required from the following courses:': AtleastNCredits(6,6),
	'3 Units of Sociology or Criminology required from the following courses:': AtleastNCredits(3,3),
	'Choose two courses from the following': AtleastNCourses(2,2),
	'Choose three courses from the following': AtleastNCourses(3,3),
	'At least one course': AtleastNCourses(1, 1),
	'10-15 Units Required': AtleastNCredits(10,15),
	'15 Units Required': AtleastNCredits(15,15),
	'6 Units Required from the following courses': AtleastNCredits(6,6),
	'6 Units Required in European, Asian, Latin American and/or African history from the following courses': AtleastNCredits(6,6),
	'3 Units Required  Cannot count ECON 1011, 1021 or 1031': AtleastNCredits(3,3),
	'Select at least 9 hours of the following': AtleastNCredits(9,9),
	'3 units required': AtleastNCredits(3,3),
	'9 units required': AtleastNCredits(9,9),
	'At least one course, this course can also count as a World History Elective': AtleastNCourses(1, 1),
	'3 Units Required *COMM 4216 OR POL AMER 4160*': AtleastNCredits(3,3),
	'9 Units Required in Sociology or Criminology from the following courses': AtleastNCredits(9, 9),
	'3 Courses Required': AtleastNCourses(3,3),
	'2 Course Required': AtleastNCourses(2,2),
	'3 Units Required - ONE may be in performance': AtleastNCredits(3,3),
	'22 Units Required': AtleastNCredits(22,22),
	'8 Units Required': AtleastNCredits(8,8),
	'14 Units Required': AtleastNCredits(14,14),
	'3 Units Required - Limited to 3000/4000-level courses in the following areas only:  MUS ED, MUS HIST, MUS LIT, MUS TECH, MUS THEO': AtleastNCredits(3,3),
	'1-3 Units Required': AtleastNCredits(1,3),
	'2-3 Units Required': AtleastNCredits(2,3),
	'26 Units Required': AtleastNCredits(26,26),
	'Select at least 18 units from the following': AtleastNCredits(18, 18),
	'Select at least 7 units from the following': AtleastNCredits(7, 7),
	'At least 2 Courses Required': AtleastNCourses(2,2),
	'2-7 Units from Category A, B, or C above that have not already been taken to fulfill the minimum of 26 units': AtleastNCredits(2,7),
	'At least 4 Courses Required': AtleastNCourses(4,4),


	'Select one of the following': AtleastNCourses(1,1),
	'1 Course  Required': AtleastNCourses(1,1),
	'(LN-040)': AtleastNCourses(1,1),
	'Requires the successful completion of an approved study abroad experience, or a departmental internship or cooperative education experience that includes a significant international component': AtleastNCourses(1,1),
	'Select one of the following courses': AtleastNCourses(1,1),
	'Introduction to Economics -  ECON 1041': AtleastNCourses(1,1),
	'Course Required': AtleastNCourses(1,1),





	'Select one group': AtleastNCredits(8,8),
	'Pick courses from each of the Categories': (...x) => AtleastNCredits(23,23)(All(...x)),
	'Requires admission to the Wilson College of Business': AtleastNCourses(5,5),
	'Select 3 hours from each emphasis': All,
	'(RQ-64059)': All,
	'(RQ-50994)': All,
	'(RQ-64513)': All,
	'(RQ-63909)': All,
	'(RQ-64523)': All,
	'(RQ-64516)': All,
	'Required, 0 Credits': All,






	'Select four courses from the following': AtleastNCourses(4,4),
	'Select a specialty of 3 courses from the Foundations Specialty Area': AtleastNCourses(3,3),

	'Choose from courses not taken from Groups A, B, or C': AtleastNCredits(9,9),
	'4 Units and **Grade of C or Better** Required': AtleastNCredits(4,4),
	'3 Units and **Grade of C or Better** Required': AtleastNCredits(3,3),
	'1 Units Required': AtleastNCredits(1,1),
	'12 Units': AtleastNCredits(12,12),
	'2  Units Required': AtleastNCredits(2,2),
	'31 Units Required': AtleastNCredits(31,31),
	'11-12 Units Required': AtleastNCredits(11,12),
	'33 Units Required': AtleastNCredits(33,33),
	'9-12 Units': AtleastNCredits(9,12),
	'24 Units Required': AtleastNCredits(24,24),
	'19 Units Required': AtleastNCredits(19,19),
	'42 Units Required': AtleastNCredits(42,42),
	'39 Units Required': AtleastNCredits(39,39),
	'13 Units Required': AtleastNCredits(13,13),
	'12-13 Units Required': AtleastNCredits(12,13),
	'38 Units Required': AtleastNCredits(38,38),
	'POLITICAL SCIENCE SUB-FIELDS - 12 Units Required': AtleastNCredits(12,12),
	'15 Units': AtleastNCredits(15,15),
	'32-33 Units Required': AtleastNCredits(32,33),
	'16 Units Required': AtleastNCredits(16,16),
	'35 Units Required': AtleastNCredits(35,35),
	'29 Units Required': AtleastNCredits(29,29),
	'10 Units Required  RQ-63990)': AtleastNCredits(10,10),
	'30 Units Required': AtleastNCredits(30,30),
	'27 Units Required': AtleastNCredits(27,27),
	'19-24 Units Required': AtleastNCredits(19,24),
	'4 Courses Required': AtleastNCourses(4,4),
	'22 Courses Required': AtleastNCourses(22,22),
	'19 Courses Required': AtleastNCourses(19,19),
	'Electives - 3 Courses Required': AtleastNCourses(3,3),
	'12-13 Courses Required': AtleastNCourses(12,13),
	'15 Courses Required': AtleastNCourses(15,15),
	'6-7 Courses Required': AtleastNCourses(6,7),
	'16 Courses Required': AtleastNCourses(16,16),
	'18 Courses Required': AtleastNCourses(18,18),
	'21 Courses Required': AtleastNCourses(21,21),
	'17 Units Required': AtleastNCredits(17,17),
	'11 Units Required': AtleastNCredits(11,11),
	'18  Units Required': AtleastNCredits(18,18),
	'To reach 36 Units': AtleastNCredits(36,36),
	'(RQ-64773)': AtleastNCredits(18,18),
	'6 Courses Required': AtleastNCourses(6,6),
	'3-6 Units Required': AtleastNCredits(3,6),
	'5-6 Units Required': AtleastNCredits(5,6),
	'13-16 Units Required': AtleastNCredits(13,16),
	'5-8 Units Required': AtleastNCredits(5,8),
	'3-5 Units Required': AtleastNCredits(3,5),
	'9-13 Units Required': AtleastNCredits(9,13),
	'40 Units Required': AtleastNCredits(40,40),
	'25 Units Required': AtleastNCredits(25,25),


	'11-14 Units Required': AtleastNCredits(11,14),
	'Choose ONE course': AtleastNCourses(1,1),
	'Choose ONE course *BIOL 3101 will count as university elective': AtleastNCourses(1,1),
	'4-5 Courses Required': AtleastNCourses(4,5),
	'20 Units Required': AtleastNCredits(20,20),
	'10 Courses Required': AtleastNCourses(10,10),
	'5 Courses Required': AtleastNCourses(5,5),

	'8-9 Courses Required': AtleastNCourses(8,9),


	'8 Courses Required': AtleastNCourses(8,8),
	'6 Courses and 3': AtleastNCourses(6,6),
	'23 Units Required': AtleastNCredits(23,23),
	'30-32 Units Required': AtleastNCredits(30,32),
	'62-63 Units Required': AtleastNCredits(62,63),
	'54 Units Required': AtleastNCredits(54,54),
	'59-62 Units Required': AtleastNCredits(59,62),
	'60 Units Required': AtleastNCredits(60,60),
	'57 Units Required': AtleastNCredits(57,57),
	'31-32 Units Required': AtleastNCredits(31,32),
	'39-40 Units Required': AtleastNCredits(39,40),
	'63 Units Required': AtleastNCredits(63,63),
	'61 Units Required': AtleastNCredits(61,61),
	'41 Units Required': AtleastNCredits(41,41),
	'49-50 Units Required': AtleastNCredits(49,50),
	'48 Units Required': AtleastNCredits(48,48),
	'32 Units Required': AtleastNCredits(32,32),
	'55 Units Required': AtleastNCredits(55,55),
	'37 Units Required': AtleastNCredits(37,46),
	'46 Units Required': AtleastNCredits(46,46),
	'55-60 Units Required': AtleastNCredits(55,60),
	'36-41 Units Required': AtleastNCredits(36,41),
	'87 Units Required': AtleastNCredits(87,87),
	'79-80 Units Required': AtleastNCredits(79,80),
	'80-81 Units Required': AtleastNCredits(80,81),
	'97-100 Units Required': AtleastNCredits(97,100),
	'78-81 Units Required': AtleastNCredits(78,81),
	'76-77 Units Required': AtleastNCredits(76,77),
	'75 Units Required': AtleastNCredits(75,75),
	'62 Units Required': AtleastNCredits(62,62),
	'49 Units Required': AtleastNCredits(49,49),
	'45-47 Units Required': AtleastNCredits(45,47),
	'47 Units Required': AtleastNCredits(47,47),
	'50 Units Required': AtleastNCredits(50,50),
	'80 Units Required': AtleastNCredits(80,80),
	'69 Units Required': AtleastNCredits(69,69),
	'79 Units Required': AtleastNCredits(79,79),
	'46 Units Required **BA Music majors are not permitted to declare a double major within the School of Music': AtleastNCredits(46,46),
	'53 Units Required **BA Music majors are not permitted to declare a double major within the School of Music': AtleastNCredits(53,53),
	'51 Units Required': AtleastNCredits(51,51),
	'52 Units Required **BA Music majors are not permitted to declare a double major within the School of Music': AtleastNCredits(52,52),
	'36 Units Required': AtleastNCredits(36,36),
	'40-43 Units Required': AtleastNCredits(40,43),
	'43-46 Units Required': AtleastNCredits(43,46),
	'63-67 Units Required': AtleastNCredits(63,67),
	'53-58 Units Required': AtleastNCredits(53,58),
	'45-51 Units Required': AtleastNCredits(45,51),
	'57-62 Units Required': AtleastNCredits(57,62),
	'64-67 Units Required': AtleastNCredits(64,67),
	'72-75 Units Required': AtleastNCredits(72,75),
	'45 Units Required': AtleastNCredits(45,45),
	'62-65 Units Required': AtleastNCredits(62,65),
	'59 Units Required': AtleastNCredits(59,59),
	'42-43 Units Required': AtleastNCredits(42,43),
	'42-47 Units Required': AtleastNCredits(42,47),
	'44 Units Required': AtleastNCredits(44,44),
	'60 Units Required  **Management majors are allowed to double major with either Supply Chain Management or Management Information Systems with five additional classes': AtleastNCredits(60,60),
	'90 Units Required': AtleastNCredits(90,90),
	'80 Units Required  - This major requires a minimum of 121 total units to graduate': AtleastNCredits(80,80),
	'54-56 Units Required': AtleastNCredits(54,56)
}


let rm_graduate_courses = (tree) => ({
	course: (tr) => tr.number < 5000 ? tr : False(),
	all: (tr) => All(...tr.req.map(rm_graduate_courses)),
	"course-range": (tr) => AtleastNCourses(tr.n, tr.m)(...tr.options.map(rm_graduate_courses)),
	"credit-range": (tr) => AtleastNCredits(tr.n, tr.m)(...tr.options.map(rm_graduate_courses)),
	tag: (tr) => Tag(tr.info, rm_graduate_courses(tr.node)),
	true: (tr) => tr,
	false: (tr) => tr
})[tree.type](tree);



let simp_tree = (tree) => ({
	course: (tr) => tr,
	all: (tr) => {
		let req = tr.req.map(simp_tree).filter(v => v.type != "true").flatMap(v => v.type == "all" ? v.req : [v]);
		
		if(req.length == 0)
			return True();
		if(req.some(v => v.type == "false"))
			return False();
		return req.length == 1 ? req[0] : All(...req);
	},
	"course-range": (tr) => {
		if(tr.n == null || tr.m == null)
			console.error("you fucked up: ", tr);
		let req = tr.options.map(simp_tree).filter(v => v.type != "true" && v.type != "false")
		if(req.length == 0)
			return False();

		if(req.every(v => v.type == "course")){
			if(req.length < tr.n)
				return False();

			if(req.length <= tr.m)
				return simp_tree(All(...req));
		}

		if(req.length == 1 && req[0].type == "course-range"){
			let nd = req[0];

			if(tr.n <= nd.n && tr.m >= nd.m)
				return nd;
		}


		if(req.every(v => v.type == "course-range")){
			let lb = req.map(v => v.n).reduce((a, b) => a + b);
			let rb = req.map(v => v.m).reduce((a, b) => a + b);

			if(lb >= tr.n && rb <= tr.m)
				return simp_tree(All(...req));
		}

		return AtleastNCourses(tr.n, tr.m)(...req);
	},
	"credit-range": (tr) => {
		if(tr.n == null || tr.m == null)
			console.error("you fucked up: ", tr);
		let req = tr.options.map(simp_tree).filter(v => v.type != "true" && v.type != "false")
		if(req.length == 0)
			return False();


		if(req.length == 1 && req[0].type == "credit-range"){
			let nd = req[0];

			if(tr.n <= nd.n && tr.m >= nd.m)
				return nd;
		}

		if(req.every(v => v.type == "credit-range")){
			let lb = req.map(v => v.n).reduce((a, b) => a + b);
			let rb = req.map(v => v.m).reduce((a, b) => a + b);

			if(lb >= tr.n && rb <= tr.m)
				return simp_tree(All(...req));
		}

		if(req.length == 1 && req[0].type == "course"){
			let course = courses.find(v => v.id == (req[0].dept + " " + req[0].number));

			if(course != null){
				if(course.hours.some(v => v >= tr.n))
					return req[0];

				return False();
			}
			console.error("missing course:", req[0]);
		}


		return AtleastNCredits(tr.n, tr.m)(...req);
	},
	tag: (tr) => Tag(tr.info, simp_tree(tr.node)),
	true: (tr) => tr,
	false: (tr) => tr
})[tree.type](tree);



let assert = (b, descr) => {
	if(!b) throw new Error(descr);
}


let fix_tree = (tr) => {
	let get_type = (type) => type_map[get_line_type(type)];
	let fix_course = ([id, dept, number]) => {
		if(dept.trim() == "(***)"){
			console.error("weird wildcard thing");
			return every_course();
		}


		try{
			let course_name = des_course(dept + " 1000");
			if(/#/.test(number))
				return [course_wildcard(course_name[0], number.trim())];

			return [Course(course_name[0], number.toString().trim())];
		}catch (e){
			return [];
		}
	}

	let fix_line = (tr) => {
		let keys = Object.keys(tr);
		return keys.map(v => get_type(v)(...tr[v].nodes.flatMap(fix_course)));
	}

	let fix_req = (tr) => {
		let key = Object.keys(tr);
		assert(key.length == 1, "should only have one");
		key = key[0]

		return get_type(key)(...Object.entries(tr[key]).map(v => fix_line(v[1])).flat());
	}

	let fix_rg = (tr) => {
		let key = Object.keys(tr);
		assert(key.length == 1, "should only have one");
		key = key[0]

		return get_type(key)(...Object.entries(tr[key]).map(v => Tag(v[0], fix_req(v[1]))));
	}


	delete tr["PROFESSIONAL EDUCATION REQUIREMENTS"];

	return Object.fromEntries(Object.entries(tr).map(v => [v[0], simp_tree(rm_graduate_courses(fix_rg(v[1])))]));
}






let csv = require("csv-parser");
let results = [];
fs.createReadStream('program_reqs.csv')
	.pipe(csv())
	.on('data', (data) => results.push(data))
	.on('end', () => {
		let tr = csv_to_tree(results, [1, 2, 3, 4, 5, 6], [7, 8, 9]);

		//console.log(JSON.stringify(tr));

		/*
	let line_descr = [
		...results.map(v => v[Object.keys(v)[6]]), 
		...results.map(v => v[Object.keys(v)[4]]),
		...results.map(v => v[Object.keys(v)[2]])
	];

	let line_types = ([...new Set(line_descr.map(get_line_type))]).filter(v => type_map[v] == null);
	console.log(Object.fromEntries(line_types.map(v => [v, "TODO"])));
	*/

		console.log(JSON.stringify(fix_tree(tr)));
//console.error(courses);
	});


