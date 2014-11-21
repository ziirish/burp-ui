
var app = angular.module('ConfigApp', ['ngSanitize', 'frapontillo.bootstrap-switch', 'ui.select', 'mgcrea.ngStrap']);

app.config(function(uiSelectConfig) {
  uiSelectConfig.theme = 'bootstrap';
});

app.controller('MainCtrl', function($scope, $http) {
	$scope.bools = [];
	$scope.strings = [];
	$scope.defaults = {};
	$scope.all = {};
	$scope.avail = {};
	$scope.suggest = {};
	$scope.old = {};
	$scope.new = {
			'bools': undefined,
			'integers': undefined,
			'strings': undefined
		};
	$scope.add = {
			'bools': false,
			'integers': false,
			'strings': false
		};
	$http.get('{{ url_for("read_conf_srv", server=server) }}').
		success(function(data, status, headers, config) {
			$scope.bools = data.results.boolean;
			$scope.all.bools = data.boolean;
			$scope.strings = data.results.common;
			$scope.all.strings = data.string;
			$scope.server_doc = data.server_doc;
			$scope.suggest = data.suggest;
			$scope.defaults = data.defaults;
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
			return;
		}
		angular.forEach($scope.bools, function(value, key) {
			$('#'+value.name).val(value.value);
			$('#'+value.name+'_view').attr('disabled', true);
		});
	};
	$scope.remove = function(key, index) {
		if (!$scope.old[key]) {
			$scope.old[key] = {};
		}
		$scope.old[key][$scope[key][index]['name']] = $scope[key][index]['value'];
		$scope[key].splice(index, 1);
		$scope.add[key] = false;
		$scope.new[key] = undefined;
	};
	$scope.clickAdd = function(type) {
		if ($scope.new[type]) {
			$scope.new[type] = undefined;
		}
		$scope.add[type] = true;
		keys = _.pluck($scope[type], 'name');
		diff = _.difference($scope.all[type], keys);
		$scope.avail[type] = [];
		_(diff).forEach(function(n) {
			v = $scope.defaults[n];
			$scope.avail[type].push({'name': n, 'value': v});
		});
	};
	$scope.select = function(selected, select, type) {
		select.search = undefined;
		if ($scope.old[type] && $scope.old[type][selected.name]) {
			selected.value = $scope.old[type][selected.name];
		}
		$scope[type].push(selected);
		$scope.add[type] = false;
	};
	$scope.undoAdd = function(type) {
		$scope.add[type] = false;
	};
	$scope.focusIn = function(ev) {
		el = $( ev.target ).parent();
		el.next('div').hide();
		el.next('div').next('div').hide();
		el.removeClass('col-lg-2').addClass('col-lg-9');
	};
	$scope.focusOut = function(ev) {
		el = $( ev.target ).parent();
		el.next('div').show();
		el.next('div').next('div').show();
		el.removeClass('col-lg-9').addClass('col-lg-2');
	};
});
