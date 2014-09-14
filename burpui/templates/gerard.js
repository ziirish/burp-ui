
var pad = function(num, size) {
	var s = "0000000" + num;
	return s.substr(s.length-size);
};

var notif = function(type, message) {
	var t = '';
	switch(type) {
		case 0:
			t = 'success';
			i = '<span class="glyphicon glyphicon-ok-sign"></span> ';
			break;
		case 1:
			t = 'warning';
			i = '<span class="glyphicon glyphicon-question-sign"></span> ';
			break;
		case 2:
			t = 'danger';
			i = '<span class="glyphicon glyphicon-exclamation-sign"></span> ';
			break;
		case 3:
		default:
			t = 'info';
			i = '<span class="glyphicon glyphicon-info-sign"></span> ';
			break;
	}
	e = $('<div class="alert alert-dismissable alert-'+t+'">'+
			'<button type="button" class="close" data-dismiss="alert">×</button>'+
			i+message+
		  '</div>');
	$('#bui-notifications').append(e).show();
	e.animate({opacity:1}, 5000, 'linear', function() { e.animate({opacity:0}, 2000, 'linear', function() {e.remove(); }); });
};

{% if not login -%}
	{% if config.STANDALONE -%}

var _check_running = function() {
	url = '{{ url_for("backup_running", server=server) }}';
	$.getJSON(url, function(data) {
		if (data.results) {
			$('#toblink').addClass('blink');
		} else {
			$('#toblink').removeClass('blink');
		}
	});
};
	{% else -%}
var _check_running = function() {
	return false;
};
	{% endif -%}
{% endif -%}

{% if config.STANDALONE -%}
/***
 * _clients_bh: Bloodhound object used for the autocompletion of the input field
 */
var _clients_bh = new Bloodhound({	
	datumTokenizer: Bloodhound.tokenizers.obj.whitespace('name'),
	queryTokenizer: Bloodhound.tokenizers.whitespace,
	limit: 10,
	prefetch: {
		url: '{{ url_for("clients_json", server=server) }}',
		filter: function(list) {
			if (list.results) {
				return list.results;
			}
			return new Array();
		}
	}
});

_clients_bh.initialize();

/***
 * Map out _clients_bh to our input with the typeahead plugin
 */
$('#input-client').typeahead({
	highlight: true
},
{
	name: 'clients',
	displayKey: 'name',
	source: _clients_bh.ttAdapter()
});
{% else -%}
	{% for srv in config.SERVERS -%}

var _{{ srv }}_bh = new Bloodhound({
	datumTokenizer: Bloodhound.tokenizers.obj.whitespace('name'),
	queryTokenizer: Bloodhound.tokenizers.whitespace,
	limit: 10,
	prefetch: {
		url: '{{ url_for("clients_json", server=srv) }}',
		filter: function(list) {
			if (list.results) {
				return list.results;
			}
			return new Array();
		}
	}
});

_{{ srv }}_bh.initialize();
	{% endfor -%}


$('#input-client').typeahead({
	highlight: true
},
	{% for srv in config.SERVERS -%}

{
	name: '{{ srv }}',
	displayKey: 'name',
	source: _{{ srv }}_bh.ttAdapter(),
	templates: {
		header: '<h3 class="server-name">{{ srv }}</h3>'
	}
		{% if loop.last -%}

}
		{% else -%}

},
		{% endif -%}
	{% endfor -%}
).on('typeahead:selected', function(obj, datum, name) {
	window.location = '{{ url_for("client") }}?name='+datum.name+'&server='+name;
});
{% endif -%}

{% if servers and overview -%}
{% include "js/servers.js" %}
{% endif -%}

{% if clients and overview -%}
{% include "js/clients.js" %}
{% endif -%}

{% if clients and report -%}
{% include "js/clients-report.js" %}
{% endif -%}

{% if client and overview -%}
{% include "js/client.js" %}
{% endif -%}

{% if backup and report and client -%}
{% include "js/backup-report.js" %}
{% endif -%}

{% if not backup and report and client -%}
{% include "js/client-report.js" %}
{% endif -%}

{% if live -%}
{% include "js/live-monitor.js" %}
{% endif -%}

var _async_ajax = function(b) {
	$.ajaxSetup({
		async: b
	});
};

$(function() {
	_async_ajax(false);

	/***
	 * Show the notifications
	 */
	$('#bui-notifications > div').each(function() {
		var e = $(this);
		e.animate({opacity:1}, 5000, 'linear', function() { e.animate({opacity:0}, 2000, 'linear', function() {e.remove(); }); });
	});

	/***
	 * show details in topbar
	 */
	$('li.detail').hover(
		// mouse in
		function() {
			$(this).find('.dtl').removeClass('hidden-md hidden-lg');
		},
		// mouse out
		function() {
			$(this).find('.dtl').addClass('hidden-md hidden-lg');
		}
	);

	/***
	 * Action on the 'refresh' button
	 */
	$('#refresh').on('click', function(e) {
		e.preventDefault();
		{% if clients -%}
		_clients();
		{% endif -%}
		{% if client -%}
		_client();
		{% endif -%}
		{% if live -%}
		_live();
		{% endif -%}
		{% if not login -%}
		//_check_running();
		{% endif -%}
		{% if servers and overview -%}
		_servers();
		{% endif -%}
	});

	{% if config.STANDALONE -%}
	/***
	 * trigger action on the 'search field' when the 'enter' key is pressed
	 */
	var search = $('input[id="input-client"]');
	search.keypress(function(e) {
		if (e.which == 13) {
			window.location = '{{ url_for("client", server=server) }}?name='+search.val();
		}
	});
	{% endif -%}

	/***
	 * add a listener to the '.clickable' element dynamically added in the document (see _client and _clients function)
	 */
	$( document ).on('click', '.clickable', function() {
		window.location = $(this).find('a').attr('href');
	});

	/***
	 * initialize our page if needed
	 */
	{% if not login -%}
	//_check_running();
	{% endif -%}
	{% if clients -%}
	_clients();
	{% endif -%}
	{% if client -%}
	_client();
	{% endif -%}
	{% if live -%}
	_live();
	{% endif -%}
	{% if servers and overview -%}
	_servers();
	{% endif -%}

	{% if not report and not login -%}
	/***
	 * auto-refresh our page if needed
	 */
	var auto_refresh = setInterval(function() {
		{% if clients -%}
		_clients();
		{% endif -%}
		{% if client -%}
		_client();
		{% endif -%}
		{% if live -%}
		_live();
		{% endif -%}
		{% if servers and overview -%}
		_servers();
		{% endif -%}
		return;
	}, {{ config.REFRESH * 1000 }});
	{% endif -%}

	{% if not login -%}
	var refresh_running = setInterval(function () {
		//_check_running();
	}, {{ config.REFRESH * 1000 }});
	{% endif -%}

	{% if tree -%}
	{% include "js/client-browse.js" %}
	{% endif -%}
});
