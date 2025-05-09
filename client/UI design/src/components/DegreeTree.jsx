import React, { useEffect, useRef } from 'react'
import * as d3                     from 'd3'
import { get_degree }             from '../api'
import './DegreeTree.css'

export default function DegreeTree({ degreeId }) {
  const container = useRef(null)

  useEffect(() => {
    const sel = d3.select(container.current)
    sel.selectAll('*').remove()

    if (!degreeId) return // nothing to draw yet

    get_degree(degreeId)
      .then(raw => {
        // extract the actual degree‐node payload
        const treeData = raw.degree ?? raw.node ?? raw

        // tell d3 how to descend:
        //  • if there's an "options" array, each opt might wrap a .node
        //  • else no children
        const root = d3.hierarchy(treeData, d =>
          Array.isArray(d.options)
            ? d.options.map(opt => opt.node ?? opt)
            : null
        )

        // layout
        d3.tree().nodeSize([24, 180])(root)

        // make our svg
        const svg = sel.append('svg')
          .attr('class','degree-tree')
          .attr('width','100%')
          .attr('height','100%')

        // optional: pan & zoom
        const g = svg.append('g').attr('transform','translate(12,12)')
        svg.call(
          d3.zoom()
            .scaleExtent([0.5,2])
            .on('zoom', e => g.attr('transform', e.transform))
        )

        // draw links
        g.append('g')
          .selectAll('path')
          .data(root.links())
          .join('path')
          .attr('class','link')
          .attr('d', d3.linkHorizontal()
            .x(d => d.y)
            .y(d => d.x)
          )

        // draw nodes
        const node = g.append('g')
          .selectAll('g')
          .data(root.descendants())
          .join('g')
          .attr('class','node')
          .attr('transform', d => `translate(${d.y},${d.x})`)

        node.append('circle').attr('r', 6)

        // smart label fallback
        node.append('text')
          .attr('dy','0.32em')
          .attr('x', d => d.children ? -12 : 12)
          .attr('text-anchor', d => d.children ? 'end' : 'start')
          .text(d => {
            const { info, name, id, dept, number } = d.data
            if (info) return info
            if (name) return name
            if (dept && number) return `${dept.toUpperCase()} ${number}`
            if (id) return id
            return ''  
          })
      })
      .catch(err => {
        console.error('X DegreeTree load error:', err)
        sel.append('div')
          .style('color','red')
          .text('Failed to load requirements')
      })
  }, [degreeId])

  return (
    <div className="degree-tree-container" ref={container} />
  )
}
