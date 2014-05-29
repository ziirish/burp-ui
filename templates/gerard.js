var pad = function (num, size) {
	var s = "0000000" + num;
	return s.substr(s.length-size);
}

var _check_running = function() {
	url = '{{ url_for("backup_running") }}';
	$.getJSON(url, function(data) {
		if (data.results) {
			$('#toblink').addClass('blink');
		} else {
			$('#toblink').removeClass('blink');
		}
	});
};

/***
 * _clients_bh: Bloodhound object used for the autocompletion of the input field
 */
var _clients_bh = new Bloodhound({	
	datumTokenizer: Bloodhound.tokenizers.obj.whitespace('name'),
	queryTokenizer: Bloodhound.tokenizers.whitespace,
	limit: 10,
	prefetch: {
		url: '{{ url_for("clients") }}',
		filter: function(list) {
			return list.results;
		}
	}
});

_clients_bh.initialize();

/***
 * Map out _clients_bh to our input with the typeahead plugin
 */
$('#input-client').typeahead(null, {
	name: 'clients',
	displayKey: 'name',
	source: _clients_bh.ttAdapter()
});


{% if clients and overview %}
/***
 * Here is the 'clients' part
 * It is available on the global clients view
 */

/***
 * First we map some burp status with some style
 */
var __status = {
	'client crashed': 'danger',
	'server crashed': 'danger',
	'running': 'info',
};

/***
 * _clients: function that retrieve up-to-date informations from the burp server
 * JSON format:
 * {
 *   "results": [
 *     {
 *       "last": "2014-05-12 19:40:02",
 *       "name": "client1",
 *       "state": "idle"
 *     },
 *     {
 *       "last": "never",
 *       "name": "client2",
 *       "state": "idle"
 *     }
 *   ]
 * }
 *  The JSON is then parsed into a table
 */
var _clients = function() {
	url = '{{ url_for("clients") }}';
	$.getJSON(url, function(data) {
		$('#table-clients > tbody:last').empty();
		$.each(data.results, function(j, c) {
			clas = '';
			if (__status[c.state] != undefined) {
				clas = ' '+__status[c.state];
			}
			$('#table-clients > tbody:last').append('<tr class="clickable'+clas+'" style="cursor: pointer;"><td><a href="{{ url_for("client") }}?name='+c.name+'" style="color: inherit; text-decoration: inherit;">'+c.name+'</a></td><td>'+c.state+'</td><td>'+c.last+'</td></tr>');
		});
	});
};
{% endif %}

{% if client and overview %}
/***
 * Here is the 'client' part
 * It is available on the 'specific' client view
 */

/***
 * _client: function that retrieve up-to-date informations from the burp server about a specific client
 * JSON format:
 * {
 *   "results": [
 *     {
 *       "date": "2014-05-12 19:40:02",
 *       "number": "254"
 *     },
 *     {
 *       "date": "2014-05-11 21:20:03",
 *       "number": "253"
 *     }
 *   ]
 * }
 * The JSON is then parsed into a table
 */
