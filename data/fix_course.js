
let fs = require("node:fs");
let list_files = path => fs.readdirSync(path);
let read_file = path => fs.readFileSync(path);
let write_file = (path, str) => fs.writeFileSync(path, str);

let st_data = JSON.parse(read_file("./structured_data.json"));

let des_course = (name) => [
	name.match(/^[^0-9]+/)[0].trim()
		.replaceAll(/[^a-zA-Z]+/g, " ")
		.toLowerCase(), 
	name.match(/[0-9]+/g)
];


let course_set = new Set(Object.entries(st_data).map(v => v[1]?.courses).filter(v => v).flat().map(v => [
	...des_course(v.course),
	v
]).map(([dept, nums, full]) => nums.map(v => dept + " " + v)).flat());

//console.error(course_set);




let True = () => ({type:"true"})
let False = () => ({type:"false"})
let Standing = (str) => ({type:"standing", value: str});
let Course = (dept, number) => ({type:"course", dept, number})
let Some = (...req) => ({type:"some", req})
let All = (...req) => ({type:"all", req})

let rm_graduate_courses = (tree) => ({
  "true": (tr) => tr,
  "false": (tr) => tr,
  "some": (tr) => Some(...tr.req.map(rm_graduate_courses)),
  "all": (tr) => All(...tr.req.map(rm_graduate_courses)),
  "course": (tr) => +tr.number < 5000 ? tr : False(),
  "standing": (tr) => tr
})[tree.type](tree)


let simp_tree = (tree) => ({
  "true": (tr) => tr,
  "false": (tr) => tr,
  "some": (tr) => {
    let req = tr.req.map(simp_tree).filter(v => v.type != "false");
    if(req.length == 0)
	  return False();
    if(req.some(v => v.type == "true"))
	  return True();
    return req.length == 1 ? req[0] : Some(...req);
  },
  "all": (tr) => {
    let req = tr.req.map(simp_tree).filter(v => v.type != "true");
    if(req.length == 0)
	  return True();
    if(req.some(v => v.type == "false"))
	  return False();
    return req.length == 1 ? req[0] : All(...req)
  },
  "course": (tr) => tr,
  "standing": (tr) => tr
})[tree.type](tree)



let fix_req = (req) => {
	if(req.length == 0)
		return True();

	let arr = req.filter(v => Array.isArray(v));
	let str = req.filter(v => !Array.isArray(v)).map(v => v.toLowerCase());
	
	//console.log(arr, str);

	let fix_str = v => {
		if(v.match(/standing/) != null){
			let thing = v.replaceAll(/standing/ig, "").trim();

			if(/^[a-zA-z]+$/.test(thing))
				return Standing(thing);
			

			return null;
		}

		try{
			if(des_course(v)[1].length != 0){
				let dc = des_course(v);
				if(!course_set.has(dc[0] + " " + dc[1][0])){
					console.error("fixme!", v, dc[0] + " " + dc[1][0]);
					return null;
				}
				return Some(...dc[1].map(v => Course(dc[0], v)));
			}
		}catch{}
			
		console.error("unexpected thing:", v);
		return null;
	};

	let fstr = str.map(fix_str).filter(v => v != null);
	let farr = arr.map(req => {
		let arr = req.filter(v => Array.isArray(v));
		let str = req.filter(v => !Array.isArray(v));

		let fstr = str.map(fix_str).filter(v => v != null);
		let farr = arr.map(fix_req);

		return Some(...fstr, ...farr);
	});


	return simp_tree(rm_graduate_courses(All(...fstr, ...farr)));
}

let courses = Object.entries(st_data).map(v => v[1]?.courses).filter(v => v).flat().map(v => [
	...des_course(v.course),
	v
]).map(([dept, nums, full]) => 
	nums.map(v => ({dept, number: v, name: full.name, hours: full.hours, semester: full.semester, 
		id: dept + " " + v,
		prereq: fix_req(full.prereq), 
		coreq: fix_req(full.coreq), 
		preorco: fix_req(full.preorco), 
		desc: full.desc}))
).flat();


courses = Object.entries(Object.fromEntries(courses.map(v => [v.id, v]))).map(v => v[1]);



console.log(JSON.stringify(courses.filter(v => +v.number < 5000)));




