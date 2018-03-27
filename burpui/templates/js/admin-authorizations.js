{% import 'macros.html' as macros %}

var _cache_id = _EXTRA;

var _me = undefined;
var _users = {};
var _groups = {};
var _auth_backends = {};
var _users_array = [];
var __promises = [];
var __globals_promises = [];

var app = angular.module('MainApp', ['ngSanitize', 'ui.select', 'mgcrea.ngStrap', 'datatables']);

app.config(function(uiSelectConfig) {
	uiSelectConfig.theme = 'bootstrap';
});

app.controller('AdminCtrl', ['$scope', '$http', '$scrollspy', 'DTOptionsBuilder', 'DTColumnDefBuilder', function($scope, $http, $scrollspy, DTOptionsBuilder, DTColumnDefBuilder) {
	var vm = this;
	$scope.auth_backends = [];

  $http.get('{{ url_for("api.acl_backends") }}', { headers: { 'X-From-UI': true } })
		.then(function (response) {
			$scope.auth_backends = [];
			_auth_backends = {};
			angular.forEach(response.data, function(back, i) {
				_auth_backends[back.name] = back;
				$scope.auth_backends.push(back);
			});
			$scope.auth_backend = "placeholder";
			/*
			vm.userAdd.auth_backend.$setValidity('valid', false);
			vm.userAdd.$setPristine();
			*/
		});

	$scope.checkSelect = function() {
		vm.userAdd.auth_backend.$setValidity('valid', ($scope.auth_backend != "placeholder"));
	};

	$scope.addUser = function(e) {
		e.preventDefault();
		var form = $(e.target);
		submit = form.find('button[type="submit"]');
		sav = submit.html();
		submit.html('<i class="fa fa-fw fa-spinner fa-pulse" aria-hidden="true"></i>&nbsp;{{ _("Creating...") }}');
		submit.attr('disabled', true);
		$http({
			url: form.attr('action'),
			method: form.attr('method'),
			params: {
				username: $scope.auth_username,
				password: $scope.auth_password,
				backend: $scope.auth_backend,
			},
			headers: { 'X-From-UI': true },
		})
		.catch(myFail)
		.then(function(response) {
			notifAll(response.data);
			$scope.auth_username = null;
			$scope.auth_password = null;
			$scope.auth_backend = "placeholder";
			vm.userAdd.auth_backend.$setValidity('valid', false);
			vm.userAdd.auth_username.$setUntouched();
			vm.userAdd.auth_password.$setUntouched();
			vm.userAdd.auth_password.$setPristine();
			vm.userAdd.$setPristine();
			_authentication();
		})
		.finally(function() {
			submit.html(sav);
			submit.attr('disabled', false);
		});
	};
}]);

