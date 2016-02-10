
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

app.controller('LiveCtrl', function($scope, $http, $interval) {
	$scope.clients = [];
	var timer;

	$scope.stopTimer = function() {
		if (angular.isDefined(stop)) {
			$interval.cancel(stop);
			stop = undefined;
		}
	};

	$scope.load = function() {
		$http.get(counters)
		.success(function(data, status, headers, config) {
			if (angular.isArray(data)) {
				$scope.clients = data;
			} else {
				$scope.clients = [];
				$scope.clients.push(data);
			}
			if ($scope.clients.length == 0) {
				$http.post('{{ url_for("api.alert") }}', {'message': 'No more backup running'});
				document.location = '{{ url_for("view.home") }}';
			}
		})
		.error(function(data, status, headers, config) {
			$scope.stopTimer();
			errorsHandler(data);
			setTimeout(function() {
				document.location = '{{ url_for("view.home") }}';
			}, 5000);
		});
	};

	$scope.refresh = function(e) {
		e.preventDefault();
		$scope.load();
	};

	timer = $interval(function() {
		$scope.load();
	}, {{ config.LIVEREFRESH * 1000 }});

	$scope.load();
});
