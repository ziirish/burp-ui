
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
 * Show the row as warning if there are no backups
 */
var __date = {
	'never': 'warning',
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

var _clients_table = $('#table-clients').dataTable( {
	responsive: true,
	ajax: {
		url: '{{ url_for("api.clients_stats", server=server) }}',
		dataSrc: function (data) {
			if (!data.results) {
				if (data.notif) {
					$.each(data.notif, function(i, n) {
						notif(n[0], n[1]);
					});
				}
				return {};
			}
			return data.results;
		}
	},
	order: [[2, 'desc']],
	destroy: true,
	rowCallback: function( row, data ) {
		if (__status[data.state] != undefined) {
			row.className += ' '+__status[data.state];
		}
		if (__date[data.last] != undefined) {
			row.className += ' '+__date[data.last];
		}
		row.className += ' clickable';
	},
	columns: [
		{ data: null, render: function ( data, type, row ) {
				return '<a href="{{ url_for("view.client", server=server) }}?name='+data.name+'" style="color: inherit; text-decoration: inherit;">'+data.name+'</a>';
			}
		},
		{ data: null, render: function ( data, type, row ) {
				if ('percent' in data) {
					return data.state+' ('+data.percent+'%)';
				}
				return data.state;
			}
		},
		{ data: 'last' }
	]
});
var first = true;

var _clients = function() {
	if (first) {
		first = false;
	} else {
		_clients_table.api().ajax.reload( null, false );
	}
};
