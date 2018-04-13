{% import 'macros.html' as macros %}

var _cache_id = _EXTRA;

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
				var body = data.split('\n')[0];
				var tooltip = escapeDoubleQuotes(data);
				return '<span data-toggle="tooltip" title=\''+tooltip+'\' data-html="true" >'+body+'</span>';
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
	}
};

{{ macros.page_length('#table-backends') }}

_backends_table.on('draw.dt', function() {
	$('[data-toggle="tooltip"]').tooltip();
});

/* Edit user */
$( document ).on('click', '.btn-edit-backend', function(e) {
	var backend_id = $(this).data('backend');
	document.location = '{{ url_for("view.admin_backend", backend="") }}'+backend_id;
});
