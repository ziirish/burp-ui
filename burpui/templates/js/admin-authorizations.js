{% import 'macros.html' as macros %}

var _cache_id = _EXTRA;

var _me = undefined;
var _users = {};
var _groups = {};
var _acl_backends = {};
var _users_array = [];
var __globals_promises = [];

var app = angular.module('MainApp', ['ngSanitize', 'ui.select', 'mgcrea.ngStrap', 'datatables']);

app.config(function(uiSelectConfig) {
	uiSelectConfig.theme = 'bootstrap';
});

{{ macros.angular_ui_ace() }}

app.controller('AdminCtrl', ['$scope', '$http', '$q', '$scrollspy', 'DTOptionsBuilder', 'DTColumnDefBuilder', function($scope, $http, $q, $scrollspy, DTOptionsBuilder, DTColumnDefBuilder) {
	var vm = this;
	var _g_promises = [];
	$scope.acl_backends = [];
	$scope.isLoading = false;
	$scope.validGrantInput = true;
	$scope.grantValue = '';
	$scope.loadingMembers = true;
	$scope.mode = undefined;
	$scope.isAdmin = false;
	$scope.isModerator = false;
	$scope.dismiss = true;
	vm.grantAdd = {};
	vm.grantAdd.groupMembers = [];
	vm.grantAdd.backendUsers = [];

  var g = $http.get('{{ url_for("api.acl_backends") }}', { headers: { 'X-From-UI': true } })
		.then(function (response) {
			$scope.acl_backends = [];
			_acl_backends = {};
			angular.forEach(response.data, function(back, i) {
				_acl_backends[back.name] = back;
				$scope.acl_backends.push(back);
			});
			$scope.acl_backend = "placeholder";
		});
	_g_promises.push(g);

	$scope.addNewGroup = function() {
		$scope.modalTitle = '{{ _("Create Group") }}';
		$scope.modalLegend = '{{ _("Create new Group") }}';
		$scope.nameLabel = '{{ _("Group name") }}';
		if ($scope.mode !== 'group') {
			$scope.grantValue = '';
			vm.grantAdd.groupMembers = []
		}
		$scope.mode = 'group';
		$scope.url = '{{ url_for("api.acl_groups") }}';
		$scope.httpParams = $scope.genNewGroupParams;
		$scope.httpCallback = $scope.addGroupCallback;
		$('#create-grant-modal').modal('toggle');
	};
	$scope.genNewGroupParams = function() {
		return {
			backend: $scope.acl_backend,
			group: $scope.name,
			grant: $scope.grantValue ? JSON.stringify(JSON.parse($scope.grantValue)) : "", // remove indentation
		};
	};
	$scope.addGroupCallback = function(response) {
		var locals = [];
		if (vm.grantAdd.groupMembers.length > 0) {
			var l = $http({
				url: '{{ url_for("api.acl_group_members") }}',
				method: 'PUT',
				data: {
					groupName: $scope.name,
					backendName: $scope.acl_backend,
					memberNames: vm.grantAdd.groupMembers,
				},
				headers: {
					'X-From-UI': true,
				},
			})
			.catch(buiFail)
			.then(function (resp2) {
				notifAll(resp2.data);
			});
			locals.push(l);
		}
		if ($scope.isAdmin) {
			var l = $http({
				url: '{{ url_for("api.acl_admin") }}',
				method: 'PUT',
			  params: {
					memberNames: '@'+$scope.name,
					backendName: $scope.acl_backend,
				},
				headers: { 'X-From-UI': true },
			})
			.catch(buiFail)
			.then(function(resp2) {
				notifAll(resp2.data);
			});
			locals.push(l);
		}
		if ($scope.isModerator) {
			var l = $http({
				url: '{{ url_for("api.acl_moderator") }}',
				method: 'PUT',
			  params: {
					memberNames: '@'+$scope.name,
					backendName: $scope.acl_backend,
				},
				headers: { 'X-From-UI': true },
			})
			.catch(buiFail)
			.then(function(resp2) {
				notifAll(resp2.data);
			});
			locals.push(l);
		}
		$q.all(locals).finally(function() {
			_authorization_groups();
			_authorization_users();
		});
		// mandatory: we need to pass the response to the next function
		return response;
	};

	$scope.addNewGrant = function() {
		$scope.modalTitle = '{{ _("Create Grant") }}';
		$scope.modalLegend = '{{ _("Create new Grant") }}';
		$scope.nameLabel = '{{ _("Grant/User name") }}';
		if ($scope.mode !== 'grant') {
			$scope.grantValue = '';
			$scope.isAdmin = false;
			$scope.isModerator = false;
		}
		$scope.mode = 'grant';
		$scope.url = '{{ url_for("api.acl_grants") }}';
		$scope.httpParams = $scope.genNewGrantParams;
		$scope.httpCallback = $scope.addGrantCallback;
		$('#create-grant-modal').modal('toggle');
	};
	$scope.genNewGrantParams = function() {
		return {
			backend: $scope.acl_backend,
			grant: $scope.name,
			content: $scope.grantValue ? JSON.stringify(JSON.parse($scope.grantValue)) : "", // remove indentation
		};
	};
	$scope.addGrantCallback = function(response) {
		var locals = [];
		var reload_groups = false;
		if ($scope.isAdmin) {
			var l = $http({
				url: '{{ url_for("api.acl_admin") }}',
				method: 'PUT',
			  params: {
					memberNames: $scope.name,
					backendName: $scope.acl_backend,
				},
				headers: { 'X-From-UI': true },
			})
			.catch(buiFail)
			.then(function(resp2) {
				notifAll(resp2.data);
				reload_groups = true;
			});
			locals.push(l);
		}
		if ($scope.isModerator) {
			var l = $http({
				url: '{{ url_for("api.acl_moderator") }}',
				method: 'PUT',
			  params: {
					memberNames: $scope.name,
					backendName: $scope.acl_backend,
				},
				headers: { 'X-From-UI': true },
			})
			.catch(buiFail)
			.then(function(resp2) {
				notifAll(resp2.data);
				reload_groups = true;
			});
			locals.push(l);
		}
    $q.all(locals).finally(function() {
			_authorization_users();
			if (reload_groups) {
				_authorization_groups();
			}
		});
		return response;
	};

	$scope.checkSelect = function() {
		vm.grantAdd.acl_backend.$setValidity('valid', ($scope.acl_backend != "placeholder"));
		if ($scope.acl_backend !== 'placeholder') {
			$scope.loadingMembers = true;
			var locals = [];
			// empty list
			vm.grantAdd.backendUsers = [];
			var l = $http.get(
				'{{ url_for("api.acl_grants") }}',
				{
					params: {
						backend: $scope.acl_backend,
					},
					headers: { 'X-From-UI': true }
				})
				.then(function (response) {
					_.forEach(response.data, function(user) {
						vm.grantAdd.backendUsers.push(user);
					});
				});
			locals.push(l);

			l = $http.get(
				'{{ url_for("api.acl_groups") }}',
				{
					params: {
						backend: $scope.acl_backend,
					},
					headers: { 'X-From-UI': true }
				})
				.then(function (response) {
					_.forEach(response.data, function(group) {
						group['id'] = '@'+group['id'];
						vm.grantAdd.backendUsers.push(group);
					});
				});
			locals.push(l);

			l = $http.get(
				'{{ url_for("api.auth_users") }}',
				{
					headers: { 'X-From-UI': true }
				})
				.then(function (response) {
					_.forEach(response.data, function(user) {
						vm.grantAdd.backendUsers.push(user);
					});
				});
			locals.push(l);

			$q.all(locals).finally(function() {
				$scope.loadingMembers = false;
				vm.grantAdd.backendUsers = _.uniqBy(vm.grantAdd.backendUsers, 'id');
			});
		}
	};

	$scope.actionAllowed = function(back) {
		var capabilities = {
			'grant': 'add_grant',
			'group': 'add_group',
		};
		return back[capabilities[$scope.mode]];
	};

	$scope.addGrant = function(e) {
		e.preventDefault();
		var form = $(e.target);
		submit = form.find('button[type="submit"]');
		sav = submit.html();
		submit.html('<i class="fa fa-fw fa-spinner fa-pulse" aria-hidden="true"></i>&nbsp;{{ _("Creating...") }}');
		submit.attr('disabled', true);
		$http({
			url: $scope.url,
			method: 'PUT',
			params: $scope.httpParams(),
			headers: { 'X-From-UI': true },
		})
		.catch(buiFail)
		.then(function(response) {
			notifAll(response.data);
			// mandatory: we need to pass the response to the next function
			return response;
		})
		.then($scope.httpCallback)
		.then(function(response) {
			// status 201 means the grant was created, any other status code means
			// something went wrong (either critical or a warning)
			if (response.status === 201) {
				$scope.acl_backend = "placeholder";
				$scope.name = "";
				vm.grantAdd.name.$setPristine();
				vm.grantAdd.name.$setUntouched();
				vm.grantAdd.acl_backend.$setValidity('valid', ($scope.acl_backend != "placeholder"));
				if ($scope.dismiss) {
					$('#create-grant-modal').modal('toggle');
				}
			}
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
		if (data.members.indexOf(_me.name) !== -1) {
			row.className += ' success';
		}
		if (data.id === 'moderator') {
			row.className += ' warning';
		}
		if (data.id === 'admin') {
			row.className += ' danger';
		}
	},
	columns: [
		{
			data: 'id',
			render: function ( data, type, row ) {
				if (type === 'sort') {
					if (data === 'moderator') {
						// make the 'moderator' group appear last
						return 'zzzzzzzzzzzzzzzzzzzzzzzzzzz';
					}
					if (data === 'admin') {
						// make the 'admin' group appear last
						return 'zzzzzzzzzzzzzzzzzzzzzzzzzzzz';
					}
				}
				return data;
			},
		},
		{
			data: 'backends',
			render: function ( data, type, row ) {
				if (type === 'filter' || type === 'sort') {
					return data.join(',');
				}
				var ret = '';
				$.each(data, function(i, back) {
					ret += '<span class="label label-default">'+back+'</span>&nbsp;';
				});
				return ret;
			}
		},
		{
			data: null,
			render: function ( data, type, row ) {
				if (type === 'filter' || type === 'sort') {
					return data.roles.join(',');
				}
				var ret = '';
				$.each(data.roles, function(i, role) {
					inh = _groups[data.id][role+'_by'];
					if (inh.length > 0) {
						ret += '<span data-toggle="tooltip" data-placement="auto top" title=\'{{ _("Inherited by: ") }}'+inh.join(', ')+'\' data-html="true">';
					}
					ret += '<span class="label label-warning">'+(inh.length > 0 ? '<em>' : '')+role+(inh.length > 0 ? '</em>' : '')+'</span>';
					if (inh.length > 0) {
						ret += '</span>';
					}
					ret += '&nbsp;';
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
					return data.join(',');
				}
				var htmlGrants = '';
				var tooltipGrants = '';
				$.each(data, function(i, grant) {
					tooltipGrants += '<pre><code class="JSON">'+JSON.stringify(JSON.parse(grant), null, 4)+'</code></pre><br />';
					htmlGrants += '<kbd>'+$.trim(grant).substring(0, 30).split(' ').slice(0, -1).join(" ")+'...</kbd>&nbsp;';
				});
				return '<span data-toggle="tooltip" title=\''+tooltipGrants+'\' data-html="true" data-template=\'<div class="tooltip" role="tooltip"><div class="tooltip-arrow"></div><div class="tooltip-inner tooltip-custom"></div></div>\'>'+htmlGrants+'</span>';
			}
		},
		{
			data: null,
			orderable: false,
			render: function ( data, type, row ) {
				return '<button data-member="'+data.id+'" class="btn btn-xs btn-danger btn-delete-group" title="{{ _("Remove") }}"'+((data.id === 'moderator' || data.id === 'admin') ? 'disabled' : '')+'><i class="fa fa-trash" aria-hidden="true"></i></button>&nbsp;<button data-member="'+data.id+'" class="btn btn-xs btn-info btn-edit-group" title="{{ _("Edit") }}"><i class="fa fa-pencil" aria-hidden="true"></i></button>';
			}
		},
	],
});

_groups_table.on('draw.dt', function() {
	$('[data-toggle="tooltip"]').tooltip();
	$('[data-toggle="tooltip"]').on('inserted.bs.tooltip', function() {
		$('.tooltip-custom').each(function(i, elmt) {
			$(elmt).css('text-align', 'left');
		});
		$('pre code').each(function(i, block) {
			hljs.highlightBlock(block);
		});
	});
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
					return data.join(',');
				}
				var ret = '';
				$.each(data, function(i, back) {
					ret += '<span class="label label-default">'+back+'</span>&nbsp;';
				});
				return ret;
			}
		},
		{
			data: null,
			render: function ( data, type, row ) {
				if (type === 'filter' || type === 'sort') {
					return data.roles.join(',');
				}
				var ret = '';
				$.each(data.roles, function(i, role) {
					inh = _users[data.id][role+'_by'];
					if (inh.length > 0) {
						ret += '<span data-toggle="tooltip" data-placement="auto top" title=\'{{ _("Inherited by: ") }}'+inh.join(', ')+'\' data-html="true">';
					}
					ret += '<span class="label label-warning">'+(inh.length > 0 ? '<em>' : '')+role+(inh.length > 0 ? '</em>' : '')+'</span>';
					if (inh.length > 0) {
						ret += '</span>';
					}
					ret += '&nbsp;';
				});
				return ret;
			}
		},
		{
			data: 'groups',
			render: function ( data, type, row ) {
				if (type === 'filter' || type === 'sort') {
					var ret = [];
					$.each(data, function(i, group) {
						ret.push(group.name);
					});
					return ret.join(',');
				}
				var ret = '';
				$.each(data, function(i, group) {
					var inh = group.inherit;
					if (inh.length > 0) {
						ret += '<span data-toggle="tooltip" data-placement="auto top" title=\'{{ _("Inherited by: ") }}'+inh.join(', ')+'\' data-html="true">';
					}
					ret += '<span class="label label-primary">'+(inh.length > 0 ? '<em>' : '')+group.name+(inh.length > 0 ? '</em>' : '')+'</span>';
					if (inh.length > 0) {
						ret += '</span>';
					}
					ret += '&nbsp;';
				});
				return ret;
			}
		},
		{
			data: 'grants',
			render: function ( data, type, row ) {
				if (type === 'filter' || type === 'sort') {
					return data.join(',');
				}
				var htmlGrants = '';
				var tooltipGrants = '';
				$.each(data, function(i, grant) {
					var json = '';
					try {
						json = JSON.stringify(JSON.parse(grant), null, 4);
					} catch(e) {
						json = grant;
					}
					tooltipGrants += '<pre><code class="JSON">'+json+'</code></pre><br />';
					htmlGrants += '<kbd>'+$.trim(grant).substring(0, 30).split(' ').slice(0, -1).join(" ")+'...</kbd>&nbsp;';
				});
				return '<span data-toggle="tooltip" data-placement="auto top" title=\''+tooltipGrants+'\' data-html="true" data-template=\'<div class="tooltip" role="tooltip"><div class="tooltip-arrow"></div><div class="tooltip-inner tooltip-custom"></div></div>\'>'+htmlGrants+'</span>';
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
	$('[data-toggle="tooltip"]').on('inserted.bs.tooltip', function() {
		$('.tooltip-custom').each(function(i, elmt) {
			$(elmt).css('text-align', 'left');
		});
		$('pre code').each(function(i, block) {
			hljs.highlightBlock(block);
		});
	});
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
	var __promises = [];
	var t = $.getJSON('{{ url_for("api.acl_grants") }}').done(function (grants) {
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
					admin_by: [],
					moderator_by: [],
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
						_users[user.id]['admin_by'] = data.inherit;
					}
				});
				__promises.push(p);
				p = $.getJSON('{{ url_for("api.acl_is_moderator", member="") }}'+user.id).done(function (data) {
					if (data.moderator) {
						_users[user.id]['roles'].push('moderator');
						_users[user.id]['moderator_by'] = data.inherit;
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
			$.when.apply( $, __globals_promises ).always(function() {
				$.when.apply( $, __promises ).always(function() {
					_users_table.clear();
					_users_table.rows.add(_users_array).draw();
					_users_table.fixedHeader.adjust();
					$('#waiting-user-container').hide();
					$('#table-users-container').show();
				});
			});
		}
		$.when.apply( $, __top_promises ).done(function() {
			$.when.apply( $, __promises ).always(function() {
				_users_array = [];
				$.each(_users, function(key, value) {
					_users_array.push(value);
				});
				$.when.apply( $, __globals_promises ).always(function() {
					_users_table.clear();
					_users_table.rows.add(_users_array).draw();
					_users_table.fixedHeader.adjust();
					$('#waiting-user-container').hide();
					$('#table-users-container').show();
				});
			});
		});
	});
};

var _authorization_groups = function() {
	$('#waiting-group-container').show();
	$('#table-groups-container').hide();
	var __groupnames = [];
	var __top_promises = [];
	var __promises = [];
	var redraw = false;
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
					roles: [],
					admin_by: [],
					moderator_by: [],
					members: group.members,
					grants: [group.grant],
					raw: [group],
				};
				var p = $.getJSON('{{ url_for("api.acl_is_admin", member="") }}@'+group.id).done(function (data) {
					if (data.admin) {
						_groups[group.id]['roles'].push('admin');
						_groups[group.id]['admin_by'] = data.inherit;
					}
				});
				__promises.push(p);
				p = $.getJSON('{{ url_for("api.acl_is_moderator", member="") }}@'+group.id).done(function (data) {
					if (data.moderator) {
						_groups[group.id]['roles'].push('moderator');
						_groups[group.id]['moderator_by'] = data.inherit;
					}
				});
				__promises.push(p);
			}
		});
		_groups_array = [];
		$.each(_groups, function(key, value) {
			if (__groupnames.indexOf(key) == -1) {
				delete _groups[key];
				redraw = true;
			} else {
				_groups_array.push(value);
			}
		});
	});
	__top_promises.push(t);
	t = $.getJSON('{{ url_for("api.acl_moderators") }}').done(function (moderators) {
		if ('moderator' in _groups) {
			delete _groups['moderator'];
		}
		$.each(moderators, function(i, moderator) {
			__groupnames.push('moderator');
			if (_groups['moderator']) {
				if (_groups['moderator']['backends'].indexOf(moderator.backend) === -1) {
					_groups['moderator']['backends'].push(moderator.backend);
				}
				if (_groups['moderator']['grants'].indexOf(moderator.grant) === -1) {
					_groups['moderator']['grants'].push(moderator.grant);
				}
				if (_groups['moderator']['raw'].indexOf(moderator) === -1) {
					_groups['moderator']['raw'].push(moderator);
				}
				_groups['moderator']['members'] = _.uniq(_.concat(_groups['moderator']['members'], moderator.members));
			} else {
				_groups['moderator'] = {
					id: 'moderator',
					backends: [moderator.backend],
					roles: ['moderator'],
					admin_by: [],
					moderator_by: [],
					members: moderator.members,
					grants: [moderator.grant],
					raw: [moderator],
				};
			}
		});
	});
	__top_promises.push(t);
	t = $.getJSON('{{ url_for("api.acl_admins") }}').done(function (admins) {
		if ('admin' in _groups) {
			delete _groups['admin'];
		}
		$.each(admins, function(i, admin) {
			__groupnames.push('admin');
			if (_groups['admin']) {
				if (_groups['admin']['backends'].indexOf(admin.backend) === -1) {
					_groups['admin']['backends'].push(admin.backend);
				}
				if (_groups['admin']['raw'].indexOf(admin) === -1) {
					_groups['admin']['raw'].push(admin);
				}
				_groups['admin']['members'] = _.uniq(_.concat(_groups['admin']['members'], admin.members));
			} else {
				_groups['admin'] = {
					id: 'admin',
					backends: [admin.backend],
					roles: ['admin'],
					admin_by: [],
					admin_by: [],
					members: admin.members,
					grants: [],
					raw: [admin],
				};
			}
		});
	});
	__top_promises.push(t);
	if (redraw) {
		$.when.apply( $, __globals_promises ).always(function() {
			$.when.apply( $, __promises ).always(function() {
				_groups_table.clear();
				_groups_table.rows.add(_groups_array).draw();
				_groups_table.fixedHeader.adjust();
				$('#waiting-group-container').hide();
				$('#table-groups-container').show();
			});
		});
	}
	$.when.apply( $, __top_promises ).done(function() {
		$.when.apply( $, __promises ).always(function() {
			_groups_array = [];
			$.each(_groups, function(key, value) {
				_groups_array.push(value);
			});
			$.when.apply( $, __globals_promises ).always(function() {
				_groups_table.clear();
				_groups_table.rows.add(_groups_array).draw();
				_groups_table.fixedHeader.adjust();
				$('#waiting-group-container').hide();
				$('#table-groups-container').show();
			});
		});
	});
};

