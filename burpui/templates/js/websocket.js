var socket;

$(function() {
	/***
	 * Websocket
	 */
	var running_status = undefined;

	{% if config.WS_URL %}
	socket = io({{ config.WS_URL }} + '/ws');
	{% else %}
	socket = io('/ws');
	{% endif %}
	socket.on('backup_running', function(running) {
		if (running_status != running) {
			_check_running();
			running_status = running;
		}
	});
});
