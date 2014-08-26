
_live = function() {
	url = '{{ url_for("running_clients") }}';
	html = ''
	$.getJSON(url, function(data) {
		if (!data.results) {
			return;
		}
		if (data.results.length === 0) {
			document.location = '{{ url_for("home") }}';
		}
		$.each(data.results, function(i, c) {
			u = '{{ url_for("render_live_tpl") }}?name='+c;
			$.get(u, function(d) {
				html += d;
			});
		});
	});
	$('#live-container').html(html);
};
