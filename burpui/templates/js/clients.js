
/***
 * Here is the 'clients' part
 * It is available on the global clients view
 */

/***
 * First we map some burp status with some style
 */
var __status = {
	"{{ _('client crashed') }}": 'danger',
	"{{ _('server crashed') }}": 'danger',
	"{{ _('running') }}": 'success',
};

var __translate = {
	"client crashed": "{{ _('client crashed') }}",
	"server crashed": "{{ _('server crashed') }}",
	"running": "{{ _('running') }}",
	"idle": "{{ _('idle') }}",
	"never": "{{ _('never') }}",
	"now": "{{ _('now') }}",
};

/***
 * Show the row as warning if there are no backups
 */
var __date = {
	"{{ _('never') }}": 'warning',
	"{{ _('now') }}": 'now',
};

var _some_clients_running = false;
var _cache_id = _EXTRA;

/***
 * _clients: function that retrieve up-to-date informations from the burp server
 * JSON format:
 * [
 *   {
 *     "last": "2014-05-12 19:40:02",
 *     "name": "client1",
 *     "state": "idle",
 *     "phase": "phase1",
 *     "percent": 12,
 *   },
 *   {
 *     "last": "never",
 *     "name": "client2",
 *     "state": "idle",
 *     "phase": "phase2",
 *     "percent": 42,
 *   }
 * ]
 *  The JSON is then parsed into a table
 */
{% import 'macros.html' as macros %}

{{ macros.timestamp_filter() }}

var __init_complete = false;
var _clients_table = $('#table-clients').DataTable( {
	{{ macros.translate_datatable() }}
	{{ macros.get_page_length() }}
	responsive: true,
	processing: true,
	fixedHeader: true,
	ajax: {
		url: '{{ url_for("api.clients_stats", server=server) }}',
		data: function (request) {
			if (_some_clients_running || !AJAX_CACHE) {
				_some_clients_running = false;
				_cache_id = new Date().getTime();
			}
			request._extra = _cache_id;
		},
		dataSrc: function (data) {
			return data;
		},
		error: buiFail,
		headers: { 'X-From-UI': true },
		cache: AJAX_CACHE && !_some_clients_running,
	},
	rowId: 'name',
	order: [[2, 'desc']],
	rowCallback: function( row, data, index ) {
		var classes = row.className.split(' ');
		_.each(classes, function(cl) {
			if (_.indexOf(['odd', 'even'], cl) != -1) {
				row.className = cl;
				return;
			}
		});
		if (__status[data.state] != undefined) {
			row.className += ' '+__status[data.state];
		}
		if (__date[data.last] != undefined) {
			row.className += ' '+__date[data.last];
		}
		row.className += ' clickable';
	},
	initComplete: function( settings, json ) {
		__init_complete = true;
	},
	columns: [
		{
			data: 'name',
			render: function ( data, type, row ) {
				if (type === 'filter' || type === 'sort') {
					return data;
				}
				return '<a href="{{ url_for("view.client", server=server, name="") }}'+data+'" style="color: inherit; text-decoration: inherit;">'+data+'</a>';
			}
		},
		{
			data: null,
			render: function ( data, type, row ) {
				var result = data.state;
				if (data.state == "{{ _('running') }}" && data.static) {
					result = data.state+' - '+data.phase;
					if (data.percent > 0) {
						result += ' ('+data.percent+'%)';
					}
				} else if (!data.static && data.state == "{{ _('running') }}") {
					_some_clients_running = true;
				}
				return result;
			}
		},
		{
			data: 'last',
			type: 'timestamp',
			render: function (data, type, row ) {
				if (type === 'filter' || type === 'sort') {
					return data;
				}
				if (!(data in __status || data in __date)) {
					return '<span data-toggle="tooltip" title="'+data+'">'+moment(data, moment.ISO_8601).format({{ g.date_format|tojson }})+'</span>';
				}
				return data;
			}
		},
		{
			data: 'labels',
			render: function (data, type, row) {
				if (type === 'filter' || type === 'sort') {
					return data.join(',');
				}
				var ret = '';
				if (!data) {
					return ret;
				}
				$.each(data, function(i, label) {
					ret += '<span class="label label-info">'+label+'</span>&nbsp;';
				});
				return ret;
			}
		},
		{
			data: null,
			orderable: false,
			render: function (data, type, row ) {
				var cls = '';
				var link_start = '';
				var link_end = '';
				var label = '';
				if (__date[data.last] == 'now' && __status[data.state] != 'idle') {
					cls = 'blink';
					link_start = '<a href="{{ url_for("view.live_monitor", server=server) }}/'+data.name+'">';
					link_end = '</a>';
					label = '&nbsp;{{ _("view") }}';
				} else {
					label = '&nbsp;{{ _("idle") }}';
				}
				return link_start + '<span class="fa-stack" style="color: #000; text-align: center;"><i class="fa fa-square fa-stack-2x" aria-hidden="true"></i><i class="fa fa-terminal fa-stack-1x fa-inverse ' + cls + '" aria-hidden="true"></i></span>' + label + link_end;
			}
		}
	]
});
var first = true;