var _client = function() {
	url = '{{ url_for("client_json", name=cname) }}';
	$.getJSON(url, function(data) {
		$('#table-client >tbody:last').empty();
		if (data.results.length == 0) {
			$('#table-client').hide();
			$('#client-alert').show();
		} else {
			$.each(data.results.reverse(), function(j, c) {
				$('#table-client> tbody:last').append('<tr class="clickable" style="cursor: pointer;"><td><a href="{{ url_for("client_browse", name=cname) }}?backup='+c.number+'" style="color: inherit; text-decoration: inherit;">'+pad(c.number, 7)+'</a></td><td>'+c.date+'</td></tr>');
			});
		}
	});
};
{% endif %}
{% if backup and report and client %}
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
//				.stacked(true)
				.tooltipContent(function(key, x, y, e, graph) { return '<h3>' + key + ' - ' + x + '</h3><p>' + y + '</p>'; })
				.color(d3.scale.category20().range())
				.showControls(false);

		chart_unified.yAxis.tickFormat(d3.format(',.0f'));
	}
	url = '{{ url_for("client_stat_json", name=cname, backup=nbackup) }}';
	$.getJSON(url, function(d) {
		var _fields = [ 'dir', 'files', 'hardlink', 'softlink' ];
		j = d.results;
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
					if (data.length > 0 && !j.windows) {
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
{% endif %}
{% if not backup and report and client %}
var _charts = [ 'new', 'changed', 'unchanged', 'deleted', 'total', 'scanned' ];
var _charts_obj = [];
var _chart_stats = null;
var _stats_data = [];
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
					;

		_chart_stats.xAxis.tickFormat(function(d) {
			var dx = data[0].values[d] && data[0].values[d][0] || 0;
			return d3.time.format('%x %X')(new Date(dx))
		}).rotateLabels(-45).showMaxMin(true);

		_chart_stats.y1Axis.tickFormat(function(d) { return _time_human_readable(d) }); // Time

		_chart_stats.y2Axis.tickFormat(function(d) { return _bytes_human_readable(d, false) }); // Size

		_chart_stats.bars.forceY([0]);
	}
	url = '{{ url_for("client_stat_json", name=cname) }}';
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
				$.each(d.results, function(a, j) {
					if (j[c] !== undefined) {
						val = parseFloat(j[c][l]);
						values.push([ parseInt(j.end)*1000, val ]);
						push = true;
					} else {
						values.push([ parseInt(j.end), 0 ]);
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
{% endif %}
{% if live %}
_live = function() {
	url = '{{ url_for("running_clients") }}';
	html = ''
	$.getJSON(url, function(data) {
		if (data.results.length === 0) {
			document.location = '{{ url_for("home") }}';
		}
		$.each(data.results, function(i, c) {
			u = '{{ url_for("render_live_tpl") }}?name='+c;
			$.get(u, function(d) {
				html += d;
			});
		});
	});
	$('#live-container').html(html);
};
{% endif %}

var _async_ajax = function(b) {
	$.ajaxSetup({
		async: b
	});
}

$(function() {
	_async_ajax(false);

	/***
	 * Action on the 'refresh' button
	 */
	$('#refresh').on('click', function(e) {
		e.preventDefault();
		{% if clients %}
		_clients();
		{% endif %}
		{% if client %}
		_client();
		{% endif %}
		{% if live %}
		_live();
		{% endif %}
	});

	/***
	 * trigger action on the 'search field' when the 'enter' key is pressed
	 */
	var search = $('input[id="input-client"]');
	search.keypress(function(e) {
		if (e.which == 13) {
			window.location = '{{ url_for("client") }}?name='+search.val();
		}
	});

	/***
	 * add a listener to the '.clickable' element dynamically added in the document (see _client and _clients function)
	 */
	$( document ).on('click', '.clickable', function() {
		window.location = $(this).find('a').attr('href');
	});

	/***
	 * initialize our page if needed
	 */
	{% if clients %}
	_clients();
	{% endif %}
	{% if client %}
	_client();
	{% endif %}
	{% if live %}
	_live();
	{% endif %}

	{% if not report %}
	/***
	 * auto-refresh our page if needed
	 */
	var auto_refresh = setInterval(function() {
		{% if clients %}
		_clients();
		{% endif %}
		{% if client %}
		_client();
		{% endif %}
		{% if live %}
		_live();
		{% endif %}
		return;
	}, {{ config.REFRESH * 1000 }});
	{% endif %}

	var refresh_running = setInterval(function () {
		_check_running();
	}, {{ config.REFRESH * 1000 }});

	{% if tree %}
	/***
	 * Here is our tree to browse a specific backup
	 * The tree is first initialized with the 'root' part of the backup.
	 * JSON example:
	 * {
	 *   "results": [
	 *     {
	 *       "name": "/",
	 *       "parent": "",
	 *       "type": "d"
	 *     }
	 *   ]
	 * }
	 * This JSON is then parsed into another one to initialize our tree.
	 * Each 'directory' is expandable.
	 * A new JSON is returned for each one of then on-demand.
	 * JSON output:
	 * {
	 *   "results": [
	 *     {
	 *       "name": "etc", 
	 *       "parent": "/", 
	 *       "type": "d"
	 *     }, 
	 *     {
	 *       "name": "home", 
	 *       "parent": "/", 
	 *       "type": "d"
	 *     }
	 *   ]
	 * }
	 */
	$("#tree").fancytree({
		extensions: ["glyph", "table", "gridnav", "filter"],
		glyph: {
			map: {
				doc: "glyphicon glyphicon-file",
				docOpen: "glyphicon glyphicon-file",
				checkbox: "glyphicon glyphicon-unchecked",
				checkboxSelected: "glyphicon glyphicon-check",
				checkboxUnknown: "glyphicon glyphicon-share",
				error: "glyphicon glyphicon-warning-sign",
				expanderClosed: "glyphicon glyphicon-plus-sign",
				expanderLazy: "glyphicon glyphicon-plus-sign",
				// expanderLazy: "glyphicon glyphicon-expand",
				expanderOpen: "glyphicon glyphicon-minus-sign",
				// expanderOpen: "glyphicon glyphicon-collapse-down",
				folder: "glyphicon glyphicon-folder-close",
				folderOpen: "glyphicon glyphicon-folder-open",
				loading: "glyphicon glyphicon-refresh"
				// loading: "icon-spinner icon-spin"
			}
		},
		source: function() { 
			r = [];
			$.getJSON('{{ url_for("client_tree", name=cname, backup=nbackup) }}', function(data) {
				$.each(data.results, function(j, c) {
					l = (c.type === "d");
					f = (c.type === "d");
					s = {title: c.name, key: c.name, lazy: l, folder: f, uid: c.uid, gid: c.gid, date: c.date, mode: c.mode, size: c.size, inodes: c.inodes};
					r.push(s);
				});
			});
			return r;
		},
		lazyLoad: function(event, data) {
			var node = data.node;
			// ugly hack to display a "loading" icon while retrieving data
			node._isLoading = true;
			node.renderStatus();
			r = [];
			p = node.key;
			if (p !== "/") p += '/';
			$.getJSON('{{ url_for("client_tree", name=cname, backup=nbackup) }}?root='+p, function(data) {
				$.each(data.results, function(j, c) {
					l = (c.type === "d");
					f = (c.type === "d");
					s = {title: c.name, key: c.parent+c.name, lazy: l, folder: f, uid: c.uid, gid: c.gid, date: c.date, mode: c.mode, size: c.size, inodes: c.inodes};
					r.push(s);
				});
			});
			data.result = r;
			node._isLoading = false;
			node.renderStatus();
		},
		/*
		// TODO: make it recursively loadable
		loadChildren: function(event, data) {
			data.node.visit(function(subNode){
				if( subNode.isUndefined() && subNode.isExpanded() ) {
					subNode.load();
				}
			});
		},
		*/
		selectMode: 1,
		scrollParent: $(window),
		renderColumns: function(event, data) {
			var node = data.node;
			$tdList = $(node.tr).find(">td");

			$tdList.eq(1).text(node.data.mode);
			$tdList.eq(2).text(node.data.uid);
			$tdList.eq(3).text(node.data.gid);
			$tdList.eq(4).text(node.data.size);
			$tdList.eq(5).text(node.data.date);
		}
	});

	var tree = $("#tree").fancytree("getTree");

	$("input[name=search-tree]").keyup(function(e){
		var n,
		leavesOnly = $("#leavesOnly").is(":checked"),
		match = $(this).val();

		if(e && e.which === $.ui.keyCode.ESCAPE || $.trim(match) === ""){
			$("#btnResetSearch").click();
			return;
		}
		if($("#regex").is(":checked")) {
			// Pass function to perform match
			n = tree.filterNodes(function(node) {
				return new RegExp(match, "i").test(node.title);
			}, leavesOnly);
		} else {
			// Pass a string to perform case insensitive matching
			n = tree.filterNodes(match, leavesOnly);
		}
		$("#btnResetSearch").attr("disabled", false);
		$("span#matches").text("(" + n + " matches)");
	});

	$("#btnResetSearch").click(function(e){
		$("input[name=search-tree]").val("");
		$("span#matches").text("");
		tree.clearFilter();
	}).attr("disabled", true);

	$("input#hideMode").change(function(e){
		tree.options.filter.mode = $(this).is(":checked") ? "hide" : "dimm";
		tree.clearFilter();
		$("input[name=search-tree]").keyup();
	});
	$("input#leavesOnly").change(function(e){
		tree.clearFilter();
		$("input[name=search-tree]").keyup();
	});
	$("input#regex").change(function(e){
		tree.clearFilter();
		$("input[name=search-tree]").keyup();
	});

	{% endif %}
});
