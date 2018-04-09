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
		},
		headers: { 'X-From-UI': true },
	})
	.fail(buiFail)
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

app.controller('AdminCtrl', ['$scope', '$http', '$scrollspy', 'DTOptionsBuilder', 'DTColumnDefBuilder', function($scope, $http, $scrollspy, DTOptionsBuilder, DTColumnDefBuilder) {
}]);
