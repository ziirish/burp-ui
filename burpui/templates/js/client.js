
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

var _client_table = $('#table-client').dataTable( {
	responsive: true,
	ajax: {
		url: '{{ url_for("api.client_report", name=cname, server=server) }}',
		dataSrc: function (data) {
			if (!data.results) {
				$('#table-client').hide();
				$('#client-alert').show();
				if (data.notif) {
					$.each(data.notif, function(i, n) {
						notif(n[0], n[1]);
					});
				}
				return {};
			}
			if (data.results.length == 0) {
				$('#table-client').hide();
				$('#client-alert').show();
			} else {
				return data.results;
			}
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
		{ data: null, render: function (data, type, row ) {
				return '<span class="glyphicon glyphicon-'+(data.deletable?'ok':'remove')+'"></span>';
			}
		},
		{ data: null, render: function (data, type, row ) {
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
