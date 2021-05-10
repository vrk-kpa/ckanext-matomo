'use strict';

ckan.module('chartData-column', function($) {
  return {
    initialize: function($) {
      let data = chartData[this.options.field].map((x) => Object.assign({}, x));
      
      const biggest = data.reduce((biggest, x) => {
        return biggest.value > x.value ? biggest : x
      }, 0);

      data = data.map((x) => {
        x.ratio = x.value / biggest;
        return x;
      });

      const dateFormat = { year: 'numeric', month: 'short'}

      initColumnChart(
        this.el[0],
        data,
        biggest.value,
        this.options.title,
        this.options.legendx,
        this.options.legendy,
        (x) => {
          return x.value;
        },
        (x) => {
          return new Date(x.label).toLocaleDateString('en-US', dateFormat);
        },
      );
    },
  };
});

const initColumnChart = (element, data, biggest, title, legendX, legendY, getValue, getLabel) => {
  const render = () => {
    d3.select(element)
      .selectAll('*')
      .remove();
    
    const margin = 80;
    const W = 1000;
    const H = 600;
    const width = W - 2 * margin;
    const height = H - 2 * margin;

    const strokeColor = d3
      .scaleOrdinal()
      .range(hslLerp(0, 60, 50, 1.0, 360, 70, 60, 1.0, data.length, true));

    const fillColor = d3
      .scaleOrdinal()
      .range(hslLerp(0, 60, 70, 1.0, 360, 70, 80, 1.0, data.length, true));
      
    const svg = d3
      .select(element)
      .append('svg')
      .attr('viewBox', '0 0 ' + W + ' ' + H);
    
    const chart = svg
      .append('g')
      .attr('transform', `translate(${margin}, ${margin})`);
    
    const xScale = d3
      .scaleBand()
      .range([0, width])
      .domain(data.map(getLabel))
      .padding(0.4);
    
    const yScale = d3
      .scaleLinear()
      .range([height, 0])
      .domain([0, biggest * 1.05]);
    
    const makeYLines = () => d3.axisLeft().scale(yScale);
    
    chart
      .append('g')
      .attr('transform', `translate(0, ${height})`)
      .call(d3.axisBottom(xScale));
    
    chart.append('g').call(d3.axisLeft(yScale));
    
    chart
      .append('g')
      .attr('class', 'grid')
      .call(
        makeYLines()
          .tickSize(-width, 0, 0)
          .tickFormat(''),
      );
    
    const barGroups = chart
      .selectAll()
      .data(data)
      .enter()
      .append('g');
    
    barGroups
      .append('rect')
      .attr('class', 'bar')
      .attr('x', g => xScale(getLabel(g)))
      .attr('y', g => yScale(getValue(g)))
      .attr('height', g => height - yScale(getValue(g)))
      .attr('width', xScale.bandwidth())
      .style('fill', function(d, i) {
        return fillColor(1);
      })
      .style('stroke', function(d, i) {
        return strokeColor(1);
      });
    
    barGroups
      .append('text')
      .attr('class', 'value')
      .attr('x', a => xScale(getLabel(a)) + xScale.bandwidth() / 2)
      .attr('y', a => yScale(getValue(a)) - 10)
      .attr('text-anchor', 'middle')
      .text(a => `${getValue(a)}`);
    
    svg
      .append('text')
      .attr('class', 'label')
      .attr('x', - (height / 2) - margin)
      .attr('y', margin / 3)
      .attr('transform', 'rotate(-90)')
      .attr('text-anchor', 'middle')
      .text(legendY);
    
    svg
      .append('text')
      .attr('class', 'label')
      .attr('x', width / 2 + margin)
      .attr('y', height + margin * 1.5)
      .attr('text-anchor', 'middle')
      .text(legendX);
    
    svg
      .append('text')
      .attr('class', 'title')
      .attr('x', width / 2 + margin)
      .attr('y', 40)
      .attr('text-anchor', 'middle')
      .text(title);
  }

  render();
}
