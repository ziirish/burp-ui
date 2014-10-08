
var _charts = [ 'repartition', 'size', 'files', 'backups' ];
var _charts_obj = [];
var initialized = false;

var _bytes_human_readable = function(bytes, si) {
	var thresh = si ? 1000 : 1024;
	if(bytes < thresh) return bytes + ' B';
	var units = si ? ['kB','MB','GB','TB','PB','EB','ZB','YB'] : ['KiB','MiB','GiB','TiB','PiB','EiB','ZiB','YiB'];
	var u = -1;
	do {
		bytes /= thresh;
		++u;
	} while(bytes >= thresh);
	return bytes.toFixed(1)+' '+units[u];
};

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
				.tooltipContent(function(key, y, e, graph) { return '<h3>'+key+'</h3><p>'+(j == 'size' ? _bytes_human_readable(y, false) : y)+'</p>'; })
				.labelThreshold(.05)
				.donutRatio(0.55)
				.donut(true)
				;

			_charts_obj.push({ 'key': 'chart_'+j, 'obj': tmp, 'data': [] });
		});
	}
	url = '{{ url_for("clients_report_json", server=server) }}';
	$.getJSON(url, function(d) {
		rep = [];
		size = [];
		files = [];
		backups = {};
		windows = 0;
		nonwin = 0;
		unknown = 0;
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
		$.each(d.results[0]['clients'], function(k, c) {
			if (c.stats.windows == 'true') {
				windows++;
			} else if (c.stats.windows == 'unknown') {
				unknown++;
			} else {
				nonwin++;
			}
			size.push({'label': c.name, 'value': c.stats.totsize});
			files.push({'label': c.name, 'value': c.stats.total.total});
		});
		$.each(d.results[0]['backups'], function(k, c) {
			if (c.name in backups) {
				backups[c.name]++;
			} else {
				backups[c.name] = 1;
			}
		});
		rep = [{'label': 'Windows', 'value': windows}, {'label': 'Unix/Linux', 'value': nonwin}, {'label': 'Unknwon', 'value': unknown}];
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
