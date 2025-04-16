let d3 = require('d3');
window.d3 = d3;

//let data := [{source:"",target:"",type:""}]


let gen_graph = (suits) => {
	function linkArc(d) {
		const r = Math.hypot(d.target.x - d.source.x, d.target.y - d.source.y);
		return `
    M${d.source.x},${d.source.y}
    A${r},${r} 0 0,1 ${d.target.x},${d.target.y}
  `;
	}

	let drag = simulation => {

		function dragstarted(event, d) {
			if (!event.active) simulation.alphaTarget(0.3).restart();
			d.fx = d.x;
			d.fy = d.y;
		}

		function dragged(event, d) {
			d.fx = event.x;
			d.fy = event.y;
		}

		function dragended(event, d) {
			if (!event.active) simulation.alphaTarget(0);
			d.fx = null;
			d.fy = null;
		}

		return d3.drag()
			.on("start", dragstarted)
			.on("drag", dragged)
			.on("end", dragended);
	}

	const width = 928;
	const height = 600;
	const types = Array.from(new Set(suits.map(d => d.type)));
	const nodes = Array.from(new Set(suits.flatMap(l => [l.source, l.target])), id => ({id}));
	const links = suits.map(d => Object.create(d))

	const color = d3.scaleOrdinal(types, d3.schemeCategory10);

	const simulation = d3.forceSimulation(nodes)
		.force("link", d3.forceLink(links).id(d => d.id))
		.force("charge", d3.forceManyBody().strength(-400))
		.force("x", d3.forceX())
		.force("y", d3.forceY());

	const svg = d3.create("svg")
		.attr("viewBox", [-width / 2, -height / 2, width, height])
		.attr("width", width)
		.attr("height", height)
		.attr("style", "width: 90vw; height: 90vh; font: 12px sans-serif;");

    function updateWindow(e){
        x = window.clientWidth;
        y = window.clientHeight;

        svg.attr("width", x).attr("height", y);
    }
    d3.select(window).on('resize.updatesvg', updateWindow);
  updateWindow();

	// Per-type markers, as they don't inherit styles.
	svg.append("defs").selectAll("marker")
		.data(types)
		.join("marker")
		.attr("id", d => `arrow-${d}`)
		.attr("viewBox", "0 -5 10 10")
		.attr("refX", 15)
		.attr("refY", -0.5)
		.attr("markerWidth", 6)
		.attr("markerHeight", 6)
		.attr("orient", "auto")
		.append("path")
		.attr("fill", color)
		.attr("d", "M0,-5L10,0L0,5");

	const link = svg.append("g")
		.attr("fill", "none")
		.attr("stroke-width", 1.5)
		.selectAll("path")
		.data(links)
		.join("path")
		.attr("stroke", d => color(d.type))
		.attr("marker-end", d => `url(${new URL(`#arrow-${d.type}`, location)})`);

	const node = svg.append("g")
		.attr("fill", "currentColor")
		.attr("stroke-linecap", "round")
		.attr("stroke-linejoin", "round")
		.selectAll("g")
		.data(nodes)
		.join("g")
		.call(drag(simulation));

	const circle = node.append("circle")
		.attr("stroke", "white")
		.attr("stroke-width", 1.5)
		.attr("r", 4);

	const text1 = node.append("text")
		.attr("x", 8)
		.attr("y", "0.31em")
		.text(d => d.id)

    const text2 = text1
		.clone(true).lower()
		.attr("fill", "none")
		.attr("stroke", "white")
		.attr("stroke-width", 3);

	simulation.on("tick", () => {
		link.attr("d", linkArc);
		circle.attr("cx", d => d.x)
          .attr("cy", d => d.y);
        text1.attr("dx", d => d.x)
          .attr("dy", d => d.y)
        text2.attr("dx", d => d.x)
          .attr("dy", d => d.y)
	});

	let myZoom = d3.zoom().on('zoom', handleZoom);

	function handleZoom(e) {
		link.attr("transform", e.transform);
		node.attr("transform", e.transform);
	}

	svg.call(myZoom);

	Object.assign(svg.node(), {scales: {color}});
	return svg.node();
};

let graph = [];

let get_edges = (course, type, graph, tr) => ({
  "true": () => null,
  "false": () => null,
  "some": () => tr.req.forEach(v => get_edges(course, type, graph, v)),
  "all": () => tr.req.forEach(v => get_edges(course, type, graph, v)),
  "course": () => graph.push({source: tr.dept + " " + tr.number, target: course, type}),
  "standing": () => null
})[tr.type](tr)

data.forEach(v => {
  get_edges(v.id.toLowerCase(), "prereq", graph, v.prereq)
  get_edges(v.id.toLowerCase(), "coreq", graph, v.coreq)
  get_edges(v.id.toLowerCase(), "preorco", graph, v.preorco)
});

graph = graph.filter(v => +v.target.match(/[0-9]+/)[0] < 5000)
	.filter(v => +v.source.match(/[0-9]+/)[0] < 5000)

paper.replaceChildren(gen_graph(graph))
