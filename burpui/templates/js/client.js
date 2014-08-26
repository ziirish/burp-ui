
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
var _client = function() {
	url = '{{ url_for("client_json", name=cname) }}';
	$.getJSON(url, function(data) {
		$('#table-client >tbody:last').empty();
		$('#client-alert').hide();
		if (!data.results) {
			$('#table-client').hide();
			$('#client-alert').show();
			return;
		}
		if (data.results.length == 0) {
			$('#table-client').hide();
			$('#client-alert').show();
		} else {
			$.each(data.results.reverse(), function(j, c) {
				$('#table-client> tbody:last').append('<tr class="clickable" style="cursor: pointer;"><td><a href="{{ url_for("client_browse", name=cname) }}?backup='+c.number+'" style="color: inherit; text-decoration: inherit;">'+pad(c.number, 7)+'</a></td><td>'+c.date+'</td></tr>');
			});
		}
	});
};
