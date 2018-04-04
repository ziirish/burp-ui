var _admin = function() {
	// do nothing
	return true;
};

$('form[name=changePassword]').on('submit', function(e) {
	e.preventDefault();
	var form = $(e.target);
	submit = form.find('button[type="submit"]');
	sav = submit.html();
	submit.html('<i class="fa fa-fw fa-spinner fa-pulse" aria-hidden="true"></i>&nbsp;{{ _("Saving...") }}');
	submit.attr('disabled', true);
	/* submit the data */
	$.ajax({
		url: form.attr('action'),
		type: 'POST',
		data: {
			'password': $('input[name=password]').val(),
			'backend': "{{ backend }}"
		},
		headers: { 'X-From-UI': true },
	})
	.fail(myFail)
	.done(function(data) {
		notifAll(data);
	})
	.always(function() {
		/* reset the submit button state */
		submit.html(sav);
		submit.attr('disabled', false);
	});
});

/* placeholder */
var app = angular.module('MainApp', ['ngSanitize', 'ui.select', 'mgcrea.ngStrap', 'datatables']);

app.config(function(uiSelectConfig) {
	uiSelectConfig.theme = 'bootstrap';
});

app.directive('uiAce', function () {

	if (angular.isUndefined(window.ace)) {
		throw new Error('ui-ace need ace to work... (o rly?)');
	}

	/**
	 * Sets editor options such as the wrapping mode or the syntax checker.
	 *
	 * The supported options are:
	 *
	 *   <ul>
	 *     <li>showGutter</li>
	 *     <li>useWrapMode</li>
	 *     <li>onLoad</li>
	 *     <li>theme</li>
	 *     <li>mode</li>
	 *   </ul>
	 *
	 * @param acee
	 * @param session ACE editor session
	 * @param {object} opts Options to be set
	 */
	var setOptions = function(scope, acee, session, opts) {

		// sets the ace worker path, if running from concatenated
		// or minified source
		if (angular.isDefined(opts.aceWorkerPath)) {
			var config = window.ace.require('ace/config');
			config.set('workerPath', opts.aceWorkerPath);
		}
		// ace requires loading
		if (angular.isDefined(opts.aceRequire)) {
			opts.aceRequire.forEach(function (n) {
					window.ace.require(n);
			});
		}
		// Boolean options
		if (angular.isDefined(opts.aceShowGutter)) {
			acee.renderer.setShowGutter(opts.aceShowGutter);
		}
		if (angular.isDefined(opts.aceUseWrapMode)) {
			session.setUseWrapMode(opts.aceUseWrapMode);
		}
		if (angular.isDefined(opts.aceShowInvisibles)) {
			acee.renderer.setShowInvisibles(opts.aceShowInvisibles);
		}
		if (angular.isDefined(opts.aceShowIndentGuides)) {
			acee.renderer.setDisplayIndentGuides(opts.aceShowIndentGuides);
		}
		if (angular.isDefined(opts.aceUseSoftTabs)) {
			session.setUseSoftTabs(opts.aceUseSoftTabs);
		}
		if (angular.isDefined(opts.aceShowPrintMargin)) {
			acee.setShowPrintMargin(opts.aceShowPrintMargin);
		}
		if (angular.isDefined(opts.readOnly)) {
			acee.setReadOnly(scope.$eval(opts.readOnly) === true);
		}

		// commands
		if (angular.isDefined(opts.aceDisableSearch) && opts.aceDisableSearch) {
			acee.commands.addCommands([
				{
					name: 'unfind',
					bindKey: {
						win: 'Ctrl-F',
						mac: 'Command-F'
					},
					exec: function () {
						return false;
					},
					readOnly: true
				}
			]);
		}

		// Basic options
		if (angular.isString(opts.aceTheme)) {
			acee.setTheme('ace/theme/' + opts.aceTheme);
		}
		if (angular.isString(opts.aceMode)) {
			session.setMode('ace/mode/' + opts.aceMode);
		}
		// Advanced options
		if (angular.isDefined(opts.aceFirstLineNumber)) {
			if (angular.isNumber(opts.aceFirstLineNumber)) {
				session.setOption('firstLineNumber', opts.aceFirstLineNumber);
			} else if (angular.isFunction(opts.aceFirstLineNumber)) {
				session.setOption('firstLineNumber', opts.aceFirstLineNumber());
			}
		}

		// advanced options
		var key, obj;
		if (angular.isDefined(opts.aceAdvanced)) {
				for (key in opts.aceAdvanced) {
						// create a javascript object with the key and value
						obj = { name: key, value: opts.aceAdvanced[key] };
						// try to assign the option to the ace editor
						acee.setOption(obj.name, obj.value);
				}
		}

		// advanced options for the renderer
		if (angular.isDefined(opts.aceRendererOptions)) {
				for (key in opts.aceRendererOptions) {
						// create a javascript object with the key and value
						obj = { name: key, value: opts.aceRendererOptions[key] };
						// try to assign the option to the ace editor
						acee.renderer.setOption(obj.name, obj.value);
				}
		}

		// onLoad callbacks
		angular.forEach(opts.callbacks, function (cb) {
			if (angular.isFunction(cb)) {
				cb(acee);
			}
		});
	};

	return {
		restrict: 'EA',
		require: '?ngModel',
		link: function (scope, elm, attrs, ngModel) {

			/**
			 * uiAceConfig merged with user options via json in attribute or data binding
			 * @type object
			 */
			var opts = attrs;

			/**
			 * ACE editor
			 * @type object
			 */
			var acee = window.ace.edit(elm[0]);

			/**
			 * ACE editor session.
			 * @type object
			 * @see [EditSession]{@link http://ace.c9.io/#nav=api&api=edit_session}
			 */
			var session = acee.getSession();

			/**
			 * Reference to a change listener created by the listener factory.
			 * @function
			 * @see listenerFactory.onChange
			 */
			var onChangeListener;

			/**
			 * Reference to a blur listener created by the listener factory.
			 * @function
			 * @see listenerFactory.onBlur
			 */
			var onBlurListener;

			/**
			 * Calls a callback by checking its existing. The argument list
			 * is variable and thus this function is relying on the arguments
			 * object.
			 * @throws {Error} If the callback isn't a function
			 */
			var executeUserCallback = function () {

				/**
				 * The callback function grabbed from the array-like arguments
				 * object. The first argument should always be the callback.
				 *
				 * @see [arguments]{@link https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions_and_function_scope/arguments}
				 * @type {*}
				 */
				var callback = arguments[0];

				/**
				 * Arguments to be passed to the callback. These are taken
				 * from the array-like arguments object. The first argument
				 * is stripped because that should be the callback function.
				 *
				 * @see [arguments]{@link https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Functions_and_function_scope/arguments}
				 * @type {Array}
				 */
				var args = Array.prototype.slice.call(arguments, 1);

				if (angular.isDefined(callback)) {
					scope.$evalAsync(function () {
						if (angular.isFunction(callback)) {
							callback(args);
						} else {
							throw new Error('ui-ace use a function as callback.');
						}
					});
				}
			};

			/**
			 * Listener factory. Until now only change listeners can be created.
			 * @type object
			 */
			var listenerFactory = {
				/**
				 * Creates a change listener which propagates the change event
				 * and the editor session to the callback from the user option
				 * onChange. It might be exchanged during runtime, if this
				 * happens the old listener will be unbound.
				 *
				 * @param callback callback function defined in the user options
				 * @see onChangeListener
				 */
				onChange: function (callback) {
					return function (e) {
						var newValue = session.getValue();

						if (ngModel && newValue !== ngModel.$viewValue &&
								// HACK make sure to only trigger the apply outside of the
								// digest loop 'cause ACE is actually using this callback
								// for any text transformation !
								!scope.$$phase && !scope.$root.$$phase) {
							scope.$evalAsync(function () {
								ngModel.$setViewValue(newValue);
							});
						}

						executeUserCallback(callback, e, acee);
					};
				},
				/**
				 * Creates a blur listener which propagates the editor session
				 * to the callback from the user option onBlur. It might be
				 * exchanged during runtime, if this happens the old listener
				 * will be unbound.
				 *
				 * @param callback callback function defined in the user options
				 * @see onBlurListener
				 */
				onBlur: function (callback) {
					return function () {
						executeUserCallback(callback, acee);
					};
				}
			};

			session.on('changeMode', function() {
				session.$worker.on('annotate', function(errors) {
					scope.validGrantInput = errors.data.length <= 0;
					scope.$apply();
				});
			});

			// Value Blind
			if (ngModel) {
				ngModel.$formatters.push(function (value) {
					if (angular.isUndefined(value) || value === null) {
						return '';
					}
					else if (angular.isObject(value) || angular.isArray(value)) {
						throw new Error('ui-ace cannot use an object or an array as a model');
					}
					return value;
				});

				ngModel.$render = function () {
					session.setValue(ngModel.$viewValue);
				};
			}

			// Listen for option updates
			var updateOptions = function (current, previous) {
				if (current === previous) return;
				opts = attrs;

				// EVENTS

				// unbind old change listener
				session.removeListener('change', onChangeListener);

				// bind new change listener
				onChangeListener = listenerFactory.onChange(opts.onChange);
				session.on('change', onChangeListener);

				// unbind old blur listener
				//session.removeListener('blur', onBlurListener);
				acee.removeListener('blur', onBlurListener);

				// bind new blur listener
				onBlurListener = listenerFactory.onBlur(opts.onBlur);
				acee.on('blur', onBlurListener);

				setOptions(scope, acee, session, opts);
			};

			options = [
				'aceWorkerPath',
				'aceRequire',
				'aceShowGutter',
				'aceUseWrapMode',
				'aceShowInvisibles',
				'aceShowIndentGuides',
				'aceUseSoftTabs',
				'aceShowPrintMargin',
				'aceDisableSearch',
				'aceTheme',
				'aceMode',
				'aceFirstLineNumber',
				'aceAdvanced',
				'aceRendererOptions',
			];

			for (var opt in options) {
				attrs.$observe(options[opt], updateOptions);
			}

			scope.$watch('isLoading', function(value) {
				acee.setReadOnly(value === true);
			});

			// scope.$watch(attrs, updateOptions, /* deep watch */ true);

			elm.on('$destroy', function () {
				acee.session.$stopWorker();
				acee.destroy();
			});

			scope.$watch(function() {
				return [elm[0].offsetWidth, elm[0].offsetHeight];
			}, function() {
				acee.resize();
				acee.renderer.updateFull();
			}, true);

		}
	}
});

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
			var url = '{{ url_for("api.acl_admins", backend=backend, member=grant) }}';
			var method = 'PUT';
			if (!$scope.isAdmin) {
				method = 'DELETE';
			}
			var p = $http({
				url: url,
				method: method,
				headers: { 'X-From-UI': true },
			})
			.catch(myFail)
			.then(function(response) {
				$scope.orig.admin = $scope.isAdmin;
				notifAll(response.data);
			});
			promises.push(p);
		}
		if ($scope.isModerator !== $scope.orig.moderator) {
			disableSubmit();
			var url = '{{ url_for("api.acl_moderators", backend=backend, member=grant) }}';
			var method = 'PUT';
			if (!$scope.isModerator) {
				method = 'DELETE';
			}
			var p = $http({
				url: url,
				method: method,
				headers: { 'X-From-UI': true },
			})
			.catch(myFail)
			.then(function(response) {
				$scope.orig.moderator = $scope.isModerator;
				notifAll(response.data);
			});
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
			.catch(myFail)
			.then(function(response) {
				$scope.orig.grantValue = $scope.grantValue;
				notifAll(response.data);
			});
			promises.push(p);
		}
		$q.all(promises).finally(function() { enableSubmit(); });
	};
}]);
