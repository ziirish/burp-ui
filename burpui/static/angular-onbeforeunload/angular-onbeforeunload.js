angular.module('angular-onbeforeunload', []);
angular.module("angular-onbeforeunload").directive("onbeforeunload", ["$window", "$filter", function ($window, $filter) {
	"use strict";
	var unloadtext, forms = [];

	function handleOnbeforeUnload() {
		var i, form, isDirty = false;

		for (i = 0; i < forms.length; i++) {
			form = forms[i];

			if (form.scope[form.name].$dirty || form.scope.changed) {
				isDirty = true;
				break;
			}
		}

		if (isDirty) {
			return unloadtext;
		} else {
			return undefined;
		}
	}

	return function ($scope, $element) {
		if ($element[0].localName !== 'form') {
			throw new Error("onbeforeunload directive must only be set on a angularjs form!");
		}

		forms.push({
			"name": $element[0].name,
			"scope": $scope
		});

		$window.onbeforeunload = handleOnbeforeUnload;

		try {
			unloadtext = $filter("translate")("onbeforeunload");
		} catch (err) {
			unloadtext = "";
		}
	};
}]);
