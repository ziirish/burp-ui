
var _charts = [ 'new', 'changed', 'unchanged', 'deleted', 'total', 'scanned' ];
var _charts_obj = [];
var _chart_stats = null;
var _stats_data = [];
var initialized = false;

var _client = function() {
	if (!initialized) {
		$.each(_charts, function(i, j) {
			tmp = nv.models.stackedAreaChart()
							.x(function(d) { return d3.time.format.iso.parse(d[0]) })
							.y(function(d) { return d[1] })
							.useInteractiveGuideline(true)
							.color(d3.scale.category20c().range())
							.margin({bottom: 115, left: 100})
							;

			tmp.xAxis.showMaxMin(true).tickFormat(function(d) { console.log(d); return d3.time.format('%x %X')(new Date(d)) }).rotateLabels(-45);

			tmp.yAxis.tickFormat(d3.format('f'));

			_charts_obj.push({ 'key': 'chart_'+j, 'obj': tmp, 'data': [] });
		});
		_chart_stats = nv.models.linePlusBarChart()
					.color(d3.scale.category10().range())
					.x(function(d,i) { return i })
					.y(function(d) { return d[1] })
					.margin({bottom: 115, left: 100, right: 80})
					.focusEnable(false)
					;

		_chart_stats.xAxis.tickFormat(function(d) {
			var dx = data[0].values[d] && data[0].values[d][0] || 0;
			return d3.time.format('%x %X')(new Date(dx))
		}).rotateLabels(-45).showMaxMin(true);

		_chart_stats.y1Axis.tickFormat(function(d) { return _time_human_readable(d) }); // Time

		_chart_stats.y2Axis.tickFormat(function(d) { return _bytes_human_readable(d, false) }); // Size

		_chart_stats.tooltip.contentGenerator(function(d) {
			if (d === null) {
				return '';
			}

			var title = 'Bytes received';
			var duration = false;
			if ('data' in d) {
				title = 'Duration';
				duration = true;
			}

			var table = d3.select(document.createElement("table"));
			var theadEnter = table.selectAll("thead")
				.data([d])
				.enter().append("thead");

			theadEnter.append("tr")
				.append("td")
				.attr("colspan", 3)
				.append("strong")
				.classed("x-value", true)
				.html(title);

			var tbodyEnter = table.selectAll("tbody")
				.data([d])
				.enter().append("tbody");

			var trowEnter = tbodyEnter.selectAll("tr")
				.data(function(p) { return p.series})
				.enter()
				.append("tr")
				.classed("highlight", function(p) { return p.highlight});

			trowEnter.append("td")
				.classed("legend-color-guide",true)
				.append("div")
				.style("background-color", function(p) { return p.color});

			trowEnter.append("td")
				.classed("key",true)
				.classed("total",function(p) { return !!p.total})
				.html(function(p, i) { 
					if (duration) {
						return _time_human_readable(p.value);
					}
					return _bytes_human_readable(p.value, false);
				});

			trowEnter.selectAll("td").each(function(p) {
				if (p.highlight) {
				var opacityScale = d3.scale.linear().domain([0,1]).range(["#fff",p.color]);
				var opacity = 0.6;
				d3.select(this)
					.style("border-bottom-color", opacityScale(opacity))
					.style("border-top-color", opacityScale(opacity))
				;
				}
			});

			var html = table.node().outerHTML;
			if (d.footer !== undefined)
				html += "<div class='footer'>" + d.footer + "</div>";
			return html;	
		});

		_chart_stats.bars.forceY([0]);
	}
	url = '{{ url_for("api.client_report", name=cname, server=server) }}';
	$.getJSON(url, function(d) {
		var _fields = [ 'dir', 'files', 'hardlink', 'softlink', 'files_enc', 'meta', 'meta_enc', 'special', 'efs', 'vssheader', 'vssheader_enc', 'vssfooter', 'vssfooter_enc' ];
		var stats = true;
		$.each(_charts, function(k, l) {
			data = [];
			$.each(_fields, function(i, c) {
				values = [];
				size = [];
				duration = [];
				push = false;
				$('.mycharts').each(function() {
					$(this).parent().show();
				});
				$.each(d, function(a, j) {
					if (j[c] !== undefined) {
						val = parseFloat(j[c][l]);
						values.push([ j.end, val ]);
						push = true;
					} else {
						values.push([ j.end, 0 ]);
					}
					if (stats) {
						size.push([ j.end, j.received ]);
						duration.push([ j.end, j.duration ]);
					}
				});
				if (stats) {
					stats = false;
					_stats_data = [
						{'key': 'Duration', 'bar': true, 'values': duration},
						{'key': 'Bytes received', 'values': size}
					]
				}
				if (push) {
					data.push({ 'key': c, 'values': values });
				}
			});
			$.each(_charts_obj, function(i, c) {
				if (c.key === 'chart_'+l) {
					if (data.length > 0) {
						c.data = data;
						$('#chart_'+l).parent().show();
					} else {
						$('#chart_'+l).parent().hide();
					}
					return false;
				}
			});
		});
		_redraw();
	})
	.fail(myFail)
	.fail(function() {
		$('.mycharts').each(function() {
			$(this).parent().hide();
		});
	});
};

var _redraw = function() {
	$.each(_charts_obj, function(i, j) {

		nv.addGraph(function() {

			d3.select('#'+j.key+' svg')
				.datum(j.data)
				.transition().duration(500)
				.call(j.obj);

			nv.utils.windowResize(j.obj.update);

			return j.obj;
		});
	});

	nv.addGraph(function() {

		d3.select('#chart_stats svg')
			.datum(_stats_data)
			.transition().duration(500)
			.call(_chart_stats);

		nv.utils.windowResize(_chart_stats.update);

		return _chart_stats;
	});

	initialized = true;
};
