
var _charts = [ 'new', 'changed', 'unchanged', 'deleted', 'total', 'scanned' ];
var _charts_obj = [];
var _chart_stats = null;
var _stats_data = [];
var initialized = false;

var _time_human_readable = function(d) {
	str = '';
	var days = Math.floor((d % 31536000) / 86400);
	var hours = Math.floor(((d % 31536000) % 86400) / 3600);
	var minutes = Math.floor((((d % 31536000) % 86400) % 3600) / 60);
	var seconds = (((d % 31536000) % 86400) % 3600) % 60;
	if (days > 0) {
		str += days;
		if (days > 1) {
			str += ' days ';
		} else {
			str += ' day ';
		}
	}
	if (hours > 0) {
		str += pad(hours,2)+'H ';
	}
	str += pad(minutes,2)+'m '+pad(seconds,2)+'s';
	return str;
};

var _client = function() {
	if (!initialized) {
		$.each(_charts, function(i, j) {
			tmp = nv.models.stackedAreaChart()
							.x(function(d) { return d[0] })
							.y(function(d) { return d[1] })
							.useInteractiveGuideline(true)
							.color(d3.scale.category20c().range())
							.margin({bottom: 105, left: 80})
							;

			tmp.xAxis.showMaxMin(true).tickFormat(function(d) { return d3.time.format('%x %X')(new Date(d)) }).rotateLabels(-45);

			tmp.yAxis.tickFormat(d3.format('f'));

			_charts_obj.push({ 'key': 'chart_'+j, 'obj': tmp, 'data': [] });
		});
		_chart_stats = nv.models.linePlusBarChart()
					.color(d3.scale.category10().range())
					.x(function(d,i) { return i })
					.y(function(d) { return d[1] })
					.margin({bottom: 105, left: 80})
					.focusEnable(false)
					;

		_chart_stats.xAxis.tickFormat(function(d) {
			var dx = data[0].values[d] && data[0].values[d][0] || 0;
			return d3.time.format('%x %X')(new Date(dx))
		}).rotateLabels(-45).showMaxMin(true);

		_chart_stats.y1Axis.tickFormat(function(d) { return _time_human_readable(d) }); // Time

		_chart_stats.y2Axis.tickFormat(function(d) { return _bytes_human_readable(d, false) }); // Size

		_chart_stats.bars.forceY([0]);
	}
	url = '{{ url_for("api.client_stats", name=cname, server=server) }}';
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
				if (!d.results) {
					if (d.notif) {
						$.each(d.notif, function(i, n) {
							notif(n[0], n[1]);
						});
					}
					$('.mycharts').each(function() {
						$(this).parent().hide();
					});
					return;
				}
				$('.mycharts').each(function() {
					$(this).parent().show();
				});
				$.each(d.results, function(a, j) {
					if (j[c] !== undefined) {
						val = parseFloat(j[c][l]);
						values.push([ parseInt(j.end)*1000, val ]);
						push = true;
					} else {
						values.push([ parseInt(j.end)*1000, 0 ]);
					}
					if (stats) {
						size.push([ parseInt(j.end)*1000, j.received ]);
						duration.push([ parseInt(j.end)*1000, j.duration ]);
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
	});
	_redraw();
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
