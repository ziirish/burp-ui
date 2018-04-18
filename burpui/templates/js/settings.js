
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
{% import 'macros.html' as macros %}

var app = angular.module('MainApp', ['ngSanitize', 'frapontillo.bootstrap-switch', 'ui.select', 'mgcrea.ngStrap', 'angular-onbeforeunload', 'datatables', 'hljs']);

app.config(function(uiSelectConfig) {
	uiSelectConfig.theme = 'bootstrap';
});

app.directive('highlight', function($interpolate, $window) {
	return {
		restrict: 'EA',
		scope: true,
		compile: function(tElem, tAttrs) {
			var interpolateFn = $interpolate(tElem.html(), true);
			tElem.html('');

			return function(scope, elem, attrs) {
				scope.$watch(interpolateFn, function(value) {
					elem.html(hljs.highlight('INI', value).value);
				});
			}
		}
	};
});

app.controller('ConfigCtrl', ['$scope', '$http', '$timeout', '$scrollspy', 'DTOptionsBuilder', 'DTColumnDefBuilder', function($scope, $http, $timeout, $scrollspy, DTOptionsBuilder, DTColumnDefBuilder) {
	$scope.bools = [];
	$scope.strings = [];
	$scope.integers = [];
	$scope.multis = [];
	$scope.pairs = [];
	$scope.clients = [];
	$scope.hierarchy = [];
	$scope.client = {};
	$scope.defaults = {};
	$scope.placeholders = {};
	$scope.all = {};
	$scope.avail = {};
	$scope.suggest = {};
	$scope.invalid = {};
	$scope.paths = {};
	$scope.revokeEnabled = false;
	$scope.inc_invalid = {};
	$scope.includes_ori = [];
	$scope.old = {};
	$scope.raw = {};
	$scope.spy = {};
	$scope.raw_content = '';
	$scope.new = {
			'bools': undefined,
			'integers': undefined,
			'strings': undefined,
			'multis': undefined,
			'templates': undefined,
			'pairs': undefined,
		};
	$scope.add = {
			'bools': false,
			'integers': false,
			'strings': false,
			'multis': false,
			'templates': false,
			'pairs': false
		};
	$scope.advanced = {};
	$scope.changed = false;
	$scope.checkbox_translation = {
			'yes':   "{{ _('yes') }}",
			'no':    "{{ _('no') }}",
			'reset': "{{ _('reset list') }}",
		};
	$scope.dtOptions = {
			{{ macros.translate_datatable() }}
			{{ macros.get_page_length() }}
			fixedHeader: true,
		};
	$scope.dtColumnDefs = [
			DTColumnDefBuilder.newColumnDef(0),
			DTColumnDefBuilder.newColumnDef(1),
			DTColumnDefBuilder.newColumnDef(2).notSortable(),
		];
	$scope.loadConfig = function() {
		{% if is_moderator and not is_admin -%}
		// We don't have rights to load this part, just return
		return;
		{% endif -%}
		{% if client -%}
			{% if template -%}
		$http.get('{{ url_for("api.client_settings", client=client, conf=conf, template=True, server=server) }}', { headers: { 'X-From-UI': true } })
			{% else -%}
		$http.get('{{ url_for("api.client_settings", client=client, conf=conf, server=server) }}', { headers: { 'X-From-UI': true } })
			{% endif -%}
		{% else -%}
		$http.get('{{ url_for("api.server_settings", conf=conf, server=server) }}', { headers: { 'X-From-UI': true } })
		{% endif -%}
			.then(function(response) {
				data = response.data;
				$scope.bools = data.results.boolean;
				$scope.all.bools = data.boolean;
				$scope.strings = data.results.common;
				$scope.all.strings = data.string;
				$scope.integers = data.results.integer;
				$scope.all.integers = data.integer;
				$scope.multis = data.results.multi;
				$scope.all.multis = data.multi;
				$scope.pairs = data.results.pair;
				$scope.all.pairs = _.keys(data.pair);
				$scope.pair_associations = data.pair;
				$scope.server_doc = data.server_doc;
				$scope.suggest = data.suggest;
				$scope.placeholders = data.placeholders;
				$scope.defaults = data.defaults;
				$scope.includes = data.results.includes;
				$scope.includes_ori = angular.copy(data.results.includes, $scope.includes_ori);
				$scope.includes_ext = data.results.includes_ext;
				$scope.templates = data.results.templates;
				$scope.hierarchy = data.results.hierarchy;
				$scope.raw_content = data.results.raw;
				$scope.advanced = data.advanced;
				$scope.refreshHierarchy();
				$scope.refreshScrollspy();
				$('#waiting-container').hide();
				$('#settings-panel').show();
			}, function(response) {
				notifAll(response.data);
				$('#waiting-container').hide();
			});
	};
	$http.get('{{ url_for("api.setting_options", server=server) }}', { headers: { 'X-From-UI': true } })
		.then(function(response) {
			$scope.revokeEnabled = response.data.is_revocation_enabled;
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
			angular.forEach($scope.multis, function(value, key) {
				angular.forEach(value.reset, function(val, i) {
					form.find('#'+value.name+'_reset_bui_CUSTOM-'+i).val(val);
					form.find('#'+value.name+'_reset_bui_CUSTOM_view-'+i).attr('disabled', true);
				});
			});
			$scope.invalid = {};
			/* UX tweak: disable the submit button + change text */
			submit = form.find('button[type="submit"]');
			sav = submit.html();
			submit.html('<i class="fa fa-fw fa-spinner fa-pulse" aria-hidden="true"></i>&nbsp;{{ _("Saving...") }}');
			submit.attr('disabled', true);
			/* submit the data */
			$.ajax({
				url: form.attr('action'),
				type: 'POST',
				data: form.serialize(),
				headers: { 'X-From-UI': true },
			})
			.fail(buiFail)
			.done(function(data) {
				/* The server answered correctly but some errors may have occurred server
				 * side so we display them */
				errors = false;
				if (data.notif) {
					$.each(data.notif, function(i, n) {
						if (n[0] !== NOTIF_SUCCESS) {
							errors = true;
						}
						notif(n[0], n[1]);
						$scope.invalid[n[2]] = true;
					});
				}
				/* if some errors occurred, don't refresh the form data */
				if (!errors) {
					$scope.setSettings.$setPristine();
					$scope.changed = false;
					$scope.getClientsList();
					$scope.loadConfig();
				}
			})
			.always(function() {
				/* reset the submit button state */
				submit.html(sav);
				submit.attr('disabled', false);
			});
			/* re-enable the checkboxes */
			angular.forEach($scope.bools, function(value, key) {
				form.find('#'+value.name+'_view').attr('disabled', false);
			});
			angular.forEach($scope.multis, function(value, key) {
				angular.forEach(value.reset, function(val, i) {
					form.find('#'+value.name+'_reset_bui_CUSTOM_view-'+i).attr('disabled', false);
				});
			});
		}
	};
	$scope.refreshHierarchy = function() {
		if ($scope.hierarchy) {
			$('#tree-hierarchy').fancytree({
				extensions: ["glyph", "table"],
				glyph: {
					preset: "bootstrap3",
					map: {
						doc: "glyphicon-file",
						docOpen: "glyphicon-file",
						checkbox: "glyphicon-unchecked",
						checkboxSelected: "glyphicon-check",
						checkboxUnknown: "glyphicon-share",
						dragHelper: "glyphicon-play",
						dropMarker: "glyphicon-arrow-right",
						error: "glyphicon-warning-sign",
						expanderClosed: "glyphicon-plus-sign",
						expanderLazy: "glyphicon-plus-sign",
						// expanderLazy: "glyphicon-expand",
						expanderOpen: "glyphicon-minus-sign",
						// expanderOpen: "glyphicon-collapse-down",
						folder: "glyphicon-folder-close",
						folderOpen: "glyphicon-folder-open",
						loading: "glyphicon-refresh fancytree-helper-spin"
					}
				},
				source: $scope.hierarchy,
				init: function() {
					$('#tree-hierarchy').floatThead({
						position: 'auto',
						autoReflow: true,
						top: $('.navbar').height(),
					});
				},
				scrollParent: $(window),
				renderColumns: function(event, data) {
					var node = data.node;
					$tdList = $(node.tr).find(">td");

					{% if client -%}
					var URL = '{{ url_for("view.cli_settings", client=client, server=server) }}?conf='+encodeURIComponent(node.data.full);
					{% else -%}
					var URL = '{{ url_for("view.settings", server=server) }}?conf='+encodeURIComponent(node.data.full);
					{% endif -%}

					$tdList.eq(1).html('<a href="'+URL+'" class="btn btn-info btn-xs no-link pull-right" title="{{ _('edit') }}"><i class="fa fa-pencil" aria-hidden="true"></i></a>');
				},
			});
			var tree = $('#tree-hierarchy').fancytree('getTree');

			tree.getRootNode().visit(function(node) {
				node.setExpanded(true);
			});
		}
	};
	$scope.refreshScrollspy = function() {
		angular.forEach($('.bui-scrollspy > li'), function(e) {
			var ae = angular.element(e);
			var target = e.dataset.target;
			var options = {
				scope: $scope,
				target: target
			};
			if (target in $scope.spy) {
				var oldSpy = $scope.spy[target];
				oldSpy.untrackElement(options.target, ae);
		    oldSpy.destroy();
			}
			var scrollspy = $scrollspy(options);
			scrollspy.trackElement(options.target, ae);
			$scope.spy[target] = scrollspy;
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
		$scope.changed = true;
	};
	$scope.clickAdd = function(type) {
		if ($scope.new[type]) {
			$scope.new[type] = undefined;
		}
		$scope.add[type] = true;
		all = $scope.all[type];
		if (type === 'templates') {
			all = [];
			_($scope.all[type]).forEach(function(value, name) {
				all.push(name);
			});
		}
		keys = _.map($scope[type], 'name');
		if (type === 'pairs') {
			iter = angular.copy(keys);
			_(iter).forEach(function(key) {
				var assoc = $scope.pair_associations[key];
				if (_.findIndex(keys, key) == -1) {
					keys.push(assoc);
				}
			});
		}
		diff = _.difference(all, keys);
		$scope.avail[type] = [];
		_(diff).forEach(function(n) {
			var data = {'name': n};
			var v = $scope.defaults[n];
			if (!v && type === 'multis') {
				v = [''];
				data['reset'] = [false];
			}
			if (!v && type === 'templates') {
				v = $scope.all[type][n];
			}
			data['value'] = v;
			$scope.avail[type].push(data);
		});
	};
	$scope.undoAdd = function(type) {
		$scope.add[type] = false;
	};
	$scope.removeMulti = function(pindex, cindex) {
		$scope.multis[pindex].value.splice(cindex, 1);
		$scope.multis[pindex].reset.splice(cindex, 1);
		if ($scope.multis[pindex].value.length <= 0) {
			$scope.multis.splice(pindex, 1);
		}
		$scope.add.multis = false;
		$scope.new.multis = false;
		$scope.changed = true;
		$scope.refreshScrollspy();
	};
	$scope.addMulti = function(pindex) {
		$scope.multis[pindex].value.push('');
		$scope.multis[pindex].reset.push(false);
		$scope.add.multis = false;
		$scope.new.multis = false;
		$scope.changed = true;
		$scope.refreshScrollspy();
	};
	$scope.removePairElement = function(pindex, pkey, cindex) {
		$scope.pairs[pindex].value[pkey].splice(cindex, 1);
		if ($scope.pairs[pindex].value[pkey].length <= 0 && $scope.pairs[pindex].value[$scope.pair_associations[pkey]].length <= 0) {
			$scope.pairs.splice(pindex, 1);
		}
		$scope.add.pairs = false;
		$scope.new.pairs = false;
		$scope.changed = true;
		$scope.refreshScrollspy();
	};
	$scope.addPairElement = function(pindex, pkey) {
		if (!$scope.pairs[pindex].value[pkey]) {
		  $scope.pairs[pindex].value[pkey] = [];
		}
		$scope.pairs[pindex].value[pkey].push('');
		$scope.add.pairs = false;
		$scope.new.pairs = false;
		$scope.changed = true;
		$scope.refreshScrollspy();
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
		$scope.changed = true;
		$scope.refreshScrollspy();
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
		$scope.changed = true;
		$scope.refreshScrollspy();
	};
	$scope.select = function(selected, select, type) {
		select.search = undefined;
		if ($scope.old[type] && $scope.old[type][selected.name]) {
			selected.value = $scope.old[type][selected.name];
		} else if (type === 'pairs') {
			selected.value = {};
			selected.value[selected.name] = [''];
			selected.value[$scope.pair_associations[selected.name]] = [];
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
		api = '{{ url_for("api.path_expander", client=client, server=server, source=conf) }}';
		{% else -%}
		api = '{{ url_for("api.path_expander", server=server, source=conf) }}';
		{% endif -%}
		$scope.inc_invalid = {};
		$http.get(
			api,
			{
				headers: { 'X-From-UI': true },
				params: { 'path': path },
			}
		).then(
			function(response) {
				data = response.data;
				/* The server answered correctly but some errors may have occurred server
				 * side so we display them */
				if (data.notif) {
					notifAll(data.notif)
					$scope.inc_invalid[index] = true;
				} else if (data.result) {
					$scope.paths[index] = [];
					$.each(data.result, function(i, p) {
						$scope.paths[index].push(p);
					});
				}
			},
			function(response) {
				errorsHandler(response.data);
			}
		);
	};
	$scope.getClientsList = function() {
		api = '{{ url_for("api.clients_list", server=server) }}';
		$http.get(
			api,
			{
				headers: { 'X-From-UI': true },
			}
		).then(
			function(response) {
				var data = response.data;
				$scope.clients = data.result;
			}
		);
	};
	$scope.getTemplatesList = function() {
		api = '{{ url_for("api.templates_list", server=server) }}';
		$http.get(
			api,
			{
				headers: { 'X-From-UI': true },
			}
		).then(
			function(response) {
				var data = response.data;
				$scope.raw.templates = data.result;
				$scope.all.templates = {};
				_(data.result).forEach(function(r) {
					$scope.all.templates[r.name] = r.value;
				});
			}
		);
	};
	$scope.deleteFile = function() {
		/* UX tweak: disable the submit button + change text */
		submit = $('#btn-remove-file');
		sav = submit.html();
		submit.html('<i class="fa fa-fw fa-spinner fa-pulse" aria-hidden="true"></i>&nbsp;{{ _("Deleting...") }}');
		submit.attr('disabled', true);
		api = '{{ url_for("api.server_settings", server=server, conf=conf) }}';
		$.ajax({
			url: api,
			type: 'DELETE'
		})
		.fail(buiFail)
		.done(function(data) {
			redirect = data[0][0] == NOTIF_SUCCESS;
			notifAll(data, redirect);
			if (redirect) {
				$timeout(function() {
					document.location = '{{ url_for("view.settings", server=server) }}';
				}, 1000);
			}
		})
		.always(function() {
			/* reset the submit button state */
			submit.html(sav);
			submit.attr('disabled', false);
		});
	};
	$scope.deleteClient = function() {
		/* UX tweak: disable the submit button + change text */
		submit = $('#btn-remove-client');
		sav = submit.html();
		submit.html('<i class="fa fa-fw fa-spinner fa-pulse" aria-hidden="true"></i>&nbsp;{{ _("Deleting...") }}');
		submit.attr('disabled', true);
		api = '{{ url_for("api.client_settings", client=client, server=server) }}';
		$.ajax({
			url: api,
			type: 'DELETE',
			{% if template -%}
			data: { template: true }
			{% else -%}
			data: { delcert: $('#delcert').is(':checked'), revoke: $('#revoke').is(':checked'), keepconf: $('#keepconf').is(':checked') }
			{% endif -%}
		})
		.fail(buiFail)
		.done(function(data) {
			redirect = data[0][0] == NOTIF_SUCCESS;
			notifAll(data, redirect);
			if (redirect) {
				$timeout(function() {
					document.location = '{{ url_for("view.settings", server=server) }}';
				}, 1000);
			}
		})
		.always(function() {
			/* reset the submit button state */
			submit.html(sav);
			submit.attr('disabled', false);
		});
	};
	$scope.createClient = function(e) {
		/* we disable the 'real' form submission */
		e.preventDefault();
		var form = $(e.target);
		submit = form.find('button[type="submit"]');
		sav = submit.html();
		submit.html('<i class="fa fa-fw fa-spinner fa-pulse" aria-hidden="true"></i>&nbsp;{{ _("Creating...") }}');
		submit.attr('disabled', true);
		$.ajax({
			url: form.attr('action'),
			type: 'PUT',
			data: form.serialize()
		})
		.fail(buiFail)
		.done(function(data) {
			/* The server answered correctly but some errors may have occurred server
			 * side so we display them */
			if (data.notif) {
				notif(data.notif[0][0], data.notif[0][1]);
				if (data.notif[0][0] == NOTIF_SUCCESS) {
					$scope.getClientsList();
					notif(data.notif[1][0], data.notif[1][1], 20000);
				}
			}
		})
		.always(function() {
			submit.attr('disabled', false);
			submit.html(sav);
		});
	};
	$scope.createTemplate = function(e) {
		/* we disable the 'real' form submission */
		e.preventDefault();
		var form = $(e.target);
		submit = form.find('button[type="submit"]');
		sav = submit.html();
		submit.html('<i class="fa fa-fw fa-spinner fa-pulse" aria-hidden="true"></i>&nbsp;{{ _("Creating...") }}');
		submit.attr('disabled', true);
		$.ajax({
			url: form.attr('action'),
			type: 'PUT',
			data: form.serialize()
		})
		.fail(buiFail)
		.done(function(data) {
			/* The server answered correctly but some errors may have occurred server
			 * side so we display them */
			if (data.notif) {
				notif(data.notif[0][0], data.notif[0][1]);
				if (data.notif[0][0] == NOTIF_SUCCESS) {
					$scope.getTemplatesList();
					notif(data.notif[1][0], data.notif[1][1], 20000);
				}
			}
		})
		.always(function() {
			submit.attr('disabled', false);
			submit.html(sav);
		});
	};
	$scope.isNumber = function(key) {
		return $scope.advanced && $scope.advanced[key] === 'integer';
	};
	/* These callbacks expand/reduce the input for a better readability */
	$scope.focusIn = function(ev) {
		el = $( ev.target ).parent();
		/* Hide the button */
		el.next('div').hide();
		/* Hide the legend */
		el.next('div').next('div').hide();
		/* Hide the reset button */
		el.next('div').next('div').next('div').hide();
		/* Expand the input */
		el.removeClass('col-lg-2').addClass('col-lg-9');
	};
	$scope.focusOut = function(ev) {
		el = $( ev.target ).parent();
		el.next('div').show();
		el.next('div').next('div').show();
		el.next('div').next('div').next('div').show();
		el.removeClass('col-lg-9').addClass('col-lg-2');
	};
	$scope.loadConfig();
	$scope.getClientsList();
	$scope.getTemplatesList();
}]);

{{ macros.page_length('#table-list-clients') }}
{{ macros.page_length('#table-list-templates') }}

$(document).ready(function () {
	$('#config-nav a').click(function (e) {
		e.preventDefault();
		$(this).tab('show');
	});
});