var _groups_table = $('#table-groups').DataTable( {
	{{ macros.translate_datatable() }}
	{{ macros.get_page_length() }}
	responsive: true,
	processing: true,
	fixedHeader: true,
	select: {
		style: 'os',
	},
	data: [],
	rowId: 'id',
	rowCallback: function( row, data, index ) {
		var classes = row.className.split(' ');
		_.each(classes, function(cl) {
			if (_.indexOf(['odd', 'even'], cl) != -1) {
				row.className = cl;
				return;
			}
		});
		if (data.id === _me.name) {
			row.className += ' success';
		}
	},
	columns: [
		{
			data: 'id',
		},
		{
			data: 'backends',
			render: function ( data, type, row ) {
				if (type === 'filter' || type === 'sort') {
					return data;
				}
				var ret = '';
				$.each(data, function(i, back) {
					ret += '<span class="label label-default">'+back+'</span>&nbsp;';
				});
				return ret;
			}
		},
		{
			data: 'members',
			render: function ( data, type, row ) {
				if (type === 'filter' || type === 'sort') {
					return data.length+'-'+data.join(',');
				}
				return '<span class="badge" data-toggle="tooltip" title="'+data.join(', ')+'">'+data.length+'</span>';
			}
		},
		{
			data: 'grants',
			render: function ( data, type, row ) {
				if (type === 'filter' || type === 'sort') {
					return data;
				}
				var ret = '';
				$.each(data, function(i, grant) {
					ret += '<code data-toggle="tooltip" data-html="true" title="<code>'+grant.replace(/\"/g,'&quot;')+'</code>">'+$.trim(grant).substring(0, 20).split(' ').slice(0, -1).join(" ")+'...</code>&nbsp;';
				});
				return ret;
			}
		},
		{
			data: null,
			orderable: false,
			render: function ( data, type, row ) {
				return '<button data-member="'+data.id+'" class="btn btn-xs btn-danger btn-delete-user" title="{{ _("Remove") }}"><i class="fa fa-trash" aria-hidden="true"></i></button>&nbsp;<button data-member="'+data.id+'" class="btn btn-xs btn-info btn-edit-user" title="{{ _("Edit") }}"><i class="fa fa-pencil" aria-hidden="true"></i></button>';
			}
		},
	],
});

_groups_table.on('draw.dt', function() {
	$('[data-toggle="tooltip"]').tooltip();
});

var _users_table = $('#table-users').DataTable( {
	{{ macros.translate_datatable() }}
	{{ macros.get_page_length() }}
	responsive: true,
	processing: true,
	fixedHeader: true,
	select: {
		style: 'os',
	},
	data: [],
	rowId: 'id',
	rowCallback: function( row, data, index ) {
		var classes = row.className.split(' ');
		_.each(classes, function(cl) {
			if (_.indexOf(['odd', 'even'], cl) != -1) {
				row.className = cl;
				return;
			}
		});
		if (data.id === _me.name) {
			row.className += ' success';
		}
	},
	columns: [
		{
			data: 'id',
		},
		{
			data: 'backends',
			render: function ( data, type, row ) {
				if (type === 'filter' || type === 'sort') {
					return data;
				}
				var ret = '';
				$.each(data, function(i, back) {
					ret += '<span class="label label-default">'+back+'</span>&nbsp;';
				});
				return ret;
			}
		},
		{
			data: 'roles',
			render: function ( data, type, row ) {
				if (type === 'filter' || type === 'sort') {
					return data;
				}
				var ret = '';
				$.each(data, function(i, role) {
					ret += '<span class="label label-warning">'+role+'</span>&nbsp;';
				});
				return ret;
			}
		},
		{
			data: 'groups',
			render: function ( data, type, row ) {
				if (type === 'filter' || type === 'sort') {
					return data;
				}
				var ret = '';
				$.each(data, function(i, group) {
					ret += '<span class="label label-primary">'+group+'</span>&nbsp;';
				});
				return ret;
			}
		},
		{
			data: 'grants',
			render: function ( data, type, row ) {
				if (type === 'filter' || type === 'sort') {
					return data;
				}
				var ret = '';
				$.each(data, function(i, grant) {
					ret += '<code data-toggle="tooltip" data-html="true" title="<code>'+grant.replace(/\"/g,'&quot;')+'</code>">'+$.trim(grant).substring(0, 20).split(' ').slice(0, -1).join(" ")+'...</code>&nbsp;';
				});
				return ret;
			}
		},
		{
			data: null,
			orderable: false,
			render: function ( data, type, row ) {
				return '<button data-member="'+data.id+'" class="btn btn-xs btn-danger btn-delete-user" title="{{ _("Remove") }}"><i class="fa fa-trash" aria-hidden="true"></i></button>&nbsp;<button data-member="'+data.id+'" class="btn btn-xs btn-info btn-edit-user" title="{{ _("Edit") }}"><i class="fa fa-pencil" aria-hidden="true"></i></button>';
			}
		},
	],
});

_users_table.on('draw.dt', function() {
	$('[data-toggle="tooltip"]').tooltip();
});

var g = $.getJSON('{{ url_for("api.admin_me") }}').done(function (data) {
	_me = data;
});
__globals_promises.push(g);

var _authorization_users = function() {
	$('#waiting-user-container').show();
	$('#table-users-container').hide();
	var __usernames = [];
	var __top_promises = [];
	var t = $.getJSON('{{ url_for("api.acl_grants") }}').done(function (grants) {
		__promises = [];
		$.each(grants, function(i, user) {
			__usernames.push(user.id);
			if (_users[user.id]) {
				if (_users[user.id]['backends'].indexOf(user.backend) === -1) {
					_users[user.id]['backends'].push(user.backend);
				}
				if (_users[user.id]['grants'].indexOf(user.grant) === -1) {
					_users[user.id]['grants'].push(user.grant);
				}
				if (_users[user.id]['raw'].indexOf(user) === -1) {
					_users[user.id]['raw'].push(user);
				}
			} else {
				_users[user.id] = {
					id: user.id,
					backends: [user.backend],
					roles: [],
					groups: [],
					grants: [user.grant],
					raw: [user],
				};
				var p = $.getJSON('{{ url_for("api.acl_groups_of", member="") }}'+user.id).done(function (data) {
					_users[user.id]['groups'] = data.groups;
				});
				__promises.push(p);
				p = $.getJSON('{{ url_for("api.acl_is_admin", member="") }}'+user.id).done(function (data) {
					if (data.admin) {
						_users[user.id]['roles'].push('admin');
					}
				});
				__promises.push(p);
				p = $.getJSON('{{ url_for("api.acl_is_moderator", member="") }}'+user.id).done(function (data) {
					if (data.moderator) {
						_users[user.id]['roles'].push('moderator');
					}
				});
				__promises.push(p);
			}
		});
		__top_promises.push(t);
		var redraw = false;
		_users_array = [];
		$.each(_users, function(key, value) {
			if (__usernames.indexOf(key) == -1) {
				delete _users[key];
				redraw = true;
			} else {
				_users_array.push(value);
			}
		});
		if (redraw) {
			_users_table.clear();
			_users_table.rows.add(_users_array).draw();
			$('#waiting-user-container').hide();
			$('#table-users-container').show();
		}
		$.when.apply( $, __top_promises ).done(function() {
			$.when.apply( $, __promises ).done(function() {
				_users_array = [];
				$.each(_users, function(key, value) {
					_users_array.push(value);
				});
				_users_table.clear();
				_users_table.rows.add(_users_array).draw();
				$('#waiting-user-container').hide();
				$('#table-users-container').show();
			});
		});
	});
};

var _authorization_groups = function() {
	$('#waiting-group-container').show();
	$('#table-groups-container').hide();
	var __groupnames = [];
	var __top_promises = [];
	var t = $.getJSON('{{ url_for("api.acl_groups") }}').done(function (groups) {
		$.each(groups, function(i, group) {
			__groupnames.push(group.id);
			if (_groups[group.id]) {
				if (_groups[group.id]['backends'].indexOf(group.backend) === -1) {
					_groups[group.id]['backends'].push(group.backend);
				}
				if (_groups[group.id]['grants'].indexOf(group.grant) === -1) {
					_groups[group.id]['grants'].push(group.grant);
				}
				if (_groups[group.id]['raw'].indexOf(group) === -1) {
					_groups[group.id]['raw'].push(group);
				}
				_groups[group.id]['members'] = _.uniq(_.concat(_groups[group.id]['members'], group.members));
			} else {
				_groups[group.id] = {
					id: group.id,
					backends: [group.backend],
					members: group.members,
					grants: [group.grant],
					raw: [group],
				};
			}
		});
		__top_promises.push(t);
		var redraw = false;
		_groups_array = [];
		$.each(_groups, function(key, value) {
			if (__groupnames.indexOf(key) == -1) {
				delete _groups[key];
				redraw = true;
			} else {
				_groups_array.push(value);
			}
		});
		if (redraw) {
			_groups_table.clear();
			_groups_table.rows.add(_groups_array).draw();
			$('#waiting-group-container').hide();
			$('#table-groups-container').show();
		}
		$.when.apply( $, __top_promises ).done(function() {
			_groups_array = [];
			$.each(_groups, function(key, value) {
				_groups_array.push(value);
			});
			_groups_table.clear();
			_groups_table.rows.add(_groups_array).draw();
			$('#waiting-group-container').hide();
			$('#table-groups-container').show();
		});
	});
};

var _admin = function() {
	_authorization_users();
	_authorization_groups();
};

{{ macros.page_length('#table-list-clients') }}
{{ macros.page_length('#table-list-templates') }}

$( document ).ready(function () {
	$('#config-nav a').click(function (e) {
		e.preventDefault();
		$(this).tab('show');
	});
});

/* Delete user */
var _remove_selected = 0;
$( document ).on('click', '.btn-delete-user', function(e) {
	var user_id = $(this).data('member');
	var user = _users[user_id];
	var content = '<legend>{{ _("Please select the backend(s) from which to remove the user:") }}</legend>';
	$.each(user['backends'], function(i, back) {
		var disabled_legend = '{{ _("The backend does not support user removal") }}';
		var disabled = 'disabled title="'+disabled_legend+'"';
		var is_enabled = _auth_backends[back]['del'];
		content += '<div class="checkbox"><label><input type="checkbox" name="user_backend" data-id="'+user_id+'" data-backend="'+back+'" '+(is_enabled?'':disabled)+'>'+back+(is_enabled?'':' <em>('+disabled_legend+')</em>')+'</label></div>';
	});
	/* disable submit button while we did not select a backend */
	$('#perform-delete').prop('disabled', true);
	$('#delete-details').html(content);
	$('#delete-user-modal').modal('toggle');
});
$( document ).on('change', 'input[name=user_backend]', function(e) {
	var user_id = $(this).data('id');
	var backend = $(this).data('backend');
	if (user_id == _me.id && backend == _me.backend) {
		if ($(this).is(':checked')) {
			$('#delete-confirm').show();
		} else {
			$('#delete-confirm').hide();
		}
	}
	if ($(this).is(':checked')) {
		_remove_selected++;
	} else {
		_remove_selected--;
	}
	if (_remove_selected > 0) {
		$('#perform-delete').prop('disabled', false);
	} else {
		$('#perform-delete').prop('disabled', true);
	}
});
$('#perform-delete').on('click', function(e) {
	$.each($('input[name=user_backend]'), function(i, elmt) {
		var e = $(elmt);
		if (e.is(':checked')) {
			$.ajax({
				url: "{{ url_for('api.auth_users', name='') }}"+$(e).data('id')+"?backend="+$(e).data('backend'),
				type: 'DELETE',
				headers: { 'X-From-UI': true },
			}).done(function(data) {
				notifAll(data);
				_authentication();
			}).fail(myFail);
		}
	});
});

/* Edit user */
$( document ).on('click', '.btn-edit-user', function(e) {
	var user_id = $(this).data('member');
	var user = _users[user_id];
	var content = '<legend>{{ _("Please select the backend from which to edit the user from:") }}</legend>';
	content += '<div class="form-group"><label for="edit_backend" class="col-lg-2 control-label">Backend</label>';
	content += '<div class="col-lg-10"><select class="form-control" id="edit_backend" name="edit_backend" data-id="'+user_id+'"><option disabled selected value="placeholder">'+'{{ _("Please select a backend") }}'+'</option>';
	$.each(user['backends'], function(i, back) {
		is_enabled = _auth_backends[back]['mod'];
		content += '<option'+(is_enabled?'':' disabled')+'>'+back+'</option>';
	});
	content += '</select></div></div>';
	$('#perform-edit').prop('disabled', true);
	$('#edit-details').html(content);
	$('#edit-user-modal').modal('toggle');
});
$( document ).on('change', '#edit_backend', function(e) {
	if ($('#edit_backend option:selected').val() != 'placeholder') {
		$('#perform-edit').prop('disabled', false);
	}
});
$('#perform-edit').on('click', function(e) {
	location = "{{ url_for('view.admin_authentication', user='') }}"+$('#edit_backend').data('id')+'?backend='+$('#edit_backend option:selected').text();
});

/* user sessions */
$( document ).on('click', '.btn-sessions-user', function(e) {
	var user_id = $(this).data('member');
	location = "{{ url_for('view.admin_sessions', user='') }}"+user_id;
});
