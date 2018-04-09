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
		url: '{{ url_for("api.other_sessions", user=user) }}',
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

var _admin = function() {
	_sessions();
};


/* placeholder */
var app = angular.module('MainApp', ['ngSanitize', 'ui.select', 'mgcrea.ngStrap', 'datatables']);

app.config(function(uiSelectConfig) {
	uiSelectConfig.theme = 'bootstrap';
});

app.controller('AdminCtrl', ['$scope', '$http', '$scrollspy', 'DTOptionsBuilder', 'DTColumnDefBuilder', function($scope, $http, $scrollspy, DTOptionsBuilder, DTColumnDefBuilder) {
}]);
