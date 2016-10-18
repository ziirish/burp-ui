var NOTIF_SUCCESS = 0;
var NOTIF_WARNING = 1;
var NOTIF_ERROR   = 2;
var NOTIF_INFO    = 3;

var _ajax_setup = function() {
	$.ajaxSetup({
		headers: { 'X-From-UI': true },
	});
};
_ajax_setup();

var pad = function(num, size) {
	var s = "0000000" + num;
	return s.substr(s.length-size);
};

var _time_human_readable = function(d) {
	str = '';
	var days = Math.floor((d % 31536000) / 86400);
	var hours = Math.floor(((d % 31536000) % 86400) / 3600);
	var minutes = Math.floor((((d % 31536000) % 86400) % 3600) / 60);
	var seconds = (((d % 31536000) % 86400) % 3600) % 60;
	if (days > 0) {
		str += days;
		if (days > 1) {
			str += ' days ';
		} else {
			str += ' day ';
		}
	}
	if (hours > 0) {
		str += pad(hours,2)+'H ';
	}
	str += pad(minutes,2)+'m '+pad(seconds,2)+'s';
	return str;
};

var _bytes_human_readable = function(bytes, si) {
	var thresh = si ? 1000 : 1024;
	if(bytes < thresh) return bytes + ' B';
	var units = si ? ['kB','MB','GB','TB','PB','EB','ZB','YB'] : ['KiB','MiB','GiB','TiB','PiB','EiB','ZiB','YiB'];
	var u = -1;
	do {
		bytes /= thresh;
		++u;
	} while(bytes >= thresh);
	return bytes.toFixed(1)+' '+units[u];
};

var notifAll = function(messages, forward) {
	forward = (typeof forward === "undefined") ? false : forward;
	if (messages instanceof Array && messages.length > 0) {
		if (messages[0] instanceof Array) {
			$.each(messages, function(i, n) {
				if (n.length == 3) {
					timeout = n[2];
				} else {
					timeout = undefined;
				}
				if (forward) {
					$.post('{{ url_for("api.alert") }}', {'message': n[1], 'level': String(n[0])});
				} else {
					notif(n[0], n[1], timeout);
				}
			});
		} else {
			if (forward) {
				$.post('{{ url_for("api.alert") }}', {'message': messages[1], 'level': messages[0]});
			} else {
				if (messages.length == 3) {
					timeout = messages[2];
				} else {
					timeout = undefined;
				}
				notif(messages[0], messages[1], timeout);
			}
		}
	}
};

var notif = function(type, message, timeout) {
	timeout = (typeof timeout === "undefined") ? 5000 : timeout;
	var t = '';
	switch(type) {
		case NOTIF_SUCCESS:
			t = 'success';
			i = '<span class="glyphicon glyphicon-ok-sign"></span> ';
			break;
		case NOTIF_WARNING:
			t = 'warning';
			i = '<span class="glyphicon glyphicon-question-sign"></span> ';
			break;
		case NOTIF_ERROR:
			t = 'danger';
			i = '<span class="glyphicon glyphicon-exclamation-sign"></span> ';
			break;
		case NOTIF_INFO:
		default:
			t = 'info';
			i = '<span class="glyphicon glyphicon-info-sign"></span> ';
			break;
	}
	e = $('<div class="alert alert-dismissable alert-'+t+'">'+
			'<button type="button" class="close" data-dismiss="alert">&times;</button>'+
			i+message+
		  '</div>');
	$('#bui-notifications').append(e).show();
	anim(e, timeout);
};

var anim = function(elem, timeout) {
	timeout = (typeof timeout === "undefined") ? 5000 : timeout;
	elem.delay(timeout)
		.fadeOut(2000, function() {elem.remove(); })
		.mouseover(function(){ elem.stop(true, false); elem.fadeIn(); })
		.mouseout(function(){ anim(elem, timeout); });
};

var errorsHandler = function(json) {
	if ('notif' in json) {
		message = json.notif;
	} else if ('message' in json) {
		try {
			message = JSON.parse(json.message);
		} catch(err) {
			message = Array();
			if (typeof(json.message) == 'string') {
				message.push([NOTIF_ERROR, json.message]);
			} else {
				for (field in json.message) {
					message.push([NOTIF_ERROR, field+': '+json.message[field]]);
				}
			}
		}
	} else {
		return false;
	}
	$.each(message, function(i, n) {
		notif(n[0], n[1]);
	});
	return true;
};

var xhrErrorsHandler = function(xhr) {
	if ('responseJSON' in xhr) {
		json = xhr.responseJSON;
		return errorsHandler(json);
	} else if ('responseText' in xhr) {
		notif(NOTIF_ERROR, xhr.responseText);
		return true;
	}
	return false;
};

var myFail = function(xhr, stat, err) {
	if (xhrErrorsHandler(xhr)) {
		return;
	}
	var msg = '<strong>ERROR:</strong> ';
	if (stat && err) {
		msg +=  '<p>'+stat+'</p><pre>'+err+'</pre>';
	} else if (stat) {
		msg += '<p>'+stat+'</p>';
	} else if (err) {
		msg += '<pre>'+err+'</pre>';
	}
	notif(NOTIF_ERROR, msg);
};

{% if config.WITH_CELERY -%}
{% set api_running_backup = "api.async_running_backup" %}
{% else -%}
{% set api_running_backup = "api.running_backup" %}
{% endif -%}
{% if not login -%}
var _check_running = function() {
	{% if server -%}
	url = '{{ url_for(api_running_backup, server=server) }}';
	{% else -%}
	url = '{{ url_for(api_running_backup) }}';
	{% endif -%}
	$.getJSON(url, function(data) {
		if (data.running) {
			$('#toblink').addClass('blink');
		} else {
			$('#toblink').removeClass('blink');
		}
	});
};
{% endif -%}

