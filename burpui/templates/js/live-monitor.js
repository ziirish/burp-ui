
_parse_live_result = function(data, serv) {
	var res = '';
	if (!data.results || data.results.length === 0) {
		return res;
	}
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
				if (d) {
					res += d;
				}
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
						if (d) {
							res += d;
						}
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
	urls.push({'url': '{{ url_for("api.running_clients", client=cname) }}?server={{ s }}', 'serv': '{{ s }}'});
	{% endfor -%}
	html = '';
	$.each(urls, function(i, rec) {
		$.getJSON(rec['url'], function(data) {
			html += _parse_live_result(data, rec['serv']);
		});
	});
	{% if server -%}
	redirect = '{{ url_for("home", server=server) }}';
	{% else -%}
	redirect = '{{ url_for("home") }}';
	{% endif -%}
	if (!html) {
		document.location = redirect;
	}
	$('#live-container').html(html);
};
{% else -%}
_live = function() {
	{% if config.STANDALONE -%}
	url = '{{ url_for("api.running_clients", client=cname) }}';
	{% else -%}
	url = '{{ url_for("api.running_clients", server=server, client=cname) }}';
	{% endif -%}
	html = ''
	$.getJSON(url, function(data) {
		html += _parse_live_result(data);
	});
	{% if server -%}
	redirect = '{{ url_for("home", server=server) }}';
	{% else -%}
	redirect = '{{ url_for("home") }}';
	{% endif -%}
	if (!html) {
		document.location = redirect;
	}
	$('#live-container').html(html);
};
{% endif -%}
