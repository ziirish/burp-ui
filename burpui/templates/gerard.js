var NOTIF_SUCCESS = 0;
var NOTIF_WARNING = 1;
var NOTIF_ERROR   = 2;
var NOTIF_INFO    = 3;

var SESSION_TAG = $('meta[name=session]').attr("content");
var _EXTRA = $('meta[name=_extra]').attr('content');
var AJAX_CACHE = true;

var _ajax_setup = function() {
	$.ajaxSetup({
		headers: { 'X-From-UI': true, 'X-Session-Tag': SESSION_TAG },
		data: { '_session': SESSION_TAG, '_extra': _EXTRA },
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

// NOTE: only escapes a " if it's not already escaped
function escapeDoubleQuotes(str) {
	if (str) {
		return str.replace(/\\([\s\S])|(")/g,"\\$1$2"); // thanks @slevithan!
	}
	return '';
}

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
			i = '<i class="fa fa-fw fa-check-circle" aria-hidden="true"></i>&nbsp;';
			break;
		case NOTIF_WARNING:
			t = 'warning';
			i = '<i class="fa fa-fw fa-question-circle" aria-hidden="true"></i>&nbsp;';
			break;
		case NOTIF_ERROR:
			t = 'danger';
			i = '<i class="fa fa-fw fa-exclamation-circle" aria-hidden="true"></i>&nbsp;';
			break;
		case NOTIF_INFO:
			t = 'info';
			i = '<i class="fa fa-fw fa-info-circle" aria-hidden="true"></i>&nbsp;';
		default:
			t = 'info';
			i = '<i class="fa fa-fw fa-info-circle" aria-hidden="true"></i>&nbsp;';
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
	if (!json) {
		return false;
	}
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
	} else if ('data' in xhr) {
		errorsHandler(xhr.data);
		return true;
	}
	return false;
};

var buiFail = function(xhr, stat, err) {
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
var _last_running_status = undefined;
var _last_call = 0;
var _check_running = function(force) {
	{% if server -%}
	var url = '{{ url_for(api_running_backup, server=server) }}';
	{% else -%}
	var url = '{{ url_for(api_running_backup) }}';
	{% endif -%}
	var now = Date.now();
	if ((now - _last_call) < 5*1000 && !force) {
		return;
	}
	_last_call = now;
	$.getJSON(url, function(data) {
		{% if clients and overview -%}
		if (_last_running_status != data.running || force) {
			$( document ).trigger('refreshClientsStatesEvent', data.running);
		}
		{% endif -%}
		{% if client and overview -%}
		if (_last_running_status != data.running || force) {
			$( document ).trigger('refreshClientStatusEvent', data.running);
		}
		{% endif -%}
		if (data.running) {
			$('#toblink').addClass('blink');
		} else {
			$('#toblink').removeClass('blink');
		}
		_last_running_status = data.running;
	});
};
{% endif -%}

{% if not login -%}

var substringMatcher = function(objs) {
	return function findMatches(q, cb) {
		var matches, substringRegex;

		// an array that will be populated with substring matches
		matches = [];

		// regex used to determine if a string contains the substring `q`
		substrRegex = new RegExp(q, 'i');

		// iterate through the pool of strings and for any string that
		// contains the substring `q`, add it to the `matches` array
		$.each(objs, function(i, obj) {
			if (substrRegex.test(obj.name)) {
				matches.push(obj);
			}
		});

		cb(matches);
	};
};

var _clients_all = [];

	{% if config.STANDALONE -%}

$.get("{{ url_for('api.clients_all') }}")
	.done(function (data) {
		_clients_all = data;

		/***
		 * Map out _clients_bh to our input with the typeahead plugin
		 */
		$('#input-client').typeahead({
			highlight: true
		},
		{
			name: 'clients',
			displayKey: 'name',
			source: substringMatcher(_clients_all),
		}).on('typeahead:selected', function(obj, datum, name) {
			window.location = '{{ url_for("view.client") }}?name='+datum.name;
		});

	});

	{% else -%}

		{% for srv in config.SERVERS -%}

var _clients_{{ srv|regex_replace("[^a-z0-9_]", "_") }} = [];

		{% endfor -%}

$.get("{{ url_for('api.clients_all') }}")
	.done(function (data) {
		_clients_all = data;
		$.each(_clients_all, function(i, v) {
			window['_clients_'+v.agent].push(v);
		});
	});


$('#input-client').typeahead({
	highlight: true
},
		{% for srv in config.SERVERS -%}
{
	name: '{{ srv }}',
	displayKey: 'name',
	source: substringMatcher(_clients_{{ srv|regex_replace("[^a-z0-9_]", "_") }}),
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
	window.location = '{{ url_for("view.client") }}?name='+datum.name+'&serverName='+datum.agent;
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
{% set is_client_func = True -%}
{% endif -%}

{% if backup and report and client -%}
{% include "js/backup-report.js" %}
{% set is_client_func = True -%}
{% endif -%}

{% if not backup and report and client -%}
{% include "js/client-report.js" %}
{% set is_client_func = True -%}
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

{% if admin -%}
	{% if authentication -%}
{% include "js/admin/authentication.js" %}
	{% elif authorization -%}
		{% if grant -%}
{% include "js/admin/grant-authorization.js" %}
		{% elif group -%}
{% include "js/admin/group-authorization.js" %}
		{% endif -%}
	{% elif sessions -%}
{% include "js/admin/sessions.js" %}
	{% elif authorizations -%}
{% include "js/admin-authorizations.js" %}
	{% elif authentications -%}
{% include "js/admin-authentications.js" %}
	{% elif backends -%}
{% include "js/admin-backends.js" %}
	{% endif -%}
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
				$(this).find('.dtl').stop().animate({width: 'show'}, 100);
			},
			// mouse out
			function() {
				$(this).find('.dtl').stop().animate({width: 'hide'}, 100);
			}
		);
		target.find('.dtl').hide();
		$.each(target, function(i, elmt) {
			if ($(elmt).is(':hover')) {
				$(elmt).find('.dtl').stop().animate({width: 'show'}, 100);
				// there should be only one highlighted element
				return;
			}
		});
	}
}

{% if not report and not login -%}
{% set autorefresh = config.REFRESH -%}
var auto_refresh = undefined;
var schedule_refresh = function() {
	auto_refresh = setTimeout(auto_refresh_function, {{ autorefresh * 1000 }});
}
var cancel_refresh = function() {
	if (auto_refresh) {
		clearTimeout(auto_refresh);
		auto_refresh = undefined;
	}
}
var auto_refresh_function = function(oneshot) {
	{% if clients -%}
	_clients();
	{% endif -%}
	{% if client and not settings -%}
	_client();
	{% endif -%}
	{% if servers and overview -%}
	_servers();
	{% endif -%}
	if (!oneshot) {
		cancel_refresh()
		schedule_refresh();
	}
};
{% endif -%}

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
		AJAX_CACHE = false;
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
		{% if admin -%}
		_admin();
		{% endif -%}
	});

	/***
	 * add a listener to the '.clickable' element dynamically added in the document (see _client and _clients function)
	 */
	$( document ).on('click', '.clickable', function(e) {
		var that = e.target;
		if ($(that).hasClass('no-link')) {
			return;
		}
		if (!$(this).closest('table').hasClass('collapsed')) {
			var $that = $(this);
			var callback = function() {
				window.location = $that.find('a').attr('href');
			};
			if (typeof __refresh_running !== "undefined") {
				_cache_id = new Date().getTime();
				$.getJSON('{{ url_for("api.ping") }}', callback);
			} else {
				callback();
			}
		}
	});
	$( document ).on('click', 'td.child', function(e) {
		var that = e.target
		if ($(that).hasClass('no-link')) {
			return;
		}
		$before = $(this).parent().prev();
		if ($before.hasClass('clickable')) {
			var callback = function() {
				window.location = $before.find('a').attr('href');
			};
			if (typeof __refresh_running !== "undefined") {
				_cache_id = new Date().getTime();
				$.getJSON('{{ url_for("api.ping") }}', callback);
			} else {
				callback();
			}
		}
	});
	$( document ).on('click', 'a', function(e) {
		if (typeof __refresh_running !== "undefined") {
			e.preventDefault();
			var target = this.href;
			_cache_id = new Date().getTime();
			$.getJSON('{{ url_for("api.ping") }}', function() { window.location = target; });
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
	{% if admin -%}
	_admin();
	{% endif -%}

	{% if not report and not login -%}
	/***
	 * auto-refresh our page if needed
	 */
	schedule_refresh();
	{% endif -%}

	{% if not login -%}
		{% if (not config.WS_AVAILABLE or not config.WITH_CELERY or not config.WS_ENABLED) and config.LIVEREFRESH > 0 -%}
	/***
	 * Javascript Loop
	 */
	var refresh_running = undefined;
	var refresh_function = function() {
		_check_running();
		if (refresh_running) {
			clearTimeout(refresh_running);
		}
		refresh_running = setTimeout(refresh_function, {{ config.LIVEREFRESH * 1000 }});
	};
	refresh_running = setTimeout(refresh_function, {{ config.LIVEREFRESH * 1000 }});
		{% endif -%}
	{% endif -%}
});

$(window).scroll(function() {
	if ($(this).scrollTop() >= 50 && $('.sidebar').height() >= 400) {    // If page is scrolled more than 50px
		$('#back-to-top').fadeIn(200);    // Fade in the arrow
	} else {
		$('#back-to-top').fadeOut(200);   // Else fade out the arrow
	}
});

{% if not login and config.WS_AVAILABLE and config.WS_ENABLED -%}
{% include "js/websocket.js" %}
{% endif -%}

{% import 'macros.html' as macros %}
{{ macros.smooth_scrolling() }}
