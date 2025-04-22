let fs = require("node:fs");
let request = require("request");
let jsdom = require("jsdom");

let list_files = path => fs.readdirSync(path);
let read_file = path => fs.readFileSync(path);
let write_file = (path, str) => fs.writeFileSync(path, str);



let scrape_index = async () => {
	let data = {};
	let body = await new Promise((resolve) => request("https://catalog.uni.edu/programrequirements/", (err, res, body) => {
		resolve(body);
	}));

	let doc = new jsdom.JSDOM(body);
	let dom = doc.window.document;

	let content = dom.getElementById("content").children[2];
	let k = [...content.children];

	let get_programs = (ul) => {
	  return [...ul.children].map(v => v.textContent.split("\n").map(v => v.trim()).filter(v => v));
	};

	let arr = k.map((v, i) => v.localName == "h4" ? [v.children[0].href, k[i+1].localName == "ul" ? get_programs(k[i+1]) : null] : null).filter(v => v);

	data.index = arr;

	data.pages = await Promise.all(
		arr.map(([url, programs], i) => 
			new Promise((resolve) => request(url, (err, res, body) => {
				resolve(body);
			}))
		)
	);

	write_file("raw_data.json", JSON.stringify(data));
};

let scrape_course = (el) => {
	let els = [...el.children];

	let title = els.find(v => v.classList.contains("courseblocktitle"));
	let descr = els.find(v => v.classList.contains("courseblockdesc"));

	let [_1, course, name, _2, hours] = title.textContent
		.trim()
		.match(/([^.]+)\.([^—]*)(—(.+)\.|\.)/)

	course = course.trim();
	name = name.trim();
	hours = hours?.match(/[0-9]+/g).map(v => +v) ?? [-1];

	let desc = [...descr.childNodes]
		.map(v => v.data ?? v.textContent)
		.map(v => v.trim())
		.filter(v => v);

	return {
		course,
		name,
		hours,
		desc
	};
}

let scrape_department = (dom, meta) => {
	let dept = {url: meta.url};
	let course_inv = dom.getElementById("courseinventorycontainer");
	let dept_page = dom.getElementById("textcontainer");

	if(course_inv){
		let courses = [...course_inv.children]
			.filter(v => v.classList.contains("courses"))
			.map(v => [...v.children]).flat()
			.filter(v => v.classList.contains("courseblock"))
			.map(scrape_course);
		dept.courses = courses;
	}

	if(dept_page){
		let [url, programs] = meta ?? [];
		programs ??= [];
		let strs = programs.flat()
			.map(v => v.split("(")[0])
			.map(v => v.trim())
			.filter(v => v);

		let els = [...dept_page.children].map((v, i) => [v, i]);
		
		let tables = els.filter(([v, i]) => v.classList.contains("sc_courselist"))
		.map(([table, ind]) => {
			for(let i = ind; i >= 0; i--){
				if(/H[0-9]/.test(els[i][0].nodeName)){
					let text = els[i][0].textContent.trim();
					if(text.at(-1) != ":")
						return [text, table];
				}
			}

			return null;
		}).filter(v => v)
		.map(([name, table]) => {
			let tbl = [...table.rows].map(v => [...v.cells].map(v => v.textContent.trim()));
			return {name, reqs: tbl};
		});

		dept.programs = tables;
	}

	return dept;
};


let hash = a => a.toLowerCase().match(/[a-z0-9]/g).join("");
let req_repl = Object.fromEntries(Object.entries(JSON.parse(read_file("req_repl.json"))).map(([k, v])=> [hash(k), v]));
let course_set = null;
let broken_reqs = {};

let structure_course = (course) => {
	let semester = course.desc.at(-1).match(/\(([^()]*)\)$/)?.[1];
	let desc = course.desc.join(" ");

	let prereq = desc.match(/Prerequisite\(s\):((\.[^]|[^.])*)\./);
	let coreq = desc.match(/Corequisite\(s\):((\.[^]|[^.])*)\./)?.[1] ?? "";
	let preorco = desc.match(/Prerequisite\(s\) or corequisite\(s\):((\.[^]|[^.])*)\./)?.[1] ?? "";

	prereq = prereq?.[1] ?? "";

	let fmt = (str) => {
		let reqs = str
			.split(";")
			.map(v => v.trim())
			.filter(v => v);

		let repl = reqs.filter(v => req_repl[hash(v)] != null).map(v => req_repl[hash(v)]);
		let keep = reqs.filter(v => req_repl[hash(v)] == null);

		//console.log("reqs", reqs, "maps to", reqs.map(v => req_repl[hash(v)]));

		
		let broken = keep.filter(v => !course_set.has(hash(v)));
		if(broken.length > 0){
			console.error(course.course, broken);
			broken.map(v => broken_reqs[v] = v);
		}

		return [keep, ...repl].flat();
	};


	prereq = fmt(prereq);
	coreq = fmt(coreq);
	preorco = fmt(preorco);

	//if(/^cs/i.test(course.course))
		//console.error(course.course, prereq, "\n\n\n\n\n");

	return {...course, desc, prereq, coreq, preorco, semester};
}

let structure_programs = (prog) => {
	let reqs = prog.reqs.map(v => v[0]);

	return prog;
}

let structure_data = (dept) => {
	let {programs, courses} = dept;

	if(courses){
		courses = courses.map(structure_course);
	}

	if(programs){
		programs = programs.map(structure_programs);
	}

	return {programs, courses};
};

(async () => {
	if(!list_files("./").includes("raw_data.json")){
		await scrape_index();
	}

	if(!list_files("./").includes("data.json")){
		let raw_data = JSON.parse(read_file("raw_data.json"));

		let dept_data = raw_data.pages.map((v, i) => scrape_department(new jsdom.JSDOM(v).window.document, raw_data.index[i]));

		write_file("data.json", JSON.stringify(dept_data));
	}

	let data = JSON.parse(read_file("data.json"));
	course_set = new Set(data.map(v => v.courses ? v.courses.map(v => hash(v.course)) : null).flat());
	
	write_file("structured_data.json", JSON.stringify(data.map(structure_data)));
	write_file("broken_reqs.json", JSON.stringify(broken_reqs));


})();
