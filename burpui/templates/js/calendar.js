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
var _client = function() {};
var _clients = function() {};
var _servers = function() {};

var app = angular.module('MainApp', ['ngSanitize', 'ui.calendar', 'ui.bootstrap']);

app.controller('CalendarCtrl', function($scope, $http, $compile, uiCalendarConfig) {
	$scope.eventSources = [];

	$scope.eventRender = function( event, element, view ) {
		element.attr({
			'tooltip-placement': 'bottom',
			'uib-tooltip': event.title+' Duration: '+_time_human_readable((new Date(event.end) - new Date(event.start))/1000),
			'tooltip-append-to-body': true,
		});
		$compile(element)($scope);
	};

	$scope.uiConfig = {
		calendar: {
			editable: false,
			eventLimit: true,
			firstDay: 1,
			locale: '{{ g.locale }}',
			header:{
				left: 'month,listWeek',
				center: 'title',
				right: 'today prev,next'
			},
			eventRender: $scope.eventRender,
			viewRender: function(view, element) {
				$scope.fetchEvents(view.start.format(), view.end.format());
			}
		}
	};

	$scope.fetchEvents = function(start, end) {
		{% if config.WITH_CELERY -%}
		var feed_url = '{{ url_for("api.async_history", client=cname, server=server) }}?start='+start+'&end='+end;
		{% else -%}
		var feed_url = '{{ url_for("api.history", client=cname, server=server) }}?start='+start+'&end='+end;
		{% endif -%}
		$http.get(feed_url, { headers: { 'X-From-UI': true } })
			.success(function(data, status, headers, config) {
				$scope.eventSources.splice(0);
				angular.forEach(data, function(source) {
					$scope.eventSources.push(source);
				});
			});
	};
});
