
var app = angular.module('ConfigApp', ['ngSanitize', 'frapontillo.bootstrap-switch', 'ui.select']);

app.config(function(uiSelectConfig) {
  uiSelectConfig.theme = 'bootstrap';
});

app.controller('MainCtrl', function($scope, $http) {
	$scope.bools = [];
	$scope.all = {};
	$scope.avail = {};
	$scope.new = {
			'bool': undefined,
			'int': undefined
		};
	$scope.add = {
			'bool': false,
			'int': false
		};
	$http.get('{{ url_for("read_conf_srv", server=server) }}').
		success(function(data, status, headers, config) {
			$scope.bools = data.results.boolean;
			$scope.all.bools = data.boolean;
			$scope.server_doc = data.server_doc;
		});
	$scope.submit = function(e) {
		/* ugly hack to disable form submission when pressing the 'return' key
		 * on the select + replace switch by hidden fields so that the unchecked
		 * switch get submitted */
		sbm = true;
		_($scope.new).forEach(function(value, key) {
			/* XXX: I have no idea why this works... */
			if (value && value.selected) sbm = false;
		});
		if (!sbm) {
			e.preventDefault();
		}
		angular.forEach($scope.bools, function(value, key) {
			$('#'+value.name).val(value.value);
			$('#'+value.name+'_view').attr('disabled', true);
		});
	};
	$scope.removeBool = function(index) {
		$scope.bools.splice(index, 1);
		$scope.add.bool = false;
		$scope.new.bool = undefined;
	};
	$scope.clickAddBool = function() {
		if ($scope.new.bool) {
			$scope.new.bool = undefined;
		}
		$scope.add.bool = true;
		keys = _.pluck($scope.bools, 'name');
		diff = _.difference($scope.all.bools, keys);
		$scope.avail.bools = [];
		_(diff).forEach(function(n) {
			$scope.avail.bools.push({'name': n, 'value': false});
		});
	};
	$scope.selectBool = function(selected, select) {
		select.search = undefined;
		$scope.bools.push(selected);
		$scope.add.bool = false;
	};
  $scope.undoAddBool = function() {
		$scope.add.bool = false;
	};
});

$(function() {
	$('body').scrollspy({ target: '#navbar-config' });
});

