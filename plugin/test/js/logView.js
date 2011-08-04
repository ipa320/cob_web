var logViewCode = '<div class="componentView-content" >\
		<div class="componentView-buttons">\
			<a href="#" class="refreshLog-button">Refresh</a>\
		</div>\
		<div class="logNavigation"></ul></div>\
		<div class="logContent">Loading ...</div>\
		<div></div>\
	</div>';

$.fn.renderLogView = function(component, callbackOnClick)
{
	this.html(logViewCode);
	
	this.find(".refreshLog-button").button( {'icons': {'primary': 'ui-icon-refresh' }});
	
	var logContent = this.find(".logContent");
	var navigation = this.find(".logNavigation");
	var ul = $('<ul class="navigation"></ul>');
	
	for (actionId in component.actions) {
		var action = component.actions[actionId];
		var icon;
		if (action.isActive())
			icon = "ui-icon-menu-component-on";
		else
			icon = "ui-icon-menu-component-off";
			
		var selected = "";
		if (component.getMainAction().id == actionId)
			selected = "actionSelected";

		var li = $('<li><span class="ui-icon ' + icon + '"></span><span class="actionName ' + selected + '">' + component.actions[actionId].name + "</span></li>");
		ul.append(li);
		li.click(function() { callbackOnClick(action.id) });
	}
	navigation.html(ul);
	
	this.setLogContent = function(html) {
		logContent.html("<pre>" + html + "</pre>");
	}
}
