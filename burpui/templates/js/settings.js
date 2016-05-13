
/***
 * The Settings Panel is managed with AngularJS.
 * Following is the AngularJS Application and Controller.
 * Our $scope is initialized with a $http request that retrieves a JSON like that:
 * {
 * 	"boolean": [
 * 		"key",
 * 		...
 * 	],
 * 	"defaults": {
 * 		"key1": "default",
 * 		"key2": false,
 * 		"key3": [
 * 			4,
 * 			2,
 * 		],
 * 		...
 * 	},
 * 	"integer": [
 * 		"key",
 * 	],
 * 	"multi": [
 * 		"key",
 * 	],
 * 	"placeholders": {
 * 		"key": "placeholder",
 * 		...
 * 	},
 * 	"results": {
 * 		"boolean": [
 * 			{
 * 				"name": "key",
 * 				"value": true
 * 			},
 * 			...
 * 		],
 * 		"clients": [
 * 			{
 * 				"name": "clientname",
 * 				"value": "/etc/burp/clientconfdir/clientname"
 * 			},
 * 			...
 * 		],
 * 		"common": [
 * 			{
 * 				"name": "key",
 * 				"value": "val"
 * 			},
 * 			...
 * 		],
 * 		"integer": [
 * 			{
 * 				"name": "key",
 * 				"value": 42
 * 			},
 * 			...
 * 		],
 * 		"multi": [
 * 			{
 * 				"name": "key",
 * 				"value": [
 * 					"value1",
 * 					"value2",
 * 					...
 * 				]
 * 			},
 * 			...
 * 		],
 *    "includes": [
 *      "glob",
 *      "example*.conf",
 *      ...
 *    ],
 *    "includes_ext": [
 *      "glob",
 *      "example1.conf",
 *      "example_toto.conf",
 *      ...
 *    ]
 * 	},
 * 	"server_doc": {
 * 		"key": "documentations of the specified key from the manpage",
 * 		...
 * 	},
 * 	"string": [
 * 		"key",
 * 		...
 * 	],
 * 	"suggest": {
 * 		"key": [
 * 			"value1",
 * 			"value2",
 * 		],
 * 		[...]
 * 	}
 * }
 * The JSON is then split-ed out into several dict/arrays to build our form.
 */

var app = angular.module('MainApp', ['ngSanitize', 'frapontillo.bootstrap-switch', 'ui.select', 'mgcrea.ngStrap', 'angular-onbeforeunload']);

app.config(function(uiSelectConfig) {
	uiSelectConfig.theme = 'bootstrap';
});

