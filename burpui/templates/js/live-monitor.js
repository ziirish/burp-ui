
{% if config.STANDALONE -%}
	{% if cname -%}
var counters = '{{ url_for("api.counters", client=cname) }}';
	{% else -%}
var counters = '{{ url_for("api.live") }}';
	{% endif -%}
{% else -%}
	{% if cname -%}
var counters = '{{ url_for("api.counters", client=cname, server=server) }}';
	{% elif server -%}
var counters = '{{ url_for("api.live", server=server) }}';
	{% else -%}
var counters = '{{ url_for("api.live") }}';
	{% endif -%}
{% endif -%}


var app = angular.module('MainApp', ['ngSanitize']);


app.filter('time_human', [function() {
	return function(d) {
		s = '';
		seconds = (((d % 31536000) % 86400) % 3600) % 60;
		minutes = Math.floor((((d % 31536000) % 86400) % 3600) / 60);
		hours = Math.floor(((d % 31536000) % 86400) / 3600);
		if (hours > 0) {
			s = pad(hours, 2) + 'H ';
		}
		s += pad(minutes, 2) + 'm ' + pad(seconds, 2) + 's';
		return s;
	};
}]);

app.filter('bytes_human', [function() {
	return function(d) {
		return _bytes_human_readable(d);
	};
}]);

app.controller('LiveCtrl', function($scope, $http, $timeout) {
	$scope.clients = [];
	var timer;

	$scope.stopTimer = function() {
		if (angular.isDefined(timer)) {
			$timeout.cancel(timer);
			timer = undefined;
		}
	};

	var last_status = 404;
	$scope.load = function() {
		$http.get(counters, { headers: { 'X-From-UI': true } })
		.then(function(response) {
			var data = response.data;
			if (angular.isArray(data)) {
				$scope.clients = data;
			} else {
				$scope.clients = [];
				$scope.clients.push(data);
			}
			if ($scope.clients.length == 0) {
				var message = "{{ _('No more backup running') }}";
				$scope.stopTimer();
				$http.post('{{ url_for("api.alert") }}', {'message': message}, { headers: { 'X-From-UI': true } })
				.then(function(response2) {
					document.location = '{{ url_for("view.home") }}';
				});
				return;
			}
			last_status = response.status;
			timer = $timeout($scope.load, {{ config.LIVEREFRESH * 1000 }});
		}, function(response) {
			var data = response.data;
			$scope.stopTimer();
			if (response.status === 404 && response.status !== last_status) {
				$scope.stopTimer();
				notif(NOTIF_INFO, "{{ _('Backup complete') }}");
			} else {
				errorsHandler(data);
			}
			notif(NOTIF_INFO, "{{ _('Will redirect you in 5 seconds') }}");
			$timeout(function() {
				document.location = '{{ url_for("view.home") }}';
			}, 5000);
		});
	};

	$scope.refresh = function(e) {
		e.preventDefault();
		$scope.load();
	};

	$scope.load();
});
