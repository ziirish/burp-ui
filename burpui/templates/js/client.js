{% if current_user and current_user.is_authenticated and (current_user.is_admin or current_user.is_moderator) -%}
{% set extra_features = True %}
{% endif -%}

/***
 * Here is the 'client' part
 * It is available on the 'specific' client view
 */

var _cache_id = _EXTRA;

/***
 * First we map some burp status with some style
 */
var __status = {
	"{{ _('client crashed') }}": 'label-danger',
	"{{ _('server crashed') }}": 'label-danger',
	"{{ _('running') }}": 'label-success',
	"{{ _('idle') }}": 'label-default',
};

var __translate = {
	"client crashed": "{{ _('client crashed') }}",
	"server crashed": "{{ _('server crashed') }}",
	"running": "{{ _('running') }}",
	"idle": "{{ _('idle') }}",
};

/***
 * Icons for <i class="fa fa-search" aria-hidden="true"></i>
 */
var __icons = {
	"{{ _('client crashed') }}": 'fa fa-fw fa-exclamation',
	"{{ _('server crashed') }}": 'fa fa-fw fa-exclamation',
	"{{ _('running') }}": 'fa fa-fw fa-play blink',
	"{{ _('idle') }}": 'fa fa-fw fa-pause',
};

/***
 * _client: function that retrieve up-to-date informations from the burp server about a specific client
 * JSON format:
 * [
 *   {
 *     "date": "2014-05-12 19:40:02",
 *     "number": "254",
 *     "deletable": true,
 *     "encrypted": true,
 *     "received": 889818873,
 *     "size": 35612321050,
 *   },
 *   {
 *     "date": "2014-05-11 21:20:03",
 *     "number": "253",
 *     "deletable": true,
 *     "encrypted": true,
 *     "received": 889818873,
 *     "size": 35612321050,
 *   }
 * ]
 * The JSON is then parsed into a table
 */
{% import 'macros.html' as macros %}

{{ macros.timestamp_filter() }}

var __init_complete = false;
var _client_table = $('#table-client').DataTable( {
	{{ macros.translate_datatable() }}
	{{ macros.get_page_length() }}
	responsive: true,
	processing: true,
	fixedHeader: true,
	ajax: {
		url: '{{ url_for("api.client_stats", name=cname, server=server) }}',
		headers: { 'X-From-UI': true },
		cache: AJAX_CACHE,
		data: function (request) {
			request._extra = _cache_id;
		},
		dataSrc: function (data) {
			if (data.length == 0) {
				$('#table-client').hide();
				$('#client-alert').show();
			} else {
				$('#client-alert').hide();
				$('#table-client').show();
			}
			return data;
		},
		error: function(xhr, stat, err) {
			buiFail(xhr, stat, err);
			$('#table-client').hide();
			$('#client-alert').show();
		}
	},
	rawId: 'number',
	order: [[0, 'desc']],
	rowCallback: function( row, data ) {
		row.className += ' clickable';
	},
	initComplete: function ( settings, json ) {
		__init_complete = true;
	},
	columns: [
		{
			data: null,
			render: function ( data, type, row ) {
				if (type === 'filter' || type === 'sort') {
					return data.number;
				}
				return '<a href="{{ url_for("view.client_browse", name=cname, server=server) }}/'+data.number+(data.encrypted?'?encrypted=1':'')+'" style="color: inherit; text-decoration: inherit;">'+pad(data.number, 7)+'</a>';
			}
		},
		{
			data: 'date',
			type: 'timestamp',
			render: function ( data, type, row ) {
				return '<span data-toggle="tooltip" title="'+data+'">'+moment(data, moment.ISO_8601).format({{ g.date_format|tojson }})+'</span>';
			}
		},
		{
			data: 'received',
			render: function ( data, type, row ) {
				return _bytes_human_readable(data, false);
			}
		},
		{
			data: 'size',
			render: function ( data, type, row ) {
				return _bytes_human_readable(data, false);
			}
		},
		{
			data: 'deletable',
			render: function ( data, type, row ) {
				return '<i class="fa fa-'+(data?'check':'remove')+'" aria-hidden="true"></i>';
			}
		},
		{
			data: 'encrypted',
			render: function ( data, type, row ) {
				return '<i class="fa fa-fw fa-'+(data?'lock':'globe')+'" aria-hidden="true"></i>&nbsp;'+(data?"{{ _('Encrypted backup') }}":"{{ _('Unencrypted backup') }}");
			}
		},
		{% if extra_features -%}
		{
			data: null,
			orderable: false,
			render: function ( data, type, row ) {
				var disable = '';
				if (!data.deletable) {
					disable = 'disabled="disabled"';
				}
				return '<button class="btn btn-danger btn-xs btn-delete-backup no-link" data-backup="' + data.number + '" ' + disable + '><i class="fa fa-trash" aria-hidden="true"></i>&nbsp;{{ _("Delete") }}</button>';
			}
		}
		{% endif -%}
	]
});
var first = true;

var _client = function() {
	url_restore = '{{ url_for("api.is_server_restore", name=cname, server=server) }}';
	$.getJSON(url_restore, function(d) {
		if (d.found) {
			$('.edit-restore').show();
			$('.scheduled-backup').hide();
			$('.cancel-backup').hide();
		} else {
			$('.edit-restore').hide();
			$('.scheduled-backup').show();
		}
	}).fail(function() {
		$('#controls').hide();
	});

	url_backup = '{{ url_for("api.is_server_backup", name=cname, server=server) }}';
	$.getJSON(url_backup, function(d) {
		if (d.is_server_backup) {
			$('.cancel-backup').show();
			$('.scheduled-backup').hide();
			$('.edit-restore').hide();
		} else {
			$('.scheduled-backup').show();
			$('.cancel-backup').hide();
		}
	}).fail(function() {
		$('#controls').hide();
	});

	if (!__init_complete) {
		return;
	}
	if (first) {
		first = false;
	} else {
		if (!AJAX_CACHE) {
			_cache_id = new Date().getTime();
		}
		_client_table.ajax.reload( null, false );
		AJAX_CACHE = true;
	}
};

