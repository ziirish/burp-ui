
_parse_live_result = function(data, serv) {
	{% if server -%}
	redirect = '{{ url_for("home", server=server) }}';
	{% else -%}
	if (serv) {
		redirect = '{{ url_for("home") }}?server='+serv;
	} else {
		redirect = '{{ url_for("home") }}';
	}
	{% endif -%}
	if (!data.results || data.results.length === 0) {
		document.location = redirect;
	}
	var res = '';
	$.each(data.results, function(i, c) {
		if (c instanceof String || typeof c == 'string') {
			{% if server -%}
			u = '{{ url_for("render_live_tpl", server=server) }}?name='+c;
			{% else -%}
			if (serv) {
				u = '{{ url_for("render_live_tpl") }}?name='+c+'&server='+serv;
			} else {
				u = '{{ url_for("render_live_tpl") }}?name='+c;
			}
			{% endif -%}
			$.get(u, function(d) {
				res += d;
			});
		} else {
			$.each(c, function(j, a) {
				$.each(a, function(k, cl) {
					{% if server -%}
					u = '{{ url_for("render_live_tpl", server=server) }}?name='+cl;
					{% else -%}
					if (serv) {
						u = '{{ url_for("render_live_tpl") }}?name='+cl+'&server='+serv;
					} else {
						u = '{{ url_for("render_live_tpl") }}?name='+cl;
					}
					{% endif -%}
					$.get(u, function(d) {
						res += d;
					});
				});
			});
		}
	});
	return res;
};

{% if not config.STANDALONE and not server -%}
_live = function() {
	urls = Array();
	{% for s in config.SERVERS -%}
	urls.append({'url': '{{ url_for("running_clients") }}'+?server={{ s }}, 'serv': {{ s }}});
	{% endfor -%}
	html = '';
	$.each(urls, function(i, rec) {
		$.getJSON(rec['url'], function(data) {
			html += _parse_live_result(data, rec['serv']);
		});
	});
	$('#live-container').html(html);
};
{% else -%}
_live = function() {
	{% if config.STANDALONE -%}
	url = '{{ url_for("running_clients") }}';
	{% else -%}
	url = '{{ url_for("running_clients", server=server) }}';
	{% endif -%}
	html = ''
	$.getJSON(url, function(data) {
		html += _parse_live_result(data);
	});
	$('#live-container').html(html);
};
{% endif -%}
