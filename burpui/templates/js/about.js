/***
 * The About page is managed with AngularJS.
 * Following is the AngularJS Application and Controller.
 * Our $scope is initialized with a $http request that retrieves a JSON like that:
 * {
 *   'version': 'xxx',
 *   'client': 'yyy',
 *   'server': 'zzz',
 * }
 */
var app = angular.module('MainApp', ['ngSanitize']);

app.controller('AboutCtrl', function($scope, $http) {
	$scope.version = '';
	$scope.client = '';
	$scope.server = '';

	$http.get('{{ url_for("api.about") }}')
		.success(function(data, status, headers, config) {
			$scope.version = data.version;
			$scope.client = data.client;
			$scope.server = data.server;
		});
});
