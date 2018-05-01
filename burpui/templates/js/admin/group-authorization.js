{% import 'macros.html' as macros %}
{% set gpname = "@"+group %}

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
	$scope.isAdmin = false;
	$scope.isAdminEnabled = false;
	$scope.isModerator = false;
	$scope.isModeratorEnabled = false;
	vm.updateGroup = {};
	vm.updateGroup.backendUsers = [];

	{% if group not in ['moderator', 'admin'] -%}
	var url = '{{ url_for("api.acl_group_members", backend=backend, name=group) }}';
	{% elif group == 'moderator' -%}
	var url = '{{ url_for("api.acl_moderator", backend=backend) }}';
	{% elif group == 'admin' -%}
	var url = '{{ url_for("api.acl_admin", backend=backend) }}';
	{% endif -%}
	var g = $http.get(url, { headers: { 'X-From-UI': true } })
		.then(function (response) {
			{% if group != 'admin' -%}
			var content = '';
			try {
				content = JSON.stringify(JSON.parse(response.data.grant), null, 4);
			} catch (e) {
				content = response.data.grant;
			}
			$scope.orig['grantValue'] = content;
			$scope.grantValue = content;
			{% endif -%}
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

	g = $http.get('{{ url_for("api.auth_users") }}', { headers: { 'X-From-UI': true } })
		.then(function (response) {
			_.forEach(response.data, function(user) {
				vm.updateGroup.backendUsers.push(user);
			});
		});
	_g_promises.push(g);

	{% if group not in  ['moderator', 'admin'] -%}
	$http.get('{{ url_for("api.acl_is_admin", backend=backend, member=gpname) }}', { headers: { 'X-From-UI': true } })
		.then(function (response) {
			$scope.isAdmin = response.data.admin;
			$scope.orig['admin'] = response.data.admin;
			$scope.isAdminEnabled = true;
		});
	$http.get('{{ url_for("api.acl_is_moderator", backend=backend, member=gpname) }}', { headers: { 'X-From-UI': true } })
		.then(function (response) {
			$scope.isModerator = response.data.moderator;
			$scope.orig['moderator'] = response.data.moderator;
			$scope.isModeratorEnabled = true;
		});
	{% endif -%}

	$q.all(_g_promises).finally(function () {
		var _all = _.map(vm.updateGroup.backendUsers, 'id');
		var missing = _.difference(vm.updateGroup.groupMembers, _all);
		if (missing.length > 0) {
			_.forEach(missing, function(name) {
				vm.updateGroup.backendUsers.push({ id: name });
			});
		}
		vm.updateGroup.backendUsers = _.uniqBy(vm.updateGroup.backendUsers, 'id');
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
		{% if group not in ['moderator', 'admin'] -%}
		if ($scope.isAdmin !== $scope.orig.admin) {
			disableSubmit();
			var url = '{{ url_for("api.acl_admin", backend=backend, member=gpname) }}';
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
			var url = '{{ url_for("api.acl_moderator", backend=backend, member=gpname) }}';
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
		{% endif -%}
		{% if group != 'admin' -%}
		if ($scope.grantValue != $scope.orig.grantValue) {
			disableSubmit();
			{% if group != 'moderator' -%}
			var url = '{{ url_for("api.acl_groups", backend=backend, name=group) }}';
			{% else -%}
			var url = '{{ url_for("api.acl_moderator", backend=backend) }}';
			{% endif -%}
			var p = $http({
				url: url,
				method: 'POST',
				data: {
					grant: $scope.grantValue ? JSON.stringify(JSON.parse($scope.grantValue)) : "", // remove indentation
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
		{% endif -%}
		if (removed.length > 0) {
			disableSubmit();
			{% if group not in ['moderator', 'admin'] -%}
			var url = '{{ url_for("api.acl_group_members", backend=backend, name=group) }}';
			{% elif group == 'moderator' -%}
			var url = '{{ url_for("api.acl_moderator", backend=backend) }}';
			{% elif group == 'admin' -%}
			var url = '{{ url_for("api.acl_admin", backend=backend) }}';
			{% endif -%}
			var p = $http({
				url: url,
				method: 'DELETE',
				params: {
					memberNames: removed,
				},
				headers: {
					'X-From-UI': true,
				},
			})
			.then(function (response) {
				$scope.orig.groupMembers = vm.updateGroup.groupMembers;
				notifAll(response.data);
			})
			.catch(buiFail)
			.catch(function () {
				vm.updateGroup.groupMembers = $scope.orig.groupMembers;
			});
			promises.push(p);
		}
		if (added.length > 0) {
			disableSubmit();
			{% if group not in ['moderator', 'admin'] -%}
			var url = '{{ url_for("api.acl_group_members", backend=backend, name=group) }}';
			{% elif group == 'moderator' -%}
			var url = '{{ url_for("api.acl_moderator", backend=backend) }}';
			{% elif group == 'admin' -%}
			var url = '{{ url_for("api.acl_admin", backend=backend) }}';
			{% endif -%}
			var p = $http({
				url: url,
				method: 'PUT',
				data: {
					memberNames: added,
				},
				headers: {
					'X-From-UI': true,
				},
			})
			.then(function (response) {
				$scope.orig.groupMembers = vm.updateGroup.groupMembers;
				notifAll(response.data);
			})
			.catch(buiFail)
			.catch(function () {
				vm.updateGroup.groupMembers = $scope.orig.groupMembers;
			});
			promises.push(p);
		}
		$q.all(promises).finally(function() { enableSubmit(); });
	};
}]);
