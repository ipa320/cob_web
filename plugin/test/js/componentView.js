var componentViewCode = '<h1>Component "<span class="ph_comp-name"></span>"</h1><div class="actionsView"></div>';

$.fn.renderComponentView = function(component, options) {
	if (!(component instanceof Component))
		throw new Error("Argument must be an instance of Component");

	// clear the html
	this.html('');

	this.addClass("componentView");
	this.append(componentViewCode);

	actionsView = this.find(".actionsView");
	for (i in component.actions) {
		div = $(document.createElement("div"))
		actionsView.append(div);
		div.attr("id", "action-" + component.actions[i].id);
		div.renderActionView(component.actions[i]);
	}

	// set the values that stay forever
	this.find(".ph_comp-name").text(component.name);

	this.updateComponentView(component, options, true);
};

$.fn.updateComponentView = function(component, options, force) {

	if (!(component instanceof Component))
		throw new Error("Argument must be an instance of Component");

	// update all the actions
	for (i in component.actions) {
		actionView = this.find("#action-" + component.actions[i].id);
		if (actionView.size() != 1)
			throw new Error("Inconsistent Component-HTML");

		actionView.updateActionView(component.actions[i], null, force);
	}
};
