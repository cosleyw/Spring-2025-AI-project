
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




let True = () => ({type:"true"})
let False = () => ({type:"false"})
let Standing = (str) => ({type:"standing", value: str});
let Course = (dept, number) => ({type:"course", dept, number})
let Some = (...req) => ({type:"some", req})
let All = (...req) => ({type:"all", req})


let simp_tree = (tree) => ({
  "true": (tr) => tr,
  "false": (tr) => tr,
  "some": (tr) => {
    return tr.req.length == 1 ? tr.req[0] : Some(...tr.req.map(simp_tree))
  },
  "all": (tr) => {
    let req = tr.req.filter(v => v.type != "true");
    if(req.length == 0)
	  return True();
    return tr.req.length == 1 ? tr.req[0] : All(...req.map(simp_tree))
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
			return Standing(v.replaceAll(/standing/ig, "").trim());
		}

		if(des_course(v)[1].length != 0){
			let dc = des_course(v);
			return Some(...dc[1].map(v => Course(dc[0], v)));
		}
			
		console.error("unexpected thing:", v);
	};

	let fstr = str.map(fix_str);
	let farr = arr.map(req => {
		let arr = req.filter(v => Array.isArray(v));
		let str = req.filter(v => !Array.isArray(v));

		let fstr = str.map(fix_str);
		let farr = arr.map(fix_req);

		return Some(...fstr, ...farr);
	});


	return simp_tree(All(...fstr, ...farr));
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





console.log(JSON.stringify(courses));




