
/***
 * Here is the 'client' part
 * It is available on the 'specific' client view
 */

/***
 * First we map some burp status with some style
 */
var __status = {
	"{{ _('client crashed') }}": 'label-danger',
	"{{ _('server crashed') }}": 'label-danger',
	"{{ _('running') }}": 'label-success',
	"{{ _('idle') }}": 'label-default',  // hack to manage translation
};

/***
 * Icons for <span class="glyphicon glyphicon-search" aria-hidden="true"></span>
 */
var __icons = {
	"{{ _('client crashed') }}": 'glyphicon glyphicon-exclamation-sign',
	"{{ _('server crashed') }}": 'glyphicon glyphicon-exclamation-sign',
	"{{ _('running') }}": 'glyphicon glyphicon-play',
	"{{ _('idle') }}": 'glyphicon glyphicon-pause',
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

var _client_table = $('#table-client').DataTable( {
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
	rawId: 'number',
	order: [[0, 'desc']],
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
				return '<span data-toggle="tooltip" title="'+data.date+'">'+moment(data.date, moment.ISO_8601).format({{ g.date_format|tojson }})+'</span>';
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
		},
		{
			data: null,
			render: function ( data, type, row ) {
				var disable = '';
				if (!data.deletable) {
					disable = 'disabled="disabled"';
				}
				return '<button class="btn btn-danger btn-xs btn-delete-backup no-link" data-backup="' + data.number + '" ' + disable + '><i class="fa fa-trash" aria-hidden="true"></i>&nbsp;{{ _("Delete") }}</button>';
			}
		}
	]
});
var first = true;

var _client = function() {
	if (first) {
		first = false;
		_check_running();
	} else {
		_client_table.ajax.reload( null, false );
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
};

{{ macros.page_length('#table-client') }}

$( document ).ready(function() {
	$('a.toggle-vis').on('click', function(e) {
		e.preventDefault();

		// Get the column API object
		var column = _client_table.column( $(this).attr('data-column') );
		var vis = column.visible();

		// add glyphicon someday: glyphicon glyphicon-eye-close
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
	}).fail(myFail);
});
