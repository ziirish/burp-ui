
var _charts = [ 'repartition', 'size', 'files', 'backups' ];
var _charts_obj = [];
var initialized = false;

var _clients = function() {
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
	url = '{{ url_for("api.clients_report", server=server) }}';
	$.getJSON(url, function(d) {
		rep = [];
		size = [];
		files = [];
		backups = {};
		windows = 0;
		nonwin = 0;
		unknown = 0;
		$('.mycharts').each(function() {
			$(this).parent().show();
		});
		$.each(d['clients'], function(k, c) {
			if (c.stats.windows == 'true') {
				windows++;
			} else if (c.stats.windows == 'unknown') {
				unknown++;
			} else {
				nonwin++;
			}
			size.push({'label': c.name, 'value': c.stats.totsize});
			files.push({'label': c.name, 'value': c.stats.total});
		});
		$.each(d['backups'], function(k, c) {
			backups[c.name] = c.number;
		});
		rep = [{'label': 'Windows', 'value': windows}, {'label': 'Unix/Linux', 'value': nonwin}, {'label': 'Unknown', 'value': unknown}];
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
					data = [];
					$.each(backups, function(cl, num) {
						data.push({'label': cl, 'value': num});
					});
					c.data = data;
					break;
			}
		});
	})
	.fail(myFail)
	.fail(function () {
		$('.mycharts').each(function() {
			$(this).parent().hide();
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
	initialized = true;
};