var _clients = function() {
	if (!__init_complete) {
		return;
	}
	if (first) {
		first = false;
	} else {
		if (!AJAX_CACHE || _some_clients_running) {
			_cache_id = new Date().getTime();
		}
		_clients_table.ajax.reload( null, false );
		AJAX_CACHE = true;
	}
};

{{ macros.page_length('#table-clients') }}

var __refresh_running = undefined;
var __last_clients_running = [];
var refresh_status = function( is_running ) {
	cancel_refresh();
	{% if config.WITH_CELERY %}
	{% set api_running_clients = "api.async_running_clients" %}
	{% else %}
	{% set api_running_clients = "api.running_clients" %}
	{% endif %}
	var url = '{{ url_for(api_running_clients, server=server) }}';
	var _promises = [];
	var _clients_running = [];
	var _get_running = undefined;
	if (is_running) {
		_get_running = $.getJSON(url, function(running) {
			_.each(running, function(name) {
				var _row = _clients_table.row('#'+name);
				var _content = _row.data();
				var _p = $.getJSON('{{ url_for("api.client_running_status", server=server) }}?clientName='+name, function(_status) {
					if (!_status.last || !_status.state) {
						return;
					}
					_status.static = true;
					var _new_content = _.merge(_content, _status);
					_row.data( _new_content );
				});
				_promises.push(_p);
				_clients_running.push(name);
			});
		});
	}
	var _inner_callback_setup = function() {
		__last_clients_running = _clients_running;
		// reset clients that are no more running
		_.each(__last_clients_running, function(name) {
			if (_.indexOf(_clients_running, name) != -1) {
				// don't refresh client that was freshly redrawn
				return;
			}
			var _row = _clients_table.row('#'+name);
			var _content = _row.data();
			var _p = $.get({
				url: '{{ url_for("api.client_running_status", server=server) }}?clientName='+name,
			}).done(function(_status) {
				if (!_status.last || !_status.state) {
					return;
				}
				_status.static = false;
				var _new_content = _.merge(_content, _status);
				_row.data( _new_content );
			});
			_promises.push(_p);
		});
		$.when.apply( $, _promises ).done( function() {
			_clients_table.draw(false);
			if (_clients_running.length > 0) {
				if (__refresh_running) {
					clearTimeout(__refresh_running);
					__refresh_running = undefined;
				}
				__refresh_running = setTimeout(function() {
					refresh_status(true);
				}, {{ config.LIVEREFRESH * 1000 }});
			} else {
				_cache_id = new Date().getTime();
				if (__init_complete && is_running) {
					auto_refresh_function(true);
				}
			}
		});
	};
	if (_get_running) {
		$.when(_get_running).done(_inner_callback_setup);
	} else {
		_inner_callback_setup();
	}
};

_clients_table.on('draw.dt', function() {
	$('[data-toggle="tooltip"]').tooltip();
});
_clients_table.on('init.dt', function() {
	_check_running(true);
});
$( document ).on('refreshClientsStatesEvent', function( event, is_running ) {
	refresh_status(is_running);
});
