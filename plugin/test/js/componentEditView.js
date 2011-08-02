var componentEditViewCode = '<a href="#" class="edit-finished-button">Done</a><h1>Component "<span class="ph_edit_comp-name"></span>"</h1><div class="actionEditsView"></div>';

$.fn.renderComponentEditView = function(component, components, options) {
	if (!(component instanceof Component))
		throw new Error("Argument must be an instance of Component");

	// clear the html
	this.addClass("componentEditView");
	this.html(componentEditViewCode);

	actionEditsView = this.find(".actionEditsView");
	for (i in component.actions) {
		var div = $(document.createElement("div"));
		var action = component.actions[i];
		var isMain = component.getMainAction() == action;

		actionEditsView.append(div);
		div.attr("id", "actionEdit-" + action.id);		
		div.renderActionEditView(action, component, components, isMain);
	}

	// set the values that stay forever
	name = this.find(".ph_edit_comp-name");
	name.text(component.name);
	
	// create the edit-button
	but = this.find(".edit-finished-button");
	but.click(function() { application.saveComponent(component); });
	but.button({ icons: {primary: 'ui-icon-check'} })
};