{{ macros.page_length('#table-client') }}

var __refresh_running = undefined;
var refresh_status = function( is_running ) {
	{% if config.WITH_CELERY %}
	{% set api_running_clients = "api.async_running_clients" %}
	{% else %}
	{% set api_running_clients = "api.running_clients" %}
	{% endif %}
	var url = '{{ url_for(api_running_clients, client=cname, server=server) }}';
	var client_status_url = '{{ url_for("api.client_running_status", name=cname, server=server) }}';
	var _get_running = undefined;
	var _get_status = undefined;
	var _client_running = false;
	var _span = $('#running-status');
	var _inner_format_status = function(status) {
		var _content = '<i class="'+__icons[status.state]+'" aria-hidden="true"></i>&nbsp;';
		if (status.state == '{{ _("running") }}') {
			_client_running = true;
			_content += '<a href="{{ url_for("view.live_monitor", server=server, name=cname) }}">';
			_content += status.state+' - '+status.phase;
			if (status.percent > 0) {
				_content += ' ('+status.percent+'%)';
			}
			_content += '</a>';
		} else if (status.state) {
			_content += status.state;
		} else {
			_content = '';
		}
		return _content;
	};
	var _inner_get_status = function() {
		return $.getJSON(client_status_url, function(_status) {
			_span.html(_inner_format_status(_status));
			_span.removeClass();
			_span.addClass('label pull-right');
			_span.addClass(__status[_status.state]);
		});
	};
	if (is_running) {
		_get_running = $.getJSON(url, function(running) {
			if (_.indexOf(running, '{{ cname }}') != -1) {
				_get_status = _inner_get_status();
				return;
			}
		});
	} else {
		_get_running = _inner_get_status();
	}
	var _inner_callback_setup = function() {
		if (__refresh_running) {
			clearTimeout(__refresh_running);
			__refresh_running = undefined;
		}
		if (_client_running) {
			__refresh_running = setTimeout(function() {
				refresh_status(true);
			}, {{ config.LIVEREFRESH * 1000 }});
		} else {
			_cache_id = new Date().getTime();
			if (__init_complete && is_running) {
				auto_refresh_function(true);
			}
		}
	};
	if (_get_running) {
		$.when( _get_running ).done( function() {
			if (_get_status) {
				$.when( _get_status ).done(_inner_callback_setup);
			} else {
				_inner_callback_setup();
			}
		});
	} else {
		_inner_callback_setup();
	}
};

$( document ).ready(function() {
	$('a.toggle-vis').on('click', function(e) {
		e.preventDefault();

		// Get the column API object
		var column = _client_table.column( $(this).attr('data-column') );
		var vis = column.visible();

		// add fa someday: fa fa-eye-close
		if (vis) {
			$(this).addClass('italic');
		} else {
			$(this).removeClass('italic');
		}

		// Toggle the visibility
		column.visible( !vis );
	});

	$('#btn-cancel-restore').on('click', function(e) {
		$.ajax({
			url: '{{ url_for("api.is_server_restore", name=cname, server=server) }}',
			headers: { 'X-From-UI': true },
			type: 'DELETE'
		}).done(function(data) {
			notifAll(data);
			if (data[0] == NOTIF_SUCCESS) {
				$('.edit-restore').hide();
				$('.scheduled-backup').show();
			}
		}).fail(buiFail);
	});

	$('#btn-cancel-backup').on('click', function(e) {
		$.ajax({
			url: '{{ url_for("api.is_server_backup", name=cname, server=server) }}',
			headers: { 'X-From-UI': true },
			type: 'DELETE'
		}).done(function(data) {
			notifAll(data);
			if (data[0] == NOTIF_SUCCESS) {
				$('.cancel-backup').hide();
				$('.scheduled-backup').show();
			}
		}).fail(buiFail);
	});

	$('#btn-schedule-backup').on('click', function(e) {
		$.ajax({
			url: '{{ url_for("api.server_backup", name=cname, server=server) }}',
			headers: { 'X-From-UI': true },
			type: 'PUT'
		}).done(function(data) {
			notifAll(data);
			if (data[0] == NOTIF_SUCCESS) {
				$('.cancel-backup').show();
				$('.scheduled-backup').hide();
			}
		}).fail(buiFail);
	});
});

_client_table.on('draw.dt', function() {
	$('[data-toggle="tooltip"]').tooltip();
});
_client_table.on('init.dt', function() {
	_check_running(true);
	refresh_status(false);
});
$( document ).on('refreshClientStatusEvent', function( event, is_running ) {
	refresh_status(is_running);
});

/* this one is outside because the buttons are dynamically added after the
 * document gets loaded
 */
$( document ).on('click', '.btn-delete-backup', function(e) {
	$.ajax({
		url: '{{ url_for("api.client_report", name=cname, server=server) }}/' + $(this).attr('data-backup'),
		headers: { 'X-From-UI': true },
		type: 'DELETE'
	}).done(function(data) {
		notif(NOTIF_SUCCESS, '{{ _("Delete task launched") }}');
		/* refresh backups list now */
		_client();
	}).fail(buiFail);
});
