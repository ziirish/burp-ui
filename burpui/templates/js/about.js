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
	$scope.burp = [];

	$http.get('{{ url_for("api.about") }}', { headers: { 'X-From-UI': true } })
		.then(function(response) {
			$scope.version = response.data.version;
			$scope.api = response.data.api;
			$scope.burp = response.data.burp;
		});
});
