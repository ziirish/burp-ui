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

	$http.get('{{ url_for("api.history", client=cname, server=server) }}')
		.success(function(data, status, headers, config) {
			$scope.eventSources.splice(0);
			angular.forEach(data, function(source) {
				$scope.eventSources.push(source);
			});
		});

	$scope.eventRender = function( event, element, view ) {
		element.attr({
			'tooltip-placement': 'bottom',
			'uib-tooltip': event.title+' Duration: '+_time_human_readable((new Date(event.end) - new Date(event.start))/1000),
		});
		$compile(element)($scope);
	};

	$scope.uiConfig = {
		calendar: {
			editable: false,
			eventLimit: true,
			firstDay: 1,
			header:{
				left: 'month agendaWeek agendaDay',
				center: 'title',
				right: 'today prev,next'
			},
			eventRender: $scope.eventRender
		}
	};
});
