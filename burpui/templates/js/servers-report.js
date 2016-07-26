
var _charts = [ 'repartition', 'size', 'files', 'backups' ];
var _charts_obj = [];
var initialized = false;

var _servers = function() {
	if (!initialized) {
		$.each(_charts, function(i, j) {
			tmp =  nv.models.pieChart()
				.x(function(d) { return d.label })
				.y(function(d) { return d.value })
				.showLabels(true)
				.labelThreshold(.05)
				.labelType("percent")
				.valueFormat(d3.format('f'))
				.color(d3.scale.category20c().range())
				.labelThreshold(.05)
				.donutRatio(0.55)
				.donut(true)
				;

			tmp.tooltip.contentGenerator(function(obj) { return '<h3>'+obj.data.label+'</h3><p>'+(j == 'size' ? _bytes_human_readable(obj.data.value, false) : obj.data.value)+'</p>'; });

			_charts_obj.push({ 'key': 'chart_'+j, 'obj': tmp, 'data': [] });
		});
	}
	url = '{{ url_for("api.servers_report") }}';
	$.getJSON(url, function(d) {
		rep = [];
		size = [];
		files = [];
		rep = [];
		backups = [];
		$('.mycharts').each(function() {
			$(this).parent().show();
		});
		$.each(d['servers'], function(k, s) {
			size.push({'label': s.name, 'value': s.stats.totsize});
			files.push({'label': s.name, 'value': s.stats.total});
			if (s.stats.windows > 0) {
				rep.push({'label': s.name + ' - Windows', 'value': s.stats.windows});
			}
			if (s.stats.linux > 0) {
				rep.push({'label': s.name + ' - Unix/Linux', 'value': s.stats.linux});
			}
			if (s.stats.unknown > 0) {
				rep.push({'label': s.name + ' - Unknown', 'value': s.stats.unknown});
			}
		});
		$.each(d['backups'], function(k, b) {
			backups.push({'label': b.name, 'value': b.number});
		});
		$.each(_charts_obj, function(i, c) {
			switch (c.key) {
				case 'chart_repartition':
					c.data = rep;
					break;
				case 'chart_size':
					c.data = size;
					break;
				case 'chart_files':
					c.data = files;
					break;
				case 'chart_backups':
					c.data = backups;
					break;
			}
		});
		_redraw();
	})
	.fail(myFail)
	.fail(function () {
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
	initialized = true;
};