{% if not login -%}
	{% if config.STANDALONE -%}
/***
 * _clients_bh: Bloodhound object used for the autocompletion of the input field
 */
var _clients_bh = new Bloodhound({
	datumTokenizer: Bloodhound.tokenizers.obj.whitespace('name'),
	queryTokenizer: Bloodhound.tokenizers.whitespace,
	limit: 10,
	prefetch: {
		url: '{{ url_for("api.clients_stats") }}',
		ttl: 1800000,
		cacheKey: '{{ version_id }}{% if current_user and current_user.is_authenticated %}-{{ current_user.get_id() }}{% endif %}',
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
}).on('typeahead:selected', function(obj, datum, name) {
	window.location = '{{ url_for("view.client") }}?name='+datum.name;
});
	{% else -%}
		{% for srv in config.SERVERS -%}

var _{{ srv }}_bh = new Bloodhound({
	datumTokenizer: Bloodhound.tokenizers.obj.whitespace('name'),
	queryTokenizer: Bloodhound.tokenizers.whitespace,
	limit: 10,
	prefetch: {
		url: '{{ url_for("api.clients_stats", server=srv) }}',
		filter: function(data) {
			res = new Array();
			$.each(data, function(i, d) {
				n = d;
				n.server = '{{ srv }}';
				res.push(n);
			});
			return res;
		},
		ttl: 1800000,
		cacheKey: '{{ version_id }}{% if current_user and current_user.is_authenticated %}-{{ current_user.get_id() }}{% endif %}-{{ srv }}',
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
).on('typeahead:selected', function(obj, datum) {
	window.location = '{{ url_for("view.client") }}?name='+datum.name+'&serverName='+datum.server;
});
	{% endif -%}
{% endif -%}


{% if servers and overview -%}
{% include "js/servers.js" %}
{% endif -%}

{% if servers and report -%}
{% include "js/servers-report.js" %}
{% endif -%}

{% if clients and overview -%}
{% include "js/clients.js" %}
{% endif -%}

{% if clients and report -%}
{% include "js/clients-report.js" %}
{% endif -%}

{% if client and overview -%}
{% include "js/client.js" %}
{% set is_client_func = True %}
{% endif -%}

{% if backup and report and client -%}
{% include "js/backup-report.js" %}
{% set is_client_func = True %}
{% endif -%}

{% if not backup and report and client -%}
{% include "js/client-report.js" %}
{% set is_client_func = True %}
{% endif -%}

{% if live -%}
{% include "js/live-monitor.js" %}
{% endif -%}

{% if settings -%}
{% include "js/settings.js" %}
{% endif -%}

{% if about -%}
{% include "js/about.js" %}
{% endif -%}

{% if calendar -%}
{% include "js/calendar.js" %}
{% endif -%}

{% if tree -%}
{% include "js/client-browse.js" %}
{% endif -%}

{% if me -%}
{% include "js/user.js" %}
{% endif -%}

var _fit_menu = function() {
	size = $(window).width();
	target = $('li.detail');
	target.off( "mouseenter mouseleave" );
	if (size <= 768) {
		target.find('.dtl').show();
	} else {
		target.hover(
			// mouse in
			function() {
				$(this).find('.dtl').stop().animate({width: 'toggle'}, 100);
			},
			// mouse out
			function() {
				$(this).find('.dtl').stop().animate({width: 'toggle'}, 100);
			}
		);
		target.find('.dtl').hide();
	}
}

$(function() {

	/***
	 * Show the notifications
	 */
	$('#bui-notifications > div').each(function() {
		var e = $(this);
		if (!e.data('permanent')) {
			anim(e);
		}
	});

	/***
	 * show details in topbar
	 */
	_fit_menu();
	$(window).on('resize', _fit_menu);

	/***
	 * Action on the 'refresh' button
	 */
	$('#refresh').on('click', function(e) {
		e.preventDefault();
		{% if clients -%}
		_clients();
		{% endif -%}
		{% if client and is_client_func -%}
		_client();
		{% endif -%}
		{% if not login -%}
		_check_running();
		{% endif -%}
		{% if servers -%}
		_servers();
		{% endif -%}
		{% if me -%}
		_sessions();
		{% endif -%}
	});

	/***
	 * add a listener to the '.clickable' element dynamically added in the document (see _client and _clients function)
	 */
	$( document ).on('click', '.clickable', function() {
		if (!$(this).closest('table').hasClass('collapsed')) {
			window.location = $(this).find('a').attr('href');
		}
	});
	$( document ).on('click', 'td.child', function() {
		$before = $(this).parent().prev();
		if ($before.hasClass('clickable')) {
			window.location = $before.find('a').attr('href');
		}
	});

	/***
	 * initialize our page if needed
	 */
	{% if not login -%}
	_check_running();
	{% endif -%}
	{% if clients -%}
	_clients();
	{% endif -%}
	{% if client and is_client_func -%}
	_client();
	{% endif -%}
	{% if servers -%}
	_servers();
	{% endif -%}
	{% if me -%}
	_sessions();
	{% endif -%}

	{% if not report and not login -%}
	/***
	 * auto-refresh our page if needed
	 */
	{% set autorefresh = config.REFRESH %}
	var auto_refresh = setInterval(function() {
		{% if clients -%}
		_clients();
		{% endif -%}
		{% if client and not settings -%}
		_client();
		{% endif -%}
		{% if servers and overview -%}
		_servers();
		{% endif -%}
		return;
	}, {{ autorefresh * 1000 }});
	{% endif -%}

	{% if not login -%}
	var refresh_running = setInterval(function () {
		_check_running();
	}, {{ config.REFRESH * 1000 }});
	{% endif -%}
});
