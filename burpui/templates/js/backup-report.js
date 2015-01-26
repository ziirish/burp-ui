
var _charts = [ 'new', 'changed', 'unchanged', 'deleted', 'total', 'scanned' ];
var _charts_obj = [];
var chart_unified;
var data_unified = [];
var initialized = false;

var _client = function() {
	if (!initialized) {
		$.each(_charts, function(i, j) {
			tmp =  nv.models.pieChart()
				.x(function(d) { return d.label })
				.y(function(d) { return parseInt(d.value) })
				.showLabels(true)
				.labelThreshold(.05)
				.labelType("percent")
				.donut(true)
				.valueFormat(d3.format('f'))
				.color(d3.scale.category20c().range())
				.tooltipContent(function(key, y, e, graph) { return '<h3>'+key+'</h3><p>'+y+' '+j+'</p>'; })
				.donutRatio(0.55);

			_charts_obj.push({ 'key': 'chart_'+j, 'obj': tmp, 'data': [] });
		});
		chart_unified = nv.models.multiBarHorizontalChart()
				.x(function(d) { return d.label })
				.y(function(d) { return parseInt(d.value) })
				.showValues(false)
				.tooltips(true)
				.valueFormat(d3.format('f'))
				.tooltipContent(function(key, x, y, e, graph) { return '<h3>' + key + ' - ' + x + '</h3><p>' + y + '</p>'; })
				.color(d3.scale.category20().range())
				.showControls(false);

		chart_unified.yAxis.tickFormat(d3.format(',.0f'));
	}
	url = '{{ url_for("client_stat_json", name=cname, backup=nbackup, server=server) }}';
	$.getJSON(url, function(d) {
		j = d.results;
		var _fields = [];
		if (j && j.encrypted) {
			_fields = [ 'dir', 'files_enc', 'hardlink', 'softlink' ];
		} else {
			_fields = [ 'dir', 'files', 'hardlink', 'softlink' ];
		}
		if (!j) {
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
		$.each(_charts, function(k, l) {
			data = [];
			$.each(_fields, function(i, c) {
				if (j[c] !== undefined && parseInt(j[c][l]) != 0) {
					data.push({ 'label': c, 'value': parseInt(j[c][l]) });
				}
			});
			if (data.length > 0) {
				var dis = (l === 'total' || l === 'unchanged' || l === 'scanned');
				data_unified.push({ 'key': l, 'values': data, disabled: dis });
			}
			$.each(_charts_obj, function(i, c) {
				if (c.key === 'chart_'+l) {
					if (data.length > 0 && j.windows != 'true') {
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
		d3.select('#chart_combined svg')
			.datum(data_unified)
			.transition().duration(500)
			.call(chart_unified);

		nv.utils.windowResize(chart_unified.update);
	});
	initialized = true;
};
