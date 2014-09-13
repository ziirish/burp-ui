
_live = function() {
	url = '{{ url_for("running_clients", server=server) }}';
	html = ''
	$.getJSON(url, function(data) {
		if (!data.results || data.results.length === 0) {
			document.location = '{{ url_for("home", server=server) }}';
		}
		$.each(data.results, function(i, c) {
			u = '{{ url_for("render_live_tpl", server=server) }}?name='+c;
			$.get(u, function(d) {
				html += d;
			});
		});
	});
	$('#live-container').html(html);
};
