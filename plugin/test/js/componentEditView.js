var componentEditViewCode = '<a href="#" class="edit-finished-button">Done</a><h1>Component "<input type="text" class="ph_edit_comp-name"></span>"</h1><div class="actionsView"></div>';

$.fn.renderComponentEditView = function(component, components, options) {
	if (!(component instanceof Component))
		throw new Error("Argument must be an instance of Component");

	// clear the html
	this.html('');

	this.addClass("componentEditView");
	this.append(componentEditViewCode);

	actionsView = this.find(".actionsView");
/*	for (i in component.actions) {
		div = $(document.createElement("div"))
		actionsView.append(div);
		div.attr("id", "action-" + component.actions[i].id);
		div.renderActionView(component.actions[i], components);
	}*/

	// set the values that stay forever
	this.find(".ph_edit_comp-name").val(component.name);
	
	// create the edit-button
	but = this.find(".edit-finished-button");
	but.attr('href', 'javascript:application.select(' + component.id + ')');
	but.button({ icons: {primary: 'ui-icon-check'} })

	//this.updateComponentView(component, components, options, true);
};

$.fn.updateComponentView = function(component, components, options, force) {

	if (!(component instanceof Component))
		throw new Error("Argument must be an instance of Component");

	// update all the actions
	for (i in component.actions) {
		actionView = this.find("#action-" + component.actions[i].id);
		if (actionView.size() != 1)
			throw new Error("Inconsistent Component-HTML");

		actionView.updateActionView(component.actions[i], components, options, force);
	}
};
