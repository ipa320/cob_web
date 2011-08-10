var componentEditViewCode = '<h1>Component "<span class="ph_edit_comp-name"></span>"</h1><div class="actionEditsView"></div><a href="#" class="edit-finished-button">Done</a><a class="actionEditCreateNewAction" href="#">Create new action</a>';

$.fn.renderComponentEditView = function(component, options) {
	if (!(component instanceof Component))
		throw new Error("Argument must be an instance of Component");

	// clear the html
	this.addClass("componentEditView");
	this.html(componentEditViewCode);

	actionEditsView = this.find(".actionEditsView");
	updateView = function() {
	    actionEditsView.html('');
	    for (i in component.actions) {
		var div = $(document.createElement("div"));
		var action = component.actions[i];
		var isMain = component.getMainAction() == action;

		actionEditsView.append(div);
		div.attr("id", "actionEdit-" + action.id);		
		div.renderActionEditView(action, component, isMain);
	    }
	}
	updateView();

	// set the values that stay forever
	name = this.find(".ph_edit_comp-name");
	name.text(component.name);
	
	// create the edit-button
	but = this.find(".edit-finished-button");
	but.click(function() { application.saveComponent(component); });
	but.button({ icons: {primary: 'ui-icon-check'} });

	// create the action-button
	var newActionButton = this.find('.actionEditCreateNewAction').button();
	newActionButton.click(function() {
	    var emptyAction = new Action(application.getUniqueTemporaryId(), '', component.id);
	    console.log(emptyAction);
	    component.addAction(emptyAction);
	    updateView();
        });
		
	
};
