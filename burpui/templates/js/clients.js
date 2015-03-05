
/***
 * Here is the 'clients' part
 * It is available on the global clients view
 */

/***
 * First we map some burp status with some style
 */
var __status = {
	'client crashed': 'danger',
	'server crashed': 'danger',
	'running': 'info',
};

/***
 * _clients: function that retrieve up-to-date informations from the burp server
 * JSON format:
 * {
 *   "results": [
 *     {
 *       "last": "2014-05-12 19:40:02",
 *       "name": "client1",
 *       "state": "idle"
 *     },
 *     {
 *       "last": "never",
 *       "name": "client2",
 *       "state": "idle"
 *     }
 *   ]
 * }
 *  The JSON is then parsed into a table
 */

/*
var _clients_table = $('#table-clients').DataTable( {
	ajax: '{{ url_for("clients_json", server=server) }}',
	columns: [
*/
var _clients_table = $('#table-clients').dataTable( {
	ajax: {
		url: '{{ url_for("clients_json", server=server) }}',
		dataSrc: 'results'
	},
	destroy: true,
	rowCallback: function( row, data ) {
		if (__status[data.state] != undefined) {
			row.className += ' '+__status[data.state];
		}
		row.className += ' clickable';
	},
	columns: [
		{ data: null, render: function ( data, type, row ) {
				return '<a href="{{ url_for("client", server=server) }}?name='+data.name+'" style="color: inherit; text-decoration: inherit;">'+data.name+'</a>';
			}
		},
		{ data: 'state' },
		{ data: 'last' }
	]
});
var first = true;

var _clients = function() {
	url = '{{ url_for("clients_json", server=server) }}';
	$.getJSON(url, function(data) {
		if (!data.results) {
			if (data.notif) {
				$.each(data.notif, function(i, n) {
					notif(n[0], n[1]);
				});
			}
			return;
		}
		if (first) {
			first = false;
		} else {
			_clients_table.api().ajax.reload( null, false );
		}
	});
};
