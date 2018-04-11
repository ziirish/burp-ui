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
	var vm = this;
	var _g_promises = [];
	$scope.validGrantInput = true;
	$scope.grantValue = '{{ _("Loading, please wait...") }}';
	$scope.isLoading = true;
	$scope.orig = {};
	vm.updateGroup = {};
	vm.updateGroup.backendUsers = [];

	var g = $http.get('{{ url_for("api.acl_group_members", backend=backend, name=group) }}', { headers: { 'X-From-UI': true } })
		.then(function (response) {
			var content = '';
			try {
				content = JSON.stringify(JSON.parse(response.data.grant), null, 4);
			} catch (e) {
				content = response.data.grant;
			}
			$scope.orig['grantValue'] = content;
			$scope.grantValue = content;
			vm.updateGroup.groupMembers = response.data.members;
			$scope.orig['groupMembers'] = response.data.members;
			$scope.isLoading = false;
		})
	  .catch(function() {
			$scope.grantValue = '';
			$scope.isLoading = false;
			vm.updateGroup.groupMembers = [];
		});
	_g_promises.push(g);

	g = $http.get('{{ url_for("api.acl_grants", backend=backend) }}', { headers: { 'X-From-UI': true } })
		.then(function (response) {
			_.forEach(response.data, function(user) {
				vm.updateGroup.backendUsers.push(user);
			});
		});
	_g_promises.push(g);

	g = $http.get('{{ url_for("api.acl_groups", backend=backend) }}', { headers: { 'X-From-UI': true } })
		.then(function (response) {
			_.forEach(response.data, function(group) {
				group['id'] = '@'+group['id'];
				vm.updateGroup.backendUsers.push(group);
			});
		});
	_g_promises.push(g);

	$q.all(_g_promises).finally(function () {
		var _all = _.map(vm.updateGroup.backendUsers, 'id');
		var missing = _.difference(vm.updateGroup.groupMembers, _all);
		if (missing.length > 0) {
			_.forEach(missing, function(name) {
				vm.updateGroup.backendUsers.push({ id: name });
			});
		}
	});

	$scope.doUpdateGroup = function(e) {
		e.preventDefault();
		var promises = [];
		var form = $(e.target);
		var removed = _.difference($scope.orig.groupMembers, vm.updateGroup.groupMembers);
		var added = _.difference(vm.updateGroup.groupMembers, $scope.orig.groupMembers);
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
		if ($scope.grantValue != $scope.orig.grantValue) {
			disableSubmit();
			var p = $http({
				url: '{{ url_for("api.acl_groups", backend=backend, name=group) }}',
				method: 'POST',
				data: {
					grant: $scope.grantValue ? JSON.stringify(JSON.parse($scope.grantValue)) : "", // remove indentation
				},
				headers: {
					'X-From-UI': true,
				},
			})
			.catch(buiFail)
			.then(function(response) {
				$scope.orig.grantValue = $scope.grantValue;
				notifAll(response.data);
			});
			promises.push(p);
		}
		if (removed.length > 0) {
			disableSubmit();
			var p = $http({
				url: '{{ url_for("api.acl_group_members", backend=backend, name=group) }}',
				method: 'DELETE',
				params: {
					memberNames: removed,
				},
				headers: {
					'X-From-UI': true,
				},
			})
			.catch(buiFail)
			.catch(function () {
				vm.updateGroup.groupMembers = $scope.orig.groupMembers;
			})
			.then(function (response) {
				$scope.orig.groupMembers = vm.updateGroup.groupMembers;
				notifAll(response.data);
			});
			promises.push(p);
		}
		if (added.length > 0) {
			disableSubmit();
			var p = $http({
				url: '{{ url_for("api.acl_group_members", backend=backend, name=group) }}',
				method: 'PUT',
				data: {
					memberNames: added,
				},
				headers: {
					'X-From-UI': true,
				},
			})
			.catch(buiFail)
			.catch(function () {
				vm.updateGroup.groupMembers = $scope.orig.groupMembers;
			})
			.then(function (response) {
				$scope.orig.groupMembers = vm.updateGroup.groupMembers;
				notifAll(response.data);
			});
			promises.push(p);
		}
		$q.all(promises).finally(function() { enableSubmit(); });
	};
}]);