var _admin = function() {
	_authorization_users();
	_authorization_groups();
};

{{ macros.page_length('#table-users') }}
{{ macros.page_length('#table-groups') }}

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
		var is_enabled = _acl_backends[back]['del_grant'];
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
	if (user_id == _me.id) {
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
	var _delete_promises = [];
	$.each($('input[name=user_backend]'), function(i, elmt) {
		var e = $(elmt);
		if (e.is(':checked')) {
			var user_id = $(e).data('id');
			var backend = $(e).data('backend');
			var user = _users[user_id];
			if (user['roles'].indexOf('admin') !== -1) {
				$.ajax({
					url: "{{ url_for('api.acl_admin') }}",
					data: {
						memberName: user_id,
						backendName: backend,
					},
					type: 'DELETE',
					headers: { 'X-From-UI': true },
				}).done(function(data) {
					notifAll(data);
				}).fail(buiFail);
			}
			if (user['roles'].indexOf('moderator') !== -1) {
				$.ajax({
					url: "{{ url_for('api.acl_moderator') }}",
					data: {
						memberName: user_id,
						backendName: backend,
					},
					type: 'DELETE',
					headers: { 'X-From-UI': true },
				}).done(function(data) {
					notifAll(data);
				}).fail(buiFail);
			}
			var d = $.ajax({
				url: "{{ url_for('api.acl_grants', name='') }}"+user_id,
				data: {
					backend: backend,
				},
				type: 'DELETE',
				headers: { 'X-From-UI': true },
			}).done(function(data) {
				notifAll(data);
			}).fail(buiFail);
			_delete_promises.push(d);
		}
	});
	$.when.apply( $, _delete_promises ).done(function() {
		_authorization_users();
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
		is_enabled = _acl_backends[back]['mod_grant'];
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
	location = "{{ url_for('view.admin_grant_authorization', grant='') }}"+$('#edit_backend').data('id')+'?backend='+$('#edit_backend option:selected').text();
});

/* Delete group */
var _remove_group_selected = 0;
$( document ).on('click', '.btn-delete-group', function(e) {
	var group_id = $(this).data('member');
	var group = _groups[group_id];
	var content = '<legend>{{ _("Please select the backend(s) from which to remove the group:") }}</legend>';
	$.each(group['backends'], function(i, back) {
		var disabled_legend = '{{ _("The backend does not support group removal") }}';
		var disabled = 'disabled title="'+disabled_legend+'"';
		var is_enabled = _acl_backends[back]['del_group'];
		content += '<div class="checkbox"><label><input type="checkbox" name="group_backend" data-id="'+group_id+'" data-backend="'+back+'" '+(is_enabled?'':disabled)+'>'+back+(is_enabled?'':' <em>('+disabled_legend+')</em>')+'</label></div>';
	});
	/* disable submit button while we did not select a backend */
	$('#perform-group-delete').prop('disabled', true);
	$('#delete-group-details').html(content);
	$('#delete-group-modal').modal('toggle');
});
$( document ).on('change', 'input[name=group_backend]', function(e) {
	if ($(this).is(':checked')) {
		_remove_group_selected++;
	} else {
		_remove_group_selected--;
	}
	if (_remove_group_selected > 0) {
		$('#perform-group-delete').prop('disabled', false);
	} else {
		$('#perform-group-delete').prop('disabled', true);
	}
});
$('#perform-group-delete').on('click', function(e) {
	var _delete_promises = [];
	$.each($('input[name=group_backend]'), function(i, elmt) {
		var e = $(elmt);
		if (e.is(':checked')) {
			var d = $.ajax({
				url: "{{ url_for('api.acl_groups', name='') }}"+$(e).data('id'),
				data: {
					backend: $(e).data('backend'),
				},
				type: 'DELETE',
				headers: { 'X-From-UI': true },
			}).done(function(data) {
				notifAll(data);
			}).fail(buiFail);
			_delete_promises.push(d);
		}
	});
	$.when.apply( $, _delete_promises ).done(function() {
		_authorization_groups();
	});
});

/* Edit group */
$( document ).on('click', '.btn-edit-group', function(e) {
	var group_id = $(this).data('member');
	var group = _groups[group_id];
	var content = '<legend>{{ _("Please select the backend from which to edit the user from:") }}</legend>';
	content += '<div class="form-group"><label for="edit_group_backend" class="col-lg-2 control-label">Backend</label>';
	content += '<div class="col-lg-10"><select class="form-control" id="edit_group_backend" name="edit_group_backend" data-id="'+group_id+'"><option disabled selected value="placeholder">'+'{{ _("Please select a backend") }}'+'</option>';
	$.each(group['backends'], function(i, back) {
		is_enabled = _acl_backends[back]['mod_group'];
		content += '<option'+(is_enabled?'':' disabled')+'>'+back+'</option>';
	});
	content += '</select></div></div>';
	$('#perform-group-edit').prop('disabled', true);
	$('#edit-group-details').html(content);
	$('#edit-group-modal').modal('toggle');
});
$( document ).on('change', '#edit_group_backend', function(e) {
	if ($('#edit_group_backend option:selected').val() != 'placeholder') {
		$('#perform-group-edit').prop('disabled', false);
	}
});
$('#perform-group-edit').on('click', function(e) {
	location = "{{ url_for('view.admin_group_authorization', group='') }}"+$('#edit_group_backend').data('id')+'?backend='+$('#edit_group_backend option:selected').text();
});
