
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

var app = angular.module('MainApp', ['ngSanitize', 'ui.select', 'mgcrea.ngStrap', 'datatables']);

app.config(function(uiSelectConfig) {
	uiSelectConfig.theme = 'bootstrap';
});

app.controller('AdminCtrl', ['$scope', '$http', '$scrollspy', 'DTOptionsBuilder', 'DTColumnDefBuilder', function($scope, $http, $scrollspy, DTOptionsBuilder, DTColumnDefBuilder) {
}]);

var _me = undefined;
var _users_table = undefined;

$.getJSON('{{ url_for("api.admin_me") }}').done(function (data) {
	_me = data;
	_users_table = $('#table-users').DataTable( {
		{{ macros.translate_datatable() }}
		{{ macros.get_page_length() }}
		responsive: true,
		processing: true,
		fixedHeader: true,
		select: {
			style: 'os',
		},
		ajax: {
			url: '{{ url_for("api.user_sessions") }}',
			headers: { 'X-From-UI': true },
			cache: AJAX_CACHE,
			error: myFail,
			data: function (request) {
				request._extra = _cache_id;
			},
			dataSrc: function (data) {
				return data;
			}
		},
	});
});


{{ macros.page_length('#table-list-clients') }}
{{ macros.page_length('#table-list-templates') }}

$(document).ready(function () {
	$('#config-nav a').click(function (e) {
		e.preventDefault();
		$(this).tab('show');
	});
});
