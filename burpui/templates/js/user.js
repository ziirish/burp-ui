/***
 * The User page is managed with AngularJS for some parts.
 * Following is the AngularJS Application and Controller.
 */
var app = angular.module('MainApp', ['ngSanitize', 'frapontillo.bootstrap-switch', 'mgcrea.ngStrap']);

app.directive('compareTo', function() {
	return {
		require: "ngModel",
		scope: {
			otherModelValue: "=compareTo"
		},
		link: function(scope, element, attributes, ngModel) {
			ngModel.$validators.compareTo = function(modelValue) {
				return modelValue == scope.otherModelValue;
			};

			scope.$watch("otherModelValue", function() {
				ngModel.$validate();
			});
		}
	};
});

app.controller('UserCtrl', function($timeout, $scope, $http, $scrollspy) {
	$scope.spy = {};
	$scope.user = {
		oldPassword: '',
		newPassword: '',
		confPassword: ''
	};
	$scope.prefs = {};

	// Get the available pageLength
	var table = $('#table-sessions').DataTable();
	var settings = table.settings();
	$scope.lengthMenu = settings[0].aLengthMenu;

	// Available languages
	$scope.languages = [
		{% for key, val in config['LANGUAGES'].items() %}
		{ 'name': {{ val|tojson }}, 'id': {{ key|tojson }} },
		{% endfor %}
	];

	$http.get("{{ url_for('api.prefs_ui') }}", { headers: { 'X-From-UI': true } })
		.then(function(response) {
			$scope.prefs = response.data;

			$scope.prefs.language = '{{ g.locale }}';

			// current pageLength
			$scope.prefs.pageLength = table.page.len();
		});

	$scope.submitChangePrefs = function(e) {
		e.preventDefault();
		var form = $(e.target);
		var submit = form.find('button[type="submit"]');
		var sav = submit.html();
		submit.html('<i class="fa fa-fw fa-spinner fa-pulse" aria-hidden="true"></i>&nbsp;{{ _("Saving...") }}');
		submit.attr('disabled', true);
		table.page.len($scope.prefs.pageLength).draw();
		/* submit the data */
		$.ajax({
			url: form.attr('action'),
			type: 'POST',
			data: $scope.prefs,
			headers: { 'X-From-UI': true },
		})
		.fail(buiFail)
		.done(function(data) {
			notif(NOTIF_SUCCESS, "{{ _('Preferences successfuly saved') }}");
		})
		.always(function() {
			/* reset the submit button state */
			submit.html(sav);
			submit.attr('disabled', false);
		});
	};

	$scope.submitChangePass = function(e) {
		e.preventDefault();
		var form = $(e.target);
		submit = form.find('button[type="submit"]');
		sav = submit.html();
		submit.html('<i class="fa fa-fw fa-spinner fa-pulse" aria-hidden="true"></i>&nbsp;{{ _("Saving...") }}');
		submit.attr('disabled', true);
		/* submit the data */
		$.ajax({
			url: form.attr('action'),
			type: 'POST',
			data: {
				'password': $scope.user.newPassword,
				'old_password': $scope.user.oldPassword,
				'backend': "{{ current_user.back.name }}"
			},
			headers: { 'X-From-UI': true },
		})
		.fail(buiFail)
		.done(function(data) {
			notifAll(data);
		})
		.always(function() {
			/* reset the submit button state */
			submit.html(sav);
			submit.attr('disabled', false);
		});
	};

	$scope.refreshScrollspy = function() {
		angular.forEach($('.bui-scrollspy > li'), function(e) {
			var ae = angular.element(e);
			var target = e.dataset.target;
			var options = {
				scope: $scope,
				target: target
			};
			if (target in $scope.spy) {
				var oldSpy = $scope.spy[target];
				oldSpy.untrackElement(options.target, ae);
		    oldSpy.destroy();
			}
			var scrollspy = $scrollspy(options);
			scrollspy.trackElement(options.target, ae);
			$scope.spy[target] = scrollspy;
		});
	};

	$timeout(function() {
		$scope.refreshScrollspy();
	});
});

/***
 * The session part is handled by datatables
 * the resulting JSON looks like:
 * [
 *  {
 *    "api": false,
 *    "current": false,
 *    "expire": "1970-01-01T00:00:00+01:00",
 *    "ip": "::ffff:10.0.0.100",
 *    "permanent": false,
 *    "timestamp": "2016-09-01T15:28:59.222028+02:00",
 *    "ua": "Mozilla/5.0 (X11; Linux x86_64; rv:45.0) Gecko/20100101 Firefox/45.0",
 *    "uuid": "feaac9c7-6f61-4103-9536-d65aba335892"
 *  }
 * ]
 */
{% import 'macros.html' as macros %}

