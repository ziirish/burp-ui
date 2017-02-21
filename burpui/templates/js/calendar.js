/***
 * The About page is managed with AngularJS.
 * Following is the AngularJS Application and Controller.
 * Our $scope is initialized with a $http request that retrieves a JSON like that:
 * {
 *   'version': 'xxx',
 *   'burp': [
 *	   {
 *       'client': 'yyy',
 *       'server': 'zzz',
 *       'name': 'aaa',
 *     },
 *   ]
 * }
 */
{% import 'macros.html' as macros %}

var _client = function() {};
var _clients = function() {};
var _servers = function() {};

$(document).ready(function() {

	myEventRender = function( event, element, view ) {
		element.attr({
			'title': event.title+', Duration: '+_time_human_readable((new Date(event.end) - new Date(event.start))/1000),
		});
	};

	fetchEvents = function(start, end) {
		{% if config.WITH_CELERY -%}
		var feed_url = '{{ url_for("api.async_history", client=cname, server=server) }}?start='+start+'&end='+end;
		{% else -%}
		var feed_url = '{{ url_for("api.history", client=cname, server=server) }}?start='+start+'&end='+end;
		{% endif -%}
		$.get(feed_url)
			.done(function(data) {
				cal = $('#calendar')
				cal.fullCalendar('removeEventSources');
				$.each(data, function(i, source) {
					if (source) {
						source.cache = true;
						cal.fullCalendar('addEventSource', source);
					}
				});
			});
	};

	$('#calendar').fullCalendar({
		{{ macros.translate_calendar() }}
		editable: false,
		eventLimit: true,
		eventLimitClick: 'day',
		firstDay: 1,
		header:{
			left: 'month,listWeek',
			center: 'title',
			right: 'today prev,next'
		},
		eventRender: myEventRender,
		viewRender: function(view, element) {
			fetchEvents(view.start.format(), view.end.format());
		}
	});
});
