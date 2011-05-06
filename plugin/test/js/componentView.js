var componentViewCode = '<h1>Componente "<span class="ph_comp-title"></span>"</h1><div class="actionsView"></div>';

$.fn.componentView = function(component, options) {
	if (! component instanceof Component)
		throw new Error("Argument must be an instance of Component");

	if (! this.hasClass("componentView")) {
		this.addClass("componentView");
		this.append(componentViewCode);

		actionsView = this.find(".actionsView");
		for (i in component.actions) {
			div = $(document.createElement("div"))
			actionsView.append(div);
			div.attr("id", "action-" + component.actions[i].id);
			div.actionView(component.actions[i]);
		}
	}

	this.updateComponentView(component, options);
};

$.fn.updateComponentView = function(component, options, force) {

	if (force === true || !this.data("lastRefresh") || this.data("lastRefresh") < component.lastChange) {
	
		// update the component itself
		this.find(".ph_comp-title").text(component.title);

		// update all the actions
		for (i in component.actions) {
			actionView = this.find("#action-" + component.actions[i].id);
			if (actionView.size() != 1)
				throw new Error("Inconsistent Component-HTML");

			actionView.updateActionView(component.actions[i]);
		}

		this.data("lastRefresh", new Date().getTime());
	}
};
