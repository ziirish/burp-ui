{% import 'macros.html' as macros %}

var _admin = function() {
	// do nothing
	return true;
};

/* placeholder */
var app = angular.module('MainApp', ['ngSanitize', 'ui.select', 'mgcrea.ngStrap', 'datatables']);

app.config(function(uiSelectConfig) {
	uiSelectConfig.theme = 'bootstrap';
});

{{ macros.angular_ui_ace() }}

app.controller('AdminCtrl', ['$scope', '$http', '$q', '$scrollspy', 'DTOptionsBuilder', 'DTColumnDefBuilder', function($scope, $http, $q, $scrollspy, DTOptionsBuilder, DTColumnDefBuilder) {
	$scope.validGrantInput = true;
	$scope.grantValue = '{{ _("Loading, please wait...") }}';
	$scope.isLoading = true;
	$scope.isAdmin = false;
	$scope.isAdminEnabled = false;
	$scope.isModerator = false;
	$scope.isModeratorEnabled = false;
	$scope.orig = {};

	$http.get('{{ url_for("api.acl_grants", backend=backend, name=grant) }}', { headers: { 'X-From-UI': true } })
		.then(function (response) {
			var content = '';
			if (response.data.length > 0) {
				try {
					content = JSON.stringify(JSON.parse(response.data[0].grant), null, 4);
				} catch (e) {
					content = response.data[0].grant;
				}
			}
			$scope.orig['grantValue'] = content;
			$scope.grantValue = content;
			$scope.isLoading = false;
		})
	  .catch(function() {
			$scope.grantValue = '';
			$scope.isLoading = false;
		});
	$http.get('{{ url_for("api.acl_is_admin", backend=backend, member=grant) }}', { headers: { 'X-From-UI': true } })
		.then(function (response) {
			$scope.isAdmin = response.data.admin;
			$scope.orig['admin'] = response.data.admin;
			$scope.isAdminEnabled = true;
		});
	$http.get('{{ url_for("api.acl_is_moderator", backend=backend, member=grant) }}', { headers: { 'X-From-UI': true } })
		.then(function (response) {
			$scope.isModerator = response.data.moderator;
			$scope.orig['moderator'] = response.data.moderator;
			$scope.isModeratorEnabled = true;
		});

	$scope.updateGrants = function(e) {
		e.preventDefault();
		var promises = [];
		var form = $(e.target);
		submit = form.find('button[type="submit"]');
		sav = submit.html();
		var disableSubmit = function() {
			submit.html('<i class="fa fa-fw fa-spinner fa-pulse" aria-hidden="true"></i>&nbsp;{{ _("Updating") }}');
			submit.attr('disabled', true);
		};
		var enableSubmit = function() {
			submit.html(sav);
			submit.attr('disabled', false);
		};
		if ($scope.isAdmin !== $scope.orig.admin) {
			disableSubmit();
			var url = '{{ url_for("api.acl_admin", backend=backend, member=grant) }}';
			var method = 'PUT';
			if (!$scope.isAdmin) {
				method = 'DELETE';
			}
			var p = $http({
				url: url,
				method: method,
				headers: { 'X-From-UI': true },
			})
			.then(function(response) {
				$scope.orig.admin = $scope.isAdmin;
				notifAll(response.data);
			})
			.catch(buiFail);
			promises.push(p);
		}
		if ($scope.isModerator !== $scope.orig.moderator) {
			disableSubmit();
			var url = '{{ url_for("api.acl_moderator", backend=backend, member=grant) }}';
			var method = 'PUT';
			if (!$scope.isModerator) {
				method = 'DELETE';
			}
			var p = $http({
				url: url,
				method: method,
				headers: { 'X-From-UI': true },
			})
			.then(function(response) {
				$scope.orig.moderator = $scope.isModerator;
				notifAll(response.data);
			})
			.catch(buiFail);
			promises.push(p);
		}
		if ($scope.grantValue != $scope.orig.grantValue) {
			disableSubmit();
			var p = $http({
				url: '{{ url_for("api.acl_grants", backend=backend, name=grant) }}',
				method: 'POST',
				data: {
					content: JSON.stringify(JSON.parse($scope.grantValue)), // remove indentation
				},
				headers: {
					'X-From-UI': true,
				},
			})
			.then(function(response) {
				$scope.orig.grantValue = $scope.grantValue;
				notifAll(response.data);
			})
			.catch(buiFail);
			promises.push(p);
		}
		$q.all(promises).finally(function() { enableSubmit(); });
	};
}]);
