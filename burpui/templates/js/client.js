
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

var _client_table = $('#table-client').dataTable( {
	responsive: true,
	ajax: {
		url: '{{ url_for("api.client_stats", name=cname, server=server) }}',
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
		fail: function(xhr, stat, err) {
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
		{ data: null, render: function ( data, type, row ) {
				return '<a href="{{ url_for("view.client_browse", name=cname, server=server) }}?backup='+data.number+(data.encrypted?'&encrypted=1':'')+'" style="color: inherit; text-decoration: inherit;">'+pad(data.number, 7)+'</a>';
			}
		},
		{ data: 'date' },
		{ data: null, render: function ( data, type, row ) {
				return _bytes_human_readable(data.received, false);
			}
		},
		{ data: null, render: function ( data, type, row ) {
				return _bytes_human_readable(data.size, false);
			}
		},
		{ data: null, render: function ( data, type, row ) {
				return '<span class="glyphicon glyphicon-'+(data.deletable?'ok':'remove')+'"></span>';
			}
		},
		{ data: null, render: function ( data, type, row ) {
				return '<span class="glyphicon glyphicon-'+(data.encrypted?'lock':'globe')+'"></span>&nbsp;'+(data.encrypted?'Encrypted':'Unencrypted')+' backup';
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
			type: 'DELETE'
		}).done(function(data) {
			notif(data[0], data[1]);
			if (data[0] == 0) {
				$('.edit-restore').hide();
				$('.scheduled-backup').show();
			}
		}).fail(myFail);
	});

	$('#btn-cancel-backup').on('click', function(e) {
		$.ajax({
			url: '{{ url_for("api.is_server_backup", name=cname, server=server) }}',
			type: 'DELETE'
		}).done(function(data) {
			notif(data[0], data[1]);
			if (data[0] == 0) {
				$('.cancel-backup').hide();
				$('.scheduled-backup').show();
			}
		}).fail(myFail);
	});

	$('#btn-schedule-backup').on('click', function(e) {
		$.ajax({
			url: '{{ url_for("api.server_backup", name=cname, server=server) }}',
			type: 'PUT'
		}).done(function(data) {
			notif(data[0], data[1]);
			if (data[0] == 0) {
				$('.cancel-backup').show();
				$('.scheduled-backup').hide();
			}
		}).fail(myFail);
	});
});
