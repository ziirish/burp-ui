
/***
 * Here is the 'servers' part
 * It is available on the global clients view
 */

/***
 * _servers: function that retrieve up-to-date informations from the burp server
 *  The JSON is then parsed into a table
 */
{% import 'macros.html' as macros %}
var _servers_table = $('#table-servers').DataTable( {
	{{ macros.translate_datatable() }}
	{{ macros.get_page_length() }}
	responsive: true,
	processing: true,
	fixedHeader: true,
	ajax: {
		url: '{{ url_for("api.servers_stats") }}',
		dataSrc: function (data) {
			return data;
		},
		error: myFail,
		headers: { 'X-From-UI': true },
		cache: AJAX_CACHE,
	},
	rowId: 'name',
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
		_servers_table.ajax.reload( null, false );
		AJAX_CACHE = true;
	}
};

{{ macros.page_length('#table-servers') }}
