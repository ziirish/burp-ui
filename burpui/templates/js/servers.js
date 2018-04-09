
/***
 * Here is the 'servers' part
 * It is available on the global clients view
 */

var _cache_id = _EXTRA;

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
		data: function (request) {
			request._extra = _cache_id;
		},
		dataSrc: function (data) {
			return data;
		},
		error: buiFail,
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
		{
			data: null,
			render: function ( data, type, row ) {
				if (type === 'filter' || type === 'sort') {
					return data.name;
				}
				href = '{{ url_for("view.clients") }}?serverName='+data.name;
				if (!data.alive) {
					href = '#';
				}
				return '<a href="'+href+'" style="color: inherit; text-decoration: inherit;">'+data.name+'</a>';
			}
		},
		{ data: 'clients' },
		{
			data: 'alive',
			render: function (data, type, row ) {
				if (type === 'filter' || type === 'sort') {
					return data;
				}
				glyph = 'fa-check';
				if (!data) {
					glyph = 'fa-remove';
				}
				return '<i class="fa '+glyph+'"></i>';
			}
		}
	]
});
var first = true;

var _servers = function() {
	if (first) {
		first = false;
	} else {
		if (!AJAX_CACHE) {
			_cache_id = new Date().getTime();
		}
		_servers_table.ajax.reload( null, false );
		AJAX_CACHE = true;
	}
};

{{ macros.page_length('#table-servers') }}
