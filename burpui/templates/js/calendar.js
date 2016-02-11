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
var app = angular.module('MainApp', ['ngSanitize', 'ui.calendar', 'ui.bootstrap']);

app.controller('CalendarCtrl', function($scope, $http) {
	$scope.eventSources = [];

	$http.get('{{ url_for("api.history", client=cname, server=server) }}')
		.success(function(data, status, headers, config) {
			$scope.eventSources = data;
		});
});