var _cache_id = _EXTRA;

{{ macros.timestamp_filter() }}

var _sessions_table = $('#table-sessions').DataTable( {
	{{ macros.translate_datatable() }}
	{{ macros.get_page_length() }}
	responsive: true,
	processing: true,
	fixedHeader: true,
	select: {
		style: 'os',
	},
	ajax: {
		url: '{{ url_for("api.user_sessions") }}',
		headers: { 'X-From-UI': true },
		cache: AJAX_CACHE,
		error: buiFail,
		data: function (request) {
			request._extra = _cache_id;
		},
		dataSrc: function (data) {
			return data;
		}
	},
	dom: "<'row'<'col-sm-6'l><'col-sm-6'f>>" +
		"<'row'<'col-sm-12'tr>>" +
		"<'row'<'col-sm-5'><'col-sm-7'p>>" +
		"<'row'<'col-sm-5'i>>" +
		"<'row'B>",
	buttons: [
		{
			text: '<i class="fa fa-check-square-o" aria-hidden="true"></i>',
			titleAttr: '{{ _("Select all") }}',
			extend: 'selectAll',
		},
		{
			text: '<i class="fa fa-filter" aria-hidden="true"></i>&nbsp;<i class="fa fa-check-square-o" aria-hidden="true"></i>',
			titleAttr: '{{ _("Select all filtered") }}',
			extend: 'selectAll',
			action: function ( e, dt, node, config ) {
				dt.rows( { search: 'applied' } ).select();
			}
		},
		{
			text: '<i class="fa fa-square-o" aria-hidden="true"></i>',
			titleAttr: '{{ _("Deselect all") }}',
			extend: 'selectNone',
		},
		{
			text : '<i class="fa fa-filter" aria-hidden="true"></i>&nbsp;<i class="fa fa-square-o" aria-hidden="true"></i>',
			titleAttr: '{{ _("Deselect all filtered") }}',
			extend: 'selectNone',
			action: function ( e, dt, node, config ) {
				dt.rows( { search: 'applied' } ).deselect();
			}
		},
		{
			text: '<span aria-label="{{ _("Revoke") }}"><i class="fa fa-trash-o" aria-hidden="true"></i></span>',
			titleAttr: '{{ _("Revoke selected") }}',
			className: 'btn-danger',
			action: function ( e, dt, node, config ) {
				var rows = dt.rows( { selected: true } ).data();
				var current = false;
				var output = '';
				$.each(rows, function(i, row) {
					output += JSON.stringify(row, null, 4)+'\n';
					if (row.current) {
						current = true;
					}
				});
				if (current) {
					$('#error-confirm').show();
				} else {
					$('#error-confirm').hide();
				}
				$('#session-details').empty().text(output);
				$('#perform-revoke').data('multi', true);
				$('#confirmation-modal').modal('toggle');
				$('pre code').each(function(i, block) {
					hljs.highlightBlock(block);
				});
			},
			enabled: false
		}
	],
	order: [[1, 'desc']],
	rowId: 'uuid',
	columns: [
		{ data: 'ip' },
		{
			data: 'timestamp',
			type: 'timestamp',
			render: function( data, type, row ) {
				if (type === 'filter') {
					return data;
				}
				return '<span data-toggle="tooltip" title="'+data+'">'+moment(data, moment.ISO_8601).subtract(3, 'seconds').fromNow()+'</span>';
			}
		},
		{ 
			data: 'ua',
			render: function( data, type, row ) {
				if (type === 'filter' || type === 'sort') {
					return data;
				}
				ret = '';
				// Browser version
				if (data.lastIndexOf('MSIE') > 0 || data.lastIndexOf('Trident') > 0) {
					ret += '<i class="fa fa-internet-explorer" aria-hidden="true"></i>';
				} else if (data.lastIndexOf('Edge') > 0) {
					ret += '<i class="fa fa-edge" aria-hidden="true"></i>';
				} else if (/Firefox[\/\s](\d+\.\d+)/.test(data)) {
					ret += '<i class="fa fa-firefox" aria-hidden="true"></i>';
				} else if (data.lastIndexOf('Chrome/') > 0) {
					ret += '<i class="fa fa-chrome" aria-hidden="true"></i>';
				} else if (data.lastIndexOf('Safari/') > 0) {
					ret += '<i class="fa fa-safari" aria-hidden="true"></i>';
				} else {
					ret += '<i class="fa fa-question" aria-hidden="true"></i>';
				}
				// Optionally add OS version
				if (data.lastIndexOf('Android') > 0) {
					ret += '&nbsp;<i class="fa fa-android" aria-hidden="true"></i>';
				} else if (data.lastIndexOf('iPhone') > 0 || data.lastIndexOf('iPad') > 0 || data.lastIndexOf('Macintosh') > 0) {
					ret += '&nbsp;<i class="fa fa-apple" aria-hidden="true"></i>';
					if (data.lastIndexOf('iPhone') > 0) {
						ret += '&nbsp;<i class="fa fa-mobile" aria-hidden="true"></i>';
					} else if (data.lastIndexOf('iPad') > 0) {
						ret += '&nbsp;<i class="fa fa-tablet" aria-hidden="true"></i>';
					}
				} else if (data.lastIndexOf('Linux') > 0) {
					ret += '&nbsp;<i class="fa fa-linux" aria-hidden="true"></i>';
				} else if (data.lastIndexOf('Windows') > 0) {
					ret += '&nbsp;<i class="fa fa-windows" aria-hidden="true"></i>';
				}
				return '<span data-toggle="tooltip" title="'+data+'">'+ret+'</span>';
			}
		},
		{
			data: 'api',
			render: function( data, type, row ) {
				return '<i class="fa fa-'+(data?'check':'remove')+'" aria-hidden="true"></i>';
			}
		},
		{
			data: 'current',
			render: function( data, type, row ) {
				return '<i class="fa fa-'+(data?'check':'remove')+'" aria-hidden="true"></i>';
			}
		},
		{
			data: 'expire',
			type: 'timestamp',
			render: function( data, type, row ) {
				if (type === 'filter') {
					return data;
				}
				return '<span data-toggle="tooltip" title="'+data+'">'+moment(data, moment.ISO_8601).fromNow()+'</span>';
			}
		},
	],
});
var first = true;