app.controller('ConfigCtrl', function($scope, $http) {
	$scope.bools = [];
	$scope.strings = [];
	$scope.clients = [];
	$scope.client = {};
	$scope.defaults = {};
	$scope.placeholders = {};
	$scope.all = {};
	$scope.avail = {};
	$scope.suggest = {};
	$scope.invalid = {};
	$scope.paths = {};
	$scope.inc_invalid = {};
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
	{% if client -%}
	$http.get('{{ url_for("api.client_settings", client=client, conf=conf, server=server) }}')
	{% else -%}
	$http.get('{{ url_for("api.server_settings", conf=conf, server=server) }}')
	{% endif -%}
		.success(function(data, status, headers, config) {
			$scope.bools = data.results.boolean;
			$scope.all.bools = data.boolean;
			$scope.strings = data.results.common;
			$scope.all.strings = data.string;
			$scope.integers = data.results.integer;
			$scope.all.integers = data.integer;
			$scope.multis = data.results.multi;
			$scope.all.multis = data.multi;
			$scope.clients = data.results.clients;
			$scope.server_doc = data.server_doc;
			$scope.suggest = data.suggest;
			$scope.placeholders = data.placeholders;
			$scope.defaults = data.defaults;
			$scope.includes = data.results.includes;
			$scope.includes_ori = angular.copy($scope.includes);
			$scope.includes_ext = data.results.includes_ext;
			$('#waiting-container').hide();
			$('#settings-panel').show();
		});
	/* Our form is submitted asynchronously thanks to this callback */
	$scope.submit = function(e) {
		/* we disable the 'real' form submission */
		e.preventDefault();
		/* ugly hack to disable form submission when pressing the 'return' key
		 * on the select + replace switch by hidden fields so that the unchecked
		 * switch get submitted */
		sbm = true;
		_($scope.new).forEach(function(value, key) {
			/* Once we found a 'select' was active, we exit the loop as we just
			 * need one to disable form submission */
			if (value && value.selected) {
				sbm = false;
				return;
			}
		});
		/* The above forEach is a function, as we cannot exit two levels at once
		 * we need this check & return */
		if (!sbm) {
			return;
		}
		var form = $(e.target);
		if (form.attr('name') === 'setSettings') {
			/* We want to submit every displayed settings. By default unchecked
			 * checkboxes are not submitted so we use a hidden field to achieve that */
			angular.forEach($scope.bools, function(value, key) {
				form.find('#'+value.name).val(value.value);
				form.find('#'+value.name+'_view').attr('disabled', true);
			});
			$scope.invalid = {};
			/* UX tweak: disable the submit button + change text */
			submit = form.find('button[type="submit"]');
			sav = submit.text();
			submit.text('Saving...');
			submit.attr('disabled', true);
			/* submit the data */
			$.ajax({
				url: form.attr('action'),
				type: 'POST',
				data: form.serialize()
			})
			.fail(myFail)
			.done(function(data) {
				/* The server answered correctly but some errors may have occurred server
				 * side so we display them */
				if (data.notif) {
					$.each(data.notif, function(i, n) {
						notif(n[0], n[1]);
						$scope.invalid[n[2]] = true;
					});
				}
				$scope.setSettings.$setPristine();
				$scope.changed = false;
				$scope.getClientsList();
			}).always(function() {
				/* reset the submit button state */
				submit.text(sav);
				submit.attr('disabled', false);
			});
			/* re-enable the checkboxes */
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
	$scope.undoAdd = function(type) {
		$scope.add[type] = false;
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
	$scope.removeIncludes = function(index) {
		if (!$scope.old.includes) {
			$scope.old.includes = [];
		}
		if (!$scope.old.includes_ori) {
			$scope.old.includes_ori = [];
		}
		$scope.old.includes.push($scope.includes[index]);
		$scope.old.includes_ori.push($scope.includes_ori[index]);
		$scope.includes.splice(index, 1);
		$scope.includes_ori.splice(index, 1);
	};
	$scope.clickAddIncludes = function() {
		val = '';
		val2 = false;
		if ($scope.old.includes) {
			val = $scope.old.includes.pop();
		}
		if ($scope.old.includes_ori) {
			val2 = $scope.old.includes_ori.pop();
		}
		$scope.includes.push(val);
		$scope.includes_ori.push(val2);
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
	/* A client has been selected, we redirect to the client config page */
	$scope.selectClient = function(selected, select) {
		select.search = undefined;
		document.location = '{{ url_for("view.cli_settings", server=server) }}?client='+selected.name;
	};
	/* A config file has been selected for edition, we redirect the client */
	$scope.editInclude = function(parent, index) {
		file = $scope.paths[parent][index];
		{% if client -%}
		document.location = '{{ url_for("view.cli_settings", client=client, server=server) }}?conf='+file;
		{% else -%}
		document.location = '{{ url_for("view.settings", server=server) }}?conf='+file;
		{% endif -%}
	};
	$scope.expandPath = function(index) {
		path = $scope.includes[index];
		{% if client -%}
		api = '{{ url_for("api.path_expander", client=client, server=server) }}';
		{% else -%}
		api = '{{ url_for("api.path_expander", server=server) }}';
		{% endif -%}
		$scope.inc_invalid = {};
		$.ajax({
			url: api,
			type: 'GET',
			data: {'path': path}
		})
		.fail(myFail)
		.done(function(data) {
			/* The server answered correctly but some errors may have occurred server
			 * side so we display them */
			if (data.notif) {
				notif(data.notif[0], data.notif[1])
				$scope.inc_invalid[index] = true;
			} else if (data.result) {
				$scope.paths[index] = [];
				$.each(data.result, function(i, p) {
					$scope.paths[index].push(p);
				});
			}
		});
	};
	$scope.getClientsList = function() {
		api = '{{ url_for("api.clients_list", server=server) }}';
		$.ajax({
			url: api,
			type: 'GET'
		}).done(function(data) {
			$scope.clients = data.result;
		});
	};
	$scope.deleteClient = function() {
		api = '{{ url_for("api.client_settings", client=client, server=server) }}';
		$.ajax({
			url: api,
			type: 'DELETE'
		})
		.fail(myFail)
		.done(function(data) {
			/* The server answered correctly but some errors may have occurred server
			 * side so we display them */
			if (data.notif) {
				notif(data.notif[0], data.notif[1]);
				if (data.notif[0] == 0) {
					document.location = '{{ url_for("view.settings", server=server) }}';
				}
			}
		});
	};
	$scope.createClient = function(e) {
		/* we disable the 'real' form submission */
		e.preventDefault();
		var form = $(e.target);
		$.ajax({
			url: form.attr('action'),
			type: 'PUT',
			data: form.serialize()
		})
		.fail(myFail)
		.done(function(data) {
			/* The server answered correctly but some errors may have occurred server
			 * side so we display them */
			if (data.notif) {
				notif(data.notif[0][0], data.notif[0][1]);
				if (data.notif[0][0] == 0) {
					$scope.getClientsList();
					notif(data.notif[1][0], data.notif[1][1], 20000);
				}
			}
		});
	};
	/* These callbacks expand/reduce the input for a better readability */
	$scope.focusIn = function(ev) {
		el = $( ev.target ).parent();
		/* Hide the button */
		el.next('div').hide();
		/* Hide the legend */
		el.next('div').next('div').hide();
		/* Expand the input */
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
