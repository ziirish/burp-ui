
/***
 * Here is the 'servers' part
 * It is available on the global clients view
 */

/***
 * _servers: function that retrieve up-to-date informations from the burp server
 *  The JSON is then parsed into a table
 */
var _servers_table = $('#table-servers').dataTable( {
	responsive: true,
	ajax: {
		url: '{{ url_for("api.servers_stats") }}',
		dataSrc: function (data) {
			return data;
		},
		error: myFail,
	},
	destroy: true,
	rowCallback: function( row, data ) {
		if (!data.alive) {
			row.className += ' danger';
		}
		row.className += ' clickable';
	},
	columns: [
		{ data: null, render: function ( data, type, row ) {
				href = '{{ url_for("view.clients") }}?serverName='+data.name;
				if (!data.alive) {
					href = '#';
				}
				return '<a href="'+href+'" style="color: inherit; text-decoration: inherit;">'+data.name+'</a>';
			}
		},
		{ data: 'clients' },
		{ data: null, render: function (data, type, row ) {
				glyph = 'glyphicon-ok';
				if (!data.alive) {
					glyph = 'glyphicon-remove';
				}
				return '<span class="glyphicon '+glyph+'"></span>';
			}
		}
	]
});
var first = true;

var _servers = function() {
	if (first) {
		first = false;
	} else {
		_servers_table.api().ajax.reload( null, false );
	}
};
