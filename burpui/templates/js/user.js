/***
 * The User page is managed with AngularJS for some parts.
 * Following is the AngularJS Application and Controller.
 */
var app = angular.module('MainApp', ['ngSanitize', 'frapontillo.bootstrap-switch', 'mgcrea.ngStrap']);

app.directive('compareTo', function() {
	return {
		require: "ngModel",
		scope: {
			otherModelValue: "=compareTo"
		},
		link: function(scope, element, attributes, ngModel) {
			ngModel.$validators.compareTo = function(modelValue) {
				return modelValue == scope.otherModelValue;
			};

			scope.$watch("otherModelValue", function() {
				ngModel.$validate();
			});
		}
	};
});

app.controller('UserCtrl', function($timeout, $scope, $http, $scrollspy) {
	$scope.spy = {};
	$scope.user = {
		oldPassword: '',
		newPassword: '',
		confPassword: ''
	};

	$scope.submitChangePass = function(e) {
		e.preventDefault();
		var form = $(e.target);
		submit = form.find('button[type="submit"]');
		sav = submit.text();
		submit.text('Saving...');
		submit.attr('disabled', true);
		/* submit the data */
		$.ajax({
			url: form.attr('action'),
			type: 'POST',
			data: {
				'password': $scope.user.newPassword,
				'old_password': $scope.user.oldPassword,
				'backend': "{{ current_user.back.name }}"
			},
			headers: { 'X-From-UI': true },
		})
		.fail(myFail)
		.done(function(data) {
			notifAll(data);
		})
		.always(function() {
			/* reset the submit button state */
			submit.text(sav);
			submit.attr('disabled', false);
		});
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

	$timeout(function() {
		$scope.refreshScrollspy();
	});
	/*
	$scope.api = '';
	$scope.burp = Array();

	$http.get('{{ url_for("api.about") }}', { headers: { 'X-From-UI': true } })
		.success(function(data, status, headers, config) {
			$scope.version = data.version;
			$scope.api = data.api;
			$scope.burp = data.burp;
		});
	*/
});

/***
 * The session part is handled by datatables
 * the resulting JSON looks like:
 * [
 *  {
 *    "api": false,
 *    "current": false,
 *    "expire": "1970-01-01T00:00:00+01:00",
 *    "ip": "::ffff:10.0.0.100",
 *    "permanent": false,
 *    "timestamp": "2016-09-01T15:28:59.222028+02:00",
 *    "ua": "Mozilla/5.0 (X11; Linux x86_64; rv:45.0) Gecko/20100101 Firefox/45.0",
 *    "uuid": "feaac9c7-6f61-4103-9536-d65aba335892"
 *  }
 * ]
 */
{% import 'macros.html' as macros %}

{{ macros.timestamp_filter() }}

var _sessions_table = $('#table-sessions').dataTable( {
	{{ macros.translate_datatable() }}
	{{ macros.get_page_length() }}
	responsive: true,
	ajax: {
		url: '{{ url_for("api.user_sessions") }}',
		headers: { 'X-From-UI': true },
		error: myFail,
		dataSrc: function (data) {
			return data;
		}
	},
	order: [[1, 'desc']],
	destroy: true,
	/*
	rowCallback: function( row, data ) {
		// do nothing
	},
	*/
	columns: [
		{ data: 'ip' },
		{
			data: null,
			type: 'timestamp',
			render: function( data, type, row ) {
				return '<span data-toggle="tooltip" title="'+data.timestamp+'">'+moment(data.timestamp, moment.ISO_8601).subtract(3, 'seconds').fromNow()+'</span>';
			}
		},
		{ 
			data: null,
			render: function( data, type, row ) {
				ret = '';
				// Browser version
				if (data.ua.lastIndexOf('MSIE') > 0 || data.ua.lastIndexOf('Trident') > 0) {
					ret += '<i class="fa fa-internet-explorer" aria-hidden="true"></i>';
				} else if (data.ua.lastIndexOf('Edge') > 0) {
					ret += '<i class="fa fa-edge" aria-hidden="true"></i>';
				} else if (/Firefox[\/\s](\d+\.\d+)/.test(data.ua)) {
					ret += '<i class="fa fa-firefox" aria-hidden="true"></i>';
				} else if (data.ua.lastIndexOf('Chrome/') > 0) {
					ret += '<i class="fa fa-chrome" aria-hidden="true"></i>';
				} else if (data.ua.lastIndexOf('Safari/') > 0) {
					ret += '<i class="fa fa-safari" aria-hidden="true"></i>';
				} else {
					ret += '<i class="fa fa-question" aria-hidden="true"></i>';
				}
				// Optionally add OS version
				if (data.ua.lastIndexOf('Android') > 0) {
					ret += '&nbsp;<i class="fa fa-android" aria-hidden="true"></i>';
				} else if (data.ua.lastIndexOf('iPhone') > 0 || data.ua.lastIndexOf('iPad') > 0 || data.ua.lastIndexOf('Macintosh') > 0) {
					ret += '&nbsp;<i class="fa fa-apple" aria-hidden="true"></i>';
					if (data.ua.lastIndexOf('iPhone') > 0) {
						ret += '&nbsp;<i class="fa fa-mobile" aria-hidden="true"></i>';
					} else if (data.ua.lastIndexOf('iPad') > 0) {
						ret += 'anbsp;<i class="fa fa-tablet" aria-hidden="true"></i>';
					}
				} else if (data.ua.lastIndexOf('Linux') > 0) {
					ret += '&nbsp;<i class="fa fa-linux" aria-hidden="true"></i>';
				} else if (data.ua.lastIndexOf('Windows') > 0) {
					ret += '&nbsp;<i class="fa fa-windows" aria-hidden="true"></i>';
				}
				return '<span data-toggle="tooltip" title="'+data.ua+'">'+ret+'</span>';
			}
		},
		{
			data: null,
			render: function( data, type, row ) {
				return '<span class="glyphicon glyphicon-'+(data.api?'ok':'remove')+'"></span>';
			}
		},
		{
			data: null,
			render: function( data, type, row ) {
				return '<span class="glyphicon glyphicon-'+(data.current?'ok':'remove')+'"></span>';
			}
		},
		{
			data: null,
			type: 'timestamp',
			render: function( data, type, row ) {
				return '<span data-toggle="tooltip" title="'+data.expire+'">'+moment(data.expire, moment.ISO_8601).fromNow()+'</span>';
			}
		},
		{
			data: null,
			render: function( data, type, row ) {
				return '<button class="btn btn-danger" data-toggle="revoke-session" data-id="'+data.uuid+'" data-current="'+data.current+'" data-misc="'+escape(JSON.stringify(data, null, 4))+'"><span class="glyphicon glyphicon-trash"></span></button>';
			}
		}
	],
});
var first = true;

var _sessions = function() {
	if (first) {
		first = false;
	} else {
		_sessions_table.api().ajax.reload( null, false );
	}
};

_events_callback = function() {
	$('[data-toggle="tooltip"]').tooltip();
	$('[data-toggle="revoke-session"]').on('click', function(e) {
		$me = $(this);
		if ($me.data('current')) {
			$('#error-confirm').show();
		} else {
			$('#error-confirm').hide();
		}
		$('#session-details').empty().html(unescape($me.data('misc')));
		$('#perform-revoke').data('id', $me.data('id'));
		$('#perform-revoke').data('current', $me.data('current'));
		$('#confirmation-modal').modal('toggle');
	});
};
_sessions_table.on('draw.dt', _events_callback);
_sessions_table.on('responsive-display.dt', function ( e, datatable, row, showHide, update ) {
	_events_callback();
});
{{ macros.page_length('#table-sessions') }}

$('#perform-revoke').on('click', function(e) {
	$me = $(this);
	if ($me.data('current')) {
		window.location = '{{ url_for("view.logout") }}';
		return;
	}
	$.ajax({
		url: '{{ url_for("api.user_sessions") }}/'+$me.data('id'),
		headers: { 'X-From-UI': true },
		type: 'DELETE'
	}).done(function(data) {
		notifAll(data);
		if (data[0] == NOTIF_SUCCESS) {
			_sessions();
		}
	}).fail(myFail);
});
