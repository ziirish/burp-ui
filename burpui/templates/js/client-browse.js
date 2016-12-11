
/***
 * Here is our tree to browse a specific backup
 * The tree is first initialized with the 'root' part of the backup.
 * JSON example:
 * [
 *   {
 *     "name": "/",
 *     "parent": "",
 *     "type": "d"
 *   }
 * ]
 * This JSON is then parsed into another one to initialize our tree.
 * Each 'directory' is expandable.
 * A new JSON is returned for each one of them on-demand.
 * JSON output:
 * [
 *   {
 *     "name": "etc",
 *     "parent": "/",
 *     "type": "d"
 *   },
 *   {
 *     "name": "home",
 *     "parent": "/",
 *     "type": "d"
 *   }
 * ]
 */
$( document ).ready(function() {
	var fixNeeded = false;

	var treeCollapsed = function() {
		var btn = $("#btn-expand-collapse-tree");
		btn.data('collapsed', true);
		btn.html('<i class="fa fa-expand" aria-hidden="true"></i>&nbsp;{{ _("Expand tree") }}</button>');
	};

	$('[data-toggle="tooltip"]').tooltip();

	$("#tree").fancytree({
		checkbox: true,
		selectMode: 3,
		extensions: ["glyph", "table", "gridnav", "filter"],
		glyph: {
			map: {
				doc: "glyphicon glyphicon-file",
				docOpen: "glyphicon glyphicon-file",
				checkbox: "glyphicon glyphicon-unchecked",
				checkboxSelected: "glyphicon glyphicon-check",
				checkboxUnknown: "glyphicon glyphicon-share",
				dragHelper: "glyphicon glyphicon-play",
				dropMarker: "glyphicon glyphicon-arrow-right",
				error: "glyphicon glyphicon-warning-sign",
				expanderClosed: "glyphicon glyphicon-plus-sign",
				expanderLazy: "glyphicon glyphicon-plus-sign",
				// expanderLazy: "glyphicon glyphicon-expand",
				expanderOpen: "glyphicon glyphicon-minus-sign",
				// expanderOpen: "glyphicon glyphicon-collapse-down",
				folder: "glyphicon glyphicon-folder-close",
				folderOpen: "glyphicon glyphicon-folder-open",
				loading: "glyphicon glyphicon-refresh glyphicon-spin"
			}
		},
		source: function() { 
			{% if edit and edit.found -%}
			url = '{{ url_for("api.client_tree", name=cname, backup=nbackup, server=server, root=edit.roots, recursive=True, selected=True) }}';
			{% else -%}
			url = '{{ url_for("api.client_tree", name=cname, backup=nbackup, server=server) }}';
			{% endif -%}
			return $.getJSON(url, function(data) {
				$("#waiting-container").hide();
				$("#tree-container").show();
				return data;
			})
			.fail(myFail);
		},
		lazyLoad: function(event, data) {
			fixNeeded = true;
			var node = data.node;
			p = node.key;
			if (p !== "/") p += '/';
			p = encodeURIComponent(p);
			data.result = { url: '{{ url_for("api.client_tree", name=cname, backup=nbackup, server=server) }}?root='+p, debugDelay: 500 };
		},
		loadChildren: function(event, data) {
			// This is a hack to select all children of a selected node after
			// lazy loading.
			// The 'fixNeeded' flag is here to ensure we apply the fix only after
			// a lazy loading.
			if (fixNeeded) {
				data.node.fixSelection3AfterClick();
			}
			// TODO: make it recursively loadable
			/*
			data.node.visit(function(subNode){
				if( subNode.isUndefined() && subNode.isExpanded() ) {
					subNode.load();
				}
			});
			*/
		},
		scrollParent: $(window),
		renderColumns: function(event, data) {
			var node = data.node;
			$tdList = $(node.tr).find(">td");

			$tdList.eq(1).text(node.data.mode);
			$tdList.eq(2).text(node.data.uid);
			$tdList.eq(3).text(node.data.gid);
			$tdList.eq(4).text(node.data.size);
			$tdList.eq(5).text(node.data.date);
		},
		select: function(event, data) {
			toggleRestorationForms(data.tree);
		},
		collapse: function(event, data) {
			if (!data.node.data.parent) {
				treeCollapsed();
			}
		},
		expand: function(event, data) {
			var btn = $("#btn-expand-collapse-tree");
			if (btn.data('collapsed')) {
				btn.data('collapsed', false);
				btn.html('<i class="fa fa-compress" aria-hidden="true"></i>&nbsp;{{ _("Colapse tree") }}');
			}
		}
	});

	var tree = $("#tree").fancytree("getTree");

	var toggleRestorationForms = function(my_tree) {
		var s = my_tree.getSelectedNodes();
		if (s.length > 0) {
			$("#restore-form").show();
			$("#server-initiated-form").show();
			v = [];
			$.each(s, function(i, n) {
				v.push({key: n.key, folder: n.folder});
			});
			r = {restore:v};
			$("input[name=list]").val(JSON.stringify(r));
			$("input[name=list-sc]").val(JSON.stringify(r));
		} else {
			$("#restore-form").hide();
			$("#server-initiated-form").hide();
			$("input[name=list]").val('');
			$("input[name=list-sc]").val('');
		}
	};

	toggleRestorationForms(tree);

	$("input[name=search-tree]").keyup(function(e){
		var n,
		leavesOnly = $("#leavesOnly").is(":checked"),
		match = $(this).val();

		if(e && e.which === $.ui.keyCode.ESCAPE || $.trim(match) === "") {
			$("#btnResetSearch").click();
			return;
		}
		if($("#regex").is(":checked")) {
			// Pass function to perform match
			n = tree.filterNodes(function(node) {
				return new RegExp(match, "i").test(node.title);
			}, leavesOnly);
		} else {
			// Pass a string to perform case insensitive matching
			n = tree.filterNodes(match, leavesOnly);
		}
		$("#btnResetSearch").attr("disabled", false);
		$("span#matches").text("(" + n + " matches)");
	});

	$("#btnResetSearch").click(function(e){
		$("input[name=search-tree]").val("");
		$("span#matches").text("");
		tree.clearFilter();
		$("#btnResetSearch").attr("disabled", true);
	}).attr("disabled", true);

	$("input#hideMode").change(function(e){
		tree.options.filter.mode = $(this).is(":checked") ? "hide" : "dimm";
		tree.clearFilter();
		$("input[name=search-tree]").keyup();
		e.stopPropagation();
	});
	$("input#leavesOnly").change(function(e){
		tree.clearFilter();
		$("input[name=search-tree]").keyup();
		e.stopPropagation();
	});
	$("input#regex").change(function(e){
		tree.clearFilter();
		$("input[name=search-tree]").keyup();
		e.stopPropagation();
	});

	$("#form-restore").on('submit', function(e) {
		var $preparingFileModal = $("#restore-modal");
		
		$preparingFileModal.modal('toggle');

		{% if config.WITH_CELERY -%}
		var check_task = function(task_id) {
			$.getJSON('{{ url_for("api.async_restore_status", task_id="") }}'+task_id)
				.done(function(data) {
					if (data.state != 'SUCCESS') {
						setTimeout(function() {
							check_task(task_id);
						}, 2000);
					} else {
						$.fileDownload(data.location, {
							successCallback: function (url) {
								$preparingFileModal.modal('hide');
							},
							failCallback: function (responseHtml, url) {
								$preparingFileModal.modal('hide');
								if (responseHtml == 'encrypted') {
									msg = 'The backup seems encrypted, please provide the encryption key in the \'Download options\' form.';
								} else {
									msg = responseHtml;
								}
								$("#error-response").empty().html(msg);
								$("#error-modal").modal('toggle');
							},
						});
					}
				})
				.fail(function(xhr, stat, err) {
					$preparingFileModal.modal('hide');
					if (xhr.status != 502) {
						myFail(xhr, stat, err);
					}
					if ('responseJSON' in xhr && 'message' in xhr.responseJSON) {
						resp = xhr.responseJSON.message;
					} else if ('responseText' in xhr) {
						resp = xhr.responseText;
					} else {
						return false;
					}
					if (resp == 'encrypted') {
						msg = 'The backup seems encrypted, please provide the encryption key in the \'Download options\' form.';
					} else {
						msg = resp;
					}
					$("#error-response").empty().html(msg);
					$("#error-modal").modal('toggle');
				});
		};
		$.post($(this).prop('action'), $(this).serialize())
			.done(function(data) {
				check_task(data.id);
			})
			.fail(function(xhr, stat, err) {
				$preparingFileModal.modal('hide');
				myFail(xhr, stat, err);
			});
		{% else -%}
		$.fileDownload($(this).prop('action'), {
			successCallback: function (url) {
				$preparingFileModal.modal('hide');
			},
			failCallback: function (responseHtml, url) {
				$preparingFileModal.modal('hide');
				if (responseHtml == 'encrypted') {
					msg = 'The backup seems encrypted, please provide the encryption key in the \'Download options\' form.';
				} else {
					msg = responseHtml;
				}
				$("#error-response").empty().html(msg);
				$("#error-modal").modal('toggle');
			},
			httpMethod: "POST",
			data: $(this).serialize()
		});
		{% endif -%}
		e.preventDefault();
		return false;
	});
	$("#form-server-initiated").on('submit', function(e) {
		e.preventDefault();

		var form = $(this);
		/* FIXME: quick-fix cause i did not manage to get the form action */
		var url = "{{ url_for('api.server_restore', name=cname, backup=nbackup, server=server) }}";
		$.ajax({
			url: url,
			headers: { 'X-From-UI': true },
			type: 'PUT',
			data: form.serialize(),
			dataType: 'text json',
		})
		.fail(myFail)
		.done(function(data) {
			notifAll(data);
		});

		return false;
	});

	$("#btn-load-all-tree").on('click', function() {
		var btn = $("#btn-load-all-tree");
		btn.prop('disabled', true);
		btn.html('<i class="fa fa-spinner fa-pulse fa-fw"></i>&nbsp;{{ _("Loading") }}');
		var load_all_tree = function(url) {
			$.get(url)
				.fail(myFail)
				.done(function(data) {
					tree.reload(data);
					btn.html('<i class="fa fa-check-square-o" aria-hidden="true"></i>&nbsp;{{ _("Nodes loaded") }}');
					$('#'+btn.attr('aria-describedby')).remove();
					btn.blur();
				});
		};
		{% if config.WITH_CELERY -%}
		var url = "{{ url_for('api.async_client_tree_all', name=cname, backup=nbackup, server=server) }}";
		var task_status = function(task_id) {
			$.getJSON('{{ url_for("api.async_browse_status", task_id="") }}'+task_id)
				.fail(myFail)
				.done(function(data) {
					if (data.state != 'SUCCESS') {
						setTimeout(function() {
							task_status(task_id);
						}, 2000);
					} else {
						load_all_tree(data.location);
					}
				});
		};
		$.post(url)
			.fail(myFail)
			.done(function(data) {
				task_status(data.id);
			});
		{% else -%}
		var url = "{{ url_for('api.client_tree_all', name=cname, backup=nbackup, server=server) }}";
		load_all_tree(url);
		{% endif -%}
	});
	$("#btn-expand-collapse-tree").on('click', function() {
		var btn = $("#btn-expand-collapse-tree");
		var collapsed = btn.data('collapsed');
		tree.getRootNode().visit(function(node) {
			if (collapsed) {
				if (node.lazy && !node.children && node.title != "/") {
					return 'skip';
				}
			}
			node.setExpanded(collapsed);
		});
		if (!collapsed) {
			treeCollapsed();
		}
	});
	$("#btn-clear").on('click', function() {
		tree.visit(function(node){
			node.setSelected(false);
		});
		return false;
	});
	$(".dropdown-menu label, .dropdown-menu input, .dropdown-menu li").click(function(e) {
		e.stopPropagation();
	});

	{% if encrypted -%}
	$("#perform").attr("disabled", "disabled");
	$("#pass").on('change', function() {
		if ($(this).val().length > 0) {
			$("#perform").removeAttr("disabled");
			$("#notice").hide();
		} else {
			$("#perform").attr("disabled", "disabled");
			$("#notice").show();
		}
	});
	{% endif -%}

	{% if edit -%}
	$('#btn-cancel-restore').on('click', function(e) {
		{% if edit.orig_client -%}
		url = '{{ url_for("api.is_server_restore", name=edit.to, server=server) }}';
		{% else -%}
		url = '{{ url_for("api.is_server_restore", name=cname, server=server) }}';
		{% endif -%}
		$.ajax({
			url: url,
			headers: { 'X-From-UI': true },
			type: 'DELETE'
		}).done(function(data) {
			notifAll(data);
			if (data[0] == 0) {
				$('#btn-cancel-restore').hide();
			}
		}).fail(myFail);
	});
	{% endif -%}
});

var app = angular.module('MainApp', ['ngSanitize']);

app.controller('BrowseCtrl', function($scope, $http) {
	// var tree = $("#tree").fancytree("getTree");
	$scope.sc_restore = {};
	$scope.load_all = false;
	{% if edit and edit.orig_client -%}
	$scope.sc_restore.to = '{{ edit.to }}';
	{% endif -%}
	$http.get('{{ url_for("api.clients_all", server=server) }}', { headers: { 'X-From-UI': true } })
		.then(function(response) {
			$scope.sc_restore.clients = response.data;
		}, function(response) {
			notifAll(response.data);
		});
	$http.get('{{ url_for("api.setting_options", server=server) }}', { headers: { 'X-From-UI': true } })
		.then(function(response) {
			$scope.sc_restore.enabled = response.data.server_can_restore;
			$scope.load_all = response.data.batch_list_supported;
		}, function(response) {
			notifAll(response.data);
		});
});
