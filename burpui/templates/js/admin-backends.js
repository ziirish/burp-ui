{% import 'macros.html' as macros %}

var _cache_id = _EXTRA;
var __backends_icons = {
	'authentication': '<i class="fa fa-fw fa-id-card-o" aria-hidden="true"></i>&nbsp;',
	'authorization': '<i class="fa fa-fw fa-lock" aria-hidden="true"></i>&nbsp;',
};

var app = angular.module('MainApp', ['ngSanitize', 'ui.select', 'mgcrea.ngStrap', 'datatables']);

app.config(function(uiSelectConfig) {
	uiSelectConfig.theme = 'bootstrap';
});

app.controller('AdminCtrl', ['$scope', '$http', '$scrollspy', 'DTOptionsBuilder', 'DTColumnDefBuilder', function($scope, $http, $scrollspy, DTOptionsBuilder, DTColumnDefBuilder) {
}]);

var _backends_table = $('#table-backends').DataTable( {
	{{ macros.translate_datatable() }}
	{{ macros.get_page_length() }}
	responsive: true,
	processing: true,
	fixedHeader: true,
	select: {
		style: 'os',
	},
	ajax: {
		url: '{{ url_for("api.acl_backends") }}',
		dataSrc: function (data) {
			return data;
		},
		error: buiFail,
		headers: { 'X-From-UI': true },
	},
	rowId: 'name',
	columns: [
		{
			data: 'name',
			render: function ( data, type, row ) {
				return data;
			}
		},
		{
			data: 'description',
			render: function ( data, type, row ) {
				if (type === 'filter' || type === 'sort') {
					return data;
				}
				var body = '';
				if (data) {
					body = data.split('\n')[0];
				}
				var tooltip = escapeDoubleQuotes(data);
				return '<span data-toggle="tooltip" title=\''+tooltip+'\' data-html="true" >'+body+'</span>';
			}
		},
		{
			data: 'priority',
			render: function ( data, type, row ) {
				if (type === 'filter' || type === 'sort') {
					return data;
				}
				return '<span class="badge">'+data+'</span>';
			}
		},
		{
			data: 'type',
			render: function ( data, type, row ) {
				if (type === 'filter' || type === 'sort') {
					return data;
				}
				return '<span class="label label-default">'+__backends_icons[data]+data+'</span>';
			}
		},
	],
});
var _auth_backends_table = $('#table-auth-backends').DataTable( {
	{{ macros.translate_datatable() }}
	{{ macros.get_page_length() }}
	responsive: true,
	processing: true,
	fixedHeader: true,
	select: {
		style: 'os',
	},
	ajax: {
		url: '{{ url_for("api.auth_backends") }}',
		dataSrc: function (data) {
			return data;
		},
		error: buiFail,
		headers: { 'X-From-UI': true },
	},
	rowId: 'name',
	columns: [
		{
			data: 'name',
			render: function ( data, type, row ) {
				return data;
			}
		},
		{
			data: 'description',
			render: function ( data, type, row ) {
				if (type === 'filter' || type === 'sort') {
					return data;
				}
				var body = '';
				if (data) {
					body = data.split('\n')[0];
				}
				var tooltip = escapeDoubleQuotes(data);
				return '<span data-toggle="tooltip" title=\''+tooltip+'\' data-html="true" >'+body+'</span>';
			}
		},
		{
			data: 'priority',
			render: function ( data, type, row ) {
				if (type === 'filter' || type === 'sort') {
					return data;
				}
				return '<span class="badge">'+data+'</span>';
			}
		},
		{
			data: 'type',
			render: function ( data, type, row ) {
				if (type === 'filter' || type === 'sort') {
					return data;
				}
				return '<span class="label label-default">'+__backends_icons[data]+data+'</span>';
			}
		},
	],
});
var first = true;

var _admin = function() {
	if (first) {
		first = false;
	} else {
		_backends_table.ajax.reload( null, false );
		_auth_backends_table.ajax.reload( null, false );
	}
};

{{ macros.page_length('#table-backends') }}
{{ macros.page_length('#table-auth-backends') }}

_backends_table.on('draw.dt', function() {
	$('[data-toggle="tooltip"]').tooltip();
});
_auth_backends_table.on('draw.dt', function() {
	$('[data-toggle="tooltip"]').tooltip();
});

/* Edit user */
$( document ).on('click', '.btn-edit-backend', function(e) {
	var backend_id = $(this).data('backend');
	document.location = '{{ url_for("view.admin_backend", backend="") }}'+backend_id;
});
