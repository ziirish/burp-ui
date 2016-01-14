
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
};

$(document).ready(function() {
	$('a.toggle-vis').on( 'click', function (e) {
		e.preventDefault();

		// Get the column API object
		var column = _client_table.api().column( $(this).attr('data-column') );

		// Toggle the visibility
		column.visible( ! column.visible() );
	});
});
