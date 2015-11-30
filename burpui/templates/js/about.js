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
var app = angular.module('MainApp', ['ngSanitize']);

app.controller('AboutCtrl', function($scope, $http) {
	$scope.version = '';
	$scope.api = '';
	$scope.burp = Array();

	$http.get('{{ url_for("api.about") }}')
		.success(function(data, status, headers, config) {
			$scope.version = data.version;
			$scope.api = data.api;
			$scope.burp = data.burp;
		});
});