var _sessions = function() {
	if (first) {
		first = false;
	} else {
		if (!AJAX_CACHE) {
			_cache_id = new Date().getTime();
		}
		_sessions_table.ajax.reload( null, false );
		AJAX_CACHE = true;
	}
};

var _events_callback = function() {
	$('[data-toggle="tooltip"]').tooltip();
	$('[data-toggle="revoke-session"]').on('click', function(e) {
		$me = $(this);
		if ($me.data('current')) {
			$('#error-confirm').show();
		} else {
			$('#error-confirm').hide();
		}
		$('#session-details').empty().text(unescape($me.data('misc')));
		$('#perform-revoke').data('id', $me.data('id'));
		$('#perform-revoke').data('current', $me.data('current'));
		$('#confirmation-modal').modal('toggle');
	});
};

var select_event = function( e, dt, type, indexes ) {
	var selectedRows = _sessions_table.rows( { selected: true } ).count();
	_sessions_table.buttons( [3, 4] ).enable( selectedRows > 0 );
};

_sessions_table.on('select.dt', select_event);
_sessions_table.on('deselect.dt', select_event);
_sessions_table.on('draw.dt', _events_callback);
_sessions_table.on('responsive-display.dt', function ( e, datatable, row, showHide, update ) {
	_events_callback();
});
{{ macros.page_length('#table-sessions') }}

var revoke_session = function(id, refresh) {
	 return $.ajax({
		url: '{{ url_for("api.user_sessions") }}/'+id,
		headers: { 'X-From-UI': true },
		type: 'DELETE'
	}).done(function(data) {
		notifAll(data);
		if (refresh && data[0] == NOTIF_SUCCESS) {
			AJAX_CACHE = false;
			_sessions();
		}
	}).fail(buiFail);
};

$('#perform-revoke').on('click', function(e) {
	$me = $(this);
	if ($me.data('multi')) {
		var rows = _sessions_table.rows( { selected: true } ).data();
		var current = undefined;
		var requests = [];
		var last;
		$.each(rows, function(i, row) {
			if (row.current) {
				current = row;
				return;
			}
			last = revoke_session(row.uuid, false);
			requests.push(last);
		});
		if (current) {
			$.when.apply( $, requests ).done(function() {
				window.location = '{{ url_for("view.logout") }}';
				return;
			});
		} else {
			$.when.apply( $, requests ).done(function() {
				AJAX_CACHE = false;
				_sessions();
			});
		}
		return;
	}
	if ($me.data('current')) {
		window.location = '{{ url_for("view.logout") }}';
		return;
	}
	revoke_session($me.data('id'), true);
});

// adapted from http://bl.ocks.org/d3noob/8375092
// ************** Generate the tree diagram	 *****************
var w = window,
		d = document,
		e = d.documentElement,
		g = d.getElementsByTagName('body')[0],
		x = $('#acl-tree').width(),
		y = w.innerHeight|| e.clientHeight|| g.clientHeight;

var margin = {top: 20, right: 120, bottom: 20, left: 120},
	width = x - margin.right - margin.left,
	height = (y*0.9) - margin.top - margin.bottom;

