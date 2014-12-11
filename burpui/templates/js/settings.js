
var app = angular.module('ConfigApp', ['ngSanitize', 'frapontillo.bootstrap-switch', 'ui.select', 'mgcrea.ngStrap', 'angular-onbeforeunload']);

app.config(function(uiSelectConfig) {
  uiSelectConfig.theme = 'bootstrap';
});

app.controller('MainCtrl', function($scope, $http) {
	$scope.bools = [];
	$scope.strings = [];
	$scope.defaults = {};
	$scope.placeholders = {};
	$scope.all = {};
	$scope.avail = {};
	$scope.suggest = {};
	$scope.old = {};
	$scope.new = {
			'bools': undefined,
			'integers': undefined,
			'strings': undefined,
			'multis': undefined
		};
	$scope.add = {
			'bools': false,
			'integers': false,
			'strings': false,
			'multis': false
		};
	$scope.changed = false;
	$http.get('{{ url_for("read_conf_srv", server=server) }}').
		success(function(data, status, headers, config) {
			$scope.bools = data.results.boolean;
			$scope.all.bools = data.boolean;
			$scope.strings = data.results.common;
			$scope.all.strings = data.string;
			$scope.integers = data.results.integer;
			$scope.all.integers = data.integer;
			$scope.multis = data.results.multi;
			$scope.all.multis = data.multi;
			$scope.server_doc = data.server_doc;
			$scope.suggest = data.suggest;
			$scope.placeholders = data.placeholders;
			$scope.defaults = data.defaults;
		});
	$scope.submit = function(e) {
		e.preventDefault();
		/* ugly hack to disable form submission when pressing the 'return' key
		 * on the select + replace switch by hidden fields so that the unchecked
		 * switch get submitted */
		sbm = true;
		_($scope.new).forEach(function(value, key) {
			/* XXX: I have no idea why this works... */
			if (value && value.selected) sbm = false;
		});
		if (!sbm) {
			return;
		}
		var form = $(e.target);
		if (form.attr('name') === 'setSettings') {
			angular.forEach($scope.bools, function(value, key) {
				form.find('#'+value.name).val(value.value);
				form.find('#'+value.name+'_view').attr('disabled', true);
			});
			submit = form.find('button[type="submit"]');
			sav = submit.text();
			submit.text('Saving...');
			submit.attr('disabled', true);
			$.ajax({
						url: form.attr('action'),
						type: form.attr('method'),
						data: form.serialize()
			}).fail(function(xhr, stat, err) {
				var msg = '<strong>ERROR:</strong> ';
				if (stat && err) {
					msg +=  '<p>'+stat+'</p><pre>'+err+'</pre>';
				} else if (stat) {
					msg += '<p>'+stat+'</p>';
				} else if (err) {
					msg += '<pre>'+err+'</pre>';
				}
				notif(2, msg, 10000);
			}).done(function(data) {
				if (data.notif) {
					$.each(data.notif, function(i, n) {
						notif(n[0], n[1]);
					});
				}
				$scope.setSettings.$setPristine();
				$scope.changed = false;
			}).always(function() {
				submit.text(sav);
				submit.attr('disabled', false);
			});
			angular.forEach($scope.bools, function(value, key) {
				form.find('#'+value.name+'_view').attr('disabled', false);
			});
		}
	};
	$scope.remove = function(key, index) {
		if (!$scope.old[key]) {
			$scope.old[key] = {};
		}
		$scope.old[key][$scope[key][index]['name']] = $scope[key][index]['value'];
		$scope[key].splice(index, 1);
		$scope.add[key] = false;
		$scope.new[key] = undefined;
		$scope.changed = true;
	};
	$scope.removeMulti = function(pindex, cindex) {
		$scope.multis[pindex].value.splice(cindex, 1);
		if ($scope.multis[pindex].value.length <= 0) {
			$scope.multis.splice(pindex, 1);
		}
		$scope.add.multis = false;
		$scope.new.multis = false;
		$scope.changed = true;
	};
	$scope.addMulti = function(pindex) {
		$scope.multis[pindex].value.push('');
		$scope.add.multis = false;
		$scope.new.multis = false;
		$scope.changed = true;
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
			if (!v && type == 'multis') {
				v = [''];
			}
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
		$scope.changed = true;
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

// Add a smooth scrolling to anchor
$(document).ready(function() {
	$('a[href^="#"]').click(function() {
		var target = $(this.hash);
		if (target.length == 0) target = $('a[name="' + this.hash.substr(1) + '"]');
		if (target.length == 0) target = $('html');
		$('html, body').animate({ scrollTop: target.offset().top }, 500);
		return false;
	});
});
