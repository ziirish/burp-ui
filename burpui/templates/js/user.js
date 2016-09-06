/***
 * The User page is managed with AngularJS for some parts.
 * Following is the AngularJS Application and Controller.
 */
var app = angular.module('MainApp', ['ngSanitize']);

app.controller('UserCtrl', function($scope, $http) {
	$scope.version = '';
	/*
	$scope.api = '';
	$scope.burp = Array();

	$http.get('{{ url_for("api.about") }}', { headers: { 'X-From-UI': true } })
		.success(function(data, status, headers, config) {
			$scope.version = data.version;
			$scope.api = data.api;
			$scope.burp = data.burp;
		});
	*/
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

// extends DataTables sorting
jQuery.extend( jQuery.fn.dataTableExt.oSort, {
	"timestamp-pre": function ( a ) {
		$obj = $(a);
		return moment($obj.attr('title')).valueOf();
	},
	"timestamp-asc": function ( a, b ) {
		return ((a < b) ? -1 : ((a > b) ? 1 : 0));
	},
	"timestamp-desc": function ( a, b ) {
		return ((a < b) ? 1 : ((a > b) ? -1 : 0));
	}
} );

var _sessions_table = $('#table-sessions').dataTable( {
	{{ macros.translate_datatable() }}
	{% if session.pageLength -%}
	pageLength: {{ session.pageLength }},
	{% endif -%}
	responsive: true,
	ajax: {
		url: '{{ url_for("api.user_sessions") }}',
		headers: { 'X-From-UI': true },
		error: myFail,
		dataSrc: function (data) {
			return data;
		}
	},
	order: [[1, 'desc']],
	destroy: true,
	/*
	rowCallback: function( row, data ) {
		// do nothing
	},
	*/
	columns: [
		{ data: 'ip' },
		{
			data: null,
			type: 'timestamp',
			render: function( data, type, row ) {
				return '<span data-toggle="tooltip" title="'+data.timestamp+'">'+moment(data.timestamp).fromNow()+'</span>';
			}
		},
		{ 
			data: null,
			render: function( data, type, row ) {
				ret = '';
				// Browser version
				if (data.ua.lastIndexOf('MSIE') > 0 || data.ua.lastIndexOf('Trident') > 0) {
					ret += '<i class="fa fa-internet-explorer" aria-hidden="true"></i>';
				} else if (data.ua.lastIndexOf('Edge') > 0) {
					ret += '<i class="fa fa-edge" aria-hidden="true"></i>';
				} else if (/Firefox[\/\s](\d+\.\d+)/.test(data.ua)) {
					ret += '<i class="fa fa-firefox" aria-hidden="true"></i>';
				} else if (data.ua.lastIndexOf('Chrome/') > 0) {
					ret += '<i class="fa fa-chrome" aria-hidden="true"></i>';
				} else if (data.ua.lastIndexOf('Safari/') > 0) {
					ret += '<i class="fa fa-safari" aria-hidden="true"></i>';
				} else {
					ret += '<i class="fa fa-question" aria-hidden="true"></i>';
				}
				// Optionally add OS version
				if (data.ua.lastIndexOf('Android') > 0) {
					ret += '&nbsp;<i class="fa fa-android" aria-hidden="true"></i>';
				} else if (data.ua.lastIndexOf('iPhone') > 0 || data.ua.lastIndexOf('Macintosh') > 0) {
					ret += '&nbsp;<i class="fa fa-apple" aria-hidden="true"></i>';
				} else if (data.ua.lastIndexOf('Linux') > 0) {
					ret += '&nbsp;<i class="fa fa-linux" aria-hidden="true"></i>';
				} else if (data.ua.lastIndexOf('Windows') > 0) {
					ret += '&nbsp;<i class="fa fa-windows" aria-hidden="true"></i>';
				}
				return '<span data-toggle="tooltip" title="'+data.ua+'">'+ret+'</span>';
			}
		},
		{
			data: null,
			render: function( data, type, row ) {
				return '<span class="glyphicon glyphicon-'+(data.api?'ok':'remove')+'"></span>';
			}
		},
		{
			data: null,
			render: function( data, type, row ) {
				return '<span class="glyphicon glyphicon-'+(data.current?'ok':'remove')+'"></span>';
			}
		},
		{
			data: null,
			type: 'timestamp',
			render: function( data, type, row ) {
				return '<span data-toggle="tooltip" title="'+data.expire+'">'+moment(data.expire).fromNow()+'</span>';
			}
		},
		{
			data: null,
			render: function( data, type, row ) {
				return '<button class="btn btn-danger" data-toggle="revoke-session" data-id="'+data.uuid+'" data-current="'+data.current+'" data-misc="'+escape(JSON.stringify(data, null, 4))+'"><span class="glyphicon glyphicon-trash"></span></button>';
			}
		}
	],
});
var first = true;

var _sessions = function() {
	if (first) {
		first = false;
	} else {
		_sessions_table.api().ajax.reload( null, false );
	}
};

_events_callback = function() {
	$('[data-toggle="tooltip"]').tooltip();
	$('[data-toggle="revoke-session"]').on('click', function(e) {
		$me = $(this);
		if ($me.data('current')) {
			$('#error-confirm').show();
		} else {
			$('#error-confirm').hide();
		}
		$('#session-details').empty().html(unescape($me.data('misc')));
		$('#perform-revoke').data('id', $me.data('id'));
		$('#confirmation-modal').modal('toggle');
	});
};
_sessions_table.on('draw.dt', _events_callback);
_sessions_table.on('responsive-display.dt', function ( e, datatable, row, showHide, update ) {
	_events_callback();
});

$('#perform-revoke').on('click', function(e) {
	$me = $(this);
	$.ajax({
		url: '{{ url_for("api.user_sessions") }}/'+$me.data('id'),
		headers: { 'X-From-UI': true },
		type: 'DELETE'
	}).done(function(data) {
		notifAll(data);
		if (data[0] == NOTIF_SUCCESS) {
			_sessions();
		}
	}).fail(myFail);
});