var i = 0,
	duration = 750,
	root;

var tree = d3.layout.tree()
	.size([height, width]);

var diagonal = d3.svg.diagonal()
	.projection(function(d) { return [d.y, d.x]; });

var svg = d3.select("#acl-tree").append("svg")
	.attr("width", width + margin.right + margin.left)
	.attr("height", height + margin.top + margin.bottom)
	.append("g")
	.attr("transform", "translate(" + margin.left + "," + margin.top + ")");

d3.select(self.frameElement).style("height", height+"px");

function update_tree(source) {

	// Compute the new tree layout.
	var nodes = tree.nodes(root).reverse(),
		links = tree.links(nodes);

	// Normalize for fixed-depth.
	nodes.forEach(function(d) { d.y = d.depth * 180; });

	// Update the nodes…
	var node = svg.selectAll("g.node")
		.data(nodes, function(d) { return d.id || (d.id = ++i); });

	// Enter any new nodes at the parent's previous position.
	var nodeEnter = node.enter().append("g")
		.attr("class", "node")
		.attr("transform", function(d) { return "translate(" + source.y0 + "," + source.x0 + ")"; })
		.on("click", click);

	nodeEnter.append("circle")
		.attr("r", 1e-6)
		.style("fill", function(d) { return d._children ? "lightsteelblue" : "#fff"; });

	nodeEnter.append("text")
		.attr("x", function(d) { return d.children || d._children ? -13 : 13; })
		.attr("dy", ".35em")
		.attr("text-anchor", function(d) { return d.children || d._children ? "end" : "start"; })
		.text(function(d) { return d.name; })
		.style("fill-opacity", 1e-6);

	// Transition nodes to their new position.
	var nodeUpdate = node.transition()
		.duration(duration)
		.attr("transform", function(d) { return "translate(" + d.y + "," + d.x + ")"; });

	nodeUpdate.select("circle")
		.attr("r", 10)
		.style("fill", function(d) { return d._children ? "lightsteelblue" : "#fff"; });

	nodeUpdate.select("text")
		.style("fill-opacity", 1);

	// Transition exiting nodes to the parent's new position.
	var nodeExit = node.exit().transition()
		.duration(duration)
		.attr("transform", function(d) { return "translate(" + source.y + "," + source.x + ")"; })
		.remove();

	nodeExit.select("circle")
		.attr("r", 1e-6);

	nodeExit.select("text")
		.style("fill-opacity", 1e-6);

	// Update the links…
	var link = svg.selectAll("path.link")
		.data(links, function(d) { return d.target.id; });

	// Enter any new links at the parent's previous position.
	link.enter().insert("path", "g")
		.attr("class", "link")
		.attr("d", function(d) {
			var o = {x: source.x0, y: source.y0};
			return diagonal({source: o, target: o});
		});

	// Transition links to their new position.
	link.transition()
		.duration(duration)
		.attr("d", diagonal);

	// Transition exiting nodes to the parent's new position.
	link.exit().transition()
		.duration(duration)
		.attr("d", function(d) {
			var o = {x: source.x, y: source.y};
			return diagonal({source: o, target: o});
		})
		.remove();

	// Stash the old positions for transition.
	nodes.forEach(function(d) {
		d.x0 = d.x;
		d.y0 = d.y;
	});
}

// Toggle children on click.
function click(d) {
	if (d.children) {
		d._children = d.children;
		d.children = null;
	} else {
		d.children = d._children;
		d._children = null;
	}
	update_tree(d);
}

d3.json("{{ url_for('api.clients_all') }}?_session=" + SESSION_TAG)
	.header('X-From-UI', true)
	.get(function(error, data) {
		if (! error) {
			root = {
				{% if config.STANDALONE -%}
				"name": "{{ _('clients') }}",
				{% else -%}
				"name": "{{ _('servers') }}",
				{% endif -%}
				"parent": "null",
				"children": []
			};
			var children = {};

			$.each(data, function(i, node) {
				if (! node.agent) {
					root.children.push({
						'name': node.name,
						'parent': "{{ _('clients') }}"
					});
					return;
				}
				if (! (node.agent in children)) {
					children[node.agent] = {
						'name': node.agent,
						'parent': "{{ _('servers') }}",
						'children': []
					};
				}
				children[node.agent]['children'].push({
					'name': node.name,
					'parent': node.agent
				});
			});

			$.each(children, function(i, nodes) {
				root.children.push(nodes);
			});

			function collapse(d) {
				if (d.children) {
					d._children = d.children;
					d._children.forEach(collapse);
					d.children = null;
				}
			}

			root.children.forEach(collapse);
			root.x0 = height / 2;
			root.y0 = 0;

			update_tree(root);
		}
	});
