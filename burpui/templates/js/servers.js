
/***
 * Here is the 'servers' part
 * It is available on the global clients view
 */

/***
 * _servers: function that retrieve up-to-date informations from the burp server
 *  The JSON is then parsed into a table
 */
var _servers = function() {
	url = '{{ url_for("servers_json") }}';
	$.getJSON(url, function(data) {
		$('#table-servers > tbody:last').empty();
		if (!data.results) {
			if (data.notif) {
				$.each(data.notif, function(i, n) {
					notif(n[0], n[1]);
				});
			}
			return;
		}
		$.each(data.results, function(j, c) {
			cl = '';
			glyph = 'glyphicon-ok';
			if (!c.connected) {
				cl = ' danger';
				glyph = 'glyphicon-remove';
			}
			$('#table-servers > tbody:last').append('<tr class="clickable'+cl+'" style="cursor: pointer;"><td><a href="{{ url_for("clients") }}?server='+c.name+'" style="color: inherit; text-decoration: inherit;">'+c.name+'</a></td><td>'+c.clients+'</td><td><span class="glyphicon '+glyph+'"></span></td></tr>');
		});
	});
};
