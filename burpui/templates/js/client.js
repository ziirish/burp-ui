
/***
 * Here is the 'client' part
 * It is available on the 'specific' client view
 */

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

var _client_table = $('#table-client').dataTable( {
	{{ macros.translate_datatable() }}
	{{ macros.get_page_length() }}
	responsive: true,
	ajax: {
		url: '{{ url_for("api.client_stats", name=cname, server=server) }}',
		headers: { 'X-From-UI': true },
		dataSrc: function (data) {
			if (data.length == 0) {
				$('#table-client').hide();
				$('#client-alert').show();
			} else {
				$('#client-alert').hide();
				$('#table-client').show();
				return data;
			}
		},
		error: function(xhr, stat, err) {
			myFail(xhr, stat, err);
			$('#table-client').hide();
			$('#client-alert').show();
		}
	},
	order: [[0, 'desc']],
	destroy: true,
	rowCallback: function( row, data ) {
		row.className += ' clickable';
	},
	columns: [
		{
			data: null,
			render: function ( data, type, row ) {
				return '<a href="{{ url_for("view.client_browse", name=cname, server=server) }}?backup='+data.number+(data.encrypted?'&encrypted=1':'')+'" style="color: inherit; text-decoration: inherit;">'+pad(data.number, 7)+'</a>';
			}
		},
		{
			data: null,
			type: 'timestamp',
			render: function ( data, type, row ) {
				return '<span data-toggle="tooltip" title="'+data.date+'">'+moment(data.date, moment.ISO_8601).format('llll')+'</span>';
			}
		},
		{
			data: null,
			render: function ( data, type, row ) {
				return _bytes_human_readable(data.received, false);
			}
		},
		{
			data: null,
			render: function ( data, type, row ) {
				return _bytes_human_readable(data.size, false);
			}
		},
		{
			data: null,
			render: function ( data, type, row ) {
				return '<span class="glyphicon glyphicon-'+(data.deletable?'ok':'remove')+'"></span>';
			}
		},
		{
			data: null,
			render: function ( data, type, row ) {
				return '<span class="glyphicon glyphicon-'+(data.encrypted?'lock':'globe')+'"></span>&nbsp;'+(data.encrypted?"{{ _('Encrypted backup') }}":"{{ _('Unencrypted backup') }}");
			}
		}
	]
});
var first = true;

var _client = function() {
	if (first) {
		first = false;
	} else {
		_client_table.api().ajax.reload( null, false );
	}

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
	}).fail(myFail);

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
	}).fail(myFail);
};

{{ macros.page_length('#table-client') }}

$(document).ready(function() {
	$('a.toggle-vis').on('click', function(e) {
		e.preventDefault();

		// Get the column API object
		var column = _client_table.api().column( $(this).attr('data-column') );
		var vis = column.visible();

		if (vis) {
			$(this).addClass('italic');
		} else {
			$(this).removeClass('italic');
		}

		// Toggle the visibility
		column.visible( ! vis );
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
		}).fail(myFail);
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
		}).fail(myFail);
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
		}).fail(myFail);
	});
});

_client_table.on('draw.dt', function() {
	$('[data-toggle="tooltip"]').tooltip();
});
