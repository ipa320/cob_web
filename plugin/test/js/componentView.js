var componentViewCode = '\<h1>Component "<span class="ph_comp-name"></span>"</h1><div class="actionsView">\
	<div class="componentView">\
		<div class="componentView-topBar componentView-name"><span class="ui-icon ui-icon-triangle-1-s" />Control Panel</div>\
		<div class="componentView-content" >\
			<div class="componentView-buttons">\
				<div class="log-buttons">\
					<input type="checkbox" class="showLog-button" id="showLog" /><label for="showLog">ShowLog</label>\
				</div>\
				<div class="actions-buttons"></div>\
			</div>\
			<div><table class="componentView-summary" cellspacing="0" cellpadding="0">\
			</table></div>\
		</div>\
		<div class="logView"></div>\
	</div>';
//<a href="javascript:application.editComponent()" class="edit-button">Edit</a><h1>Component "<span class="ph_comp-name"></span>"</h1><div class="actionsView">

$.fn.renderComponentView = function(component, components, options) {
	if (!(component instanceof Component))
		throw new Error("Argument must be an instance of Component");

	// Every component must have a main action
	var mainAction = component.getMainAction();

	// clear the html
	this.addClass("componentView");
	this.html(componentViewCode);

	// Add the buttons for the main action
	var buttons = this.find('.componentView-buttons');
	buttons.prepend(createActionButtons(mainAction));
	

	// set the values that stay forever
	this.find(".ph_comp-name").text(component.name);
	
	// create the edit-button
	this.find(".edit-button").button({ icons: {primary: 'ui-icon-scissors'} })


	// Create log buttonset
	this.find(".log-buttons").buttonset();
	var showLogButton = this.find(".showLog-button");
	showLogButton.button({ 'icons': {primary: "ui-icon-document-b" } });
	
	// hide the logView at startup
	this.find(".logView").hide()
	

	// render the buttons
	var actionsButtons = this.find(".actions-buttons");
	for (i in component.actions) {
		 // main action was added already
		 if (component.actions[i] != mainAction)
			actionsButtons.append(createActionButtons(component.actions[i]));
	}
	
	// set the actions for the log Button
	var logView = this.find(".logView");
	showLogButton.click(function() { 
		if (!logView.is(":visible")) {
			var setTextCallback = function(html) {
				logView.setLogContent(html);
			};
			
			logView.show();
			logView.renderLogView(component, function(id) { application.loadLog(id, setTextCallback); });
		}
		else {
			logView.hide();
		}
	});
	
	this.updateComponentView(component, components, options);
};

$.fn.updateComponentView = function(component, components, options) {

	if (!(component instanceof Component))
		throw new Error("Argument must be an instance of Component");

	
	var defaultOptions = {'disabled': screenManager.isLockedLocation()};
	options = $.extend(defaultOptions, options);

	// clear the summary and rerender it
	var table = this.find('.componentView-summary');
	table.html('');
	
	
	// Render Description
	var descriptions = {}

	// Dependency-Array contains a list of object / target relations
	var dependencies = []
	
	// update all the actions
	for (i in component.actions) {
		var action = component.actions[i];
		var id = action.id;
		if (action.description)
			descriptions[action.name] = action.description;
		
		// update buttons
		var startButtons = this.find("#action-buttons-" + id + " .start-buttons");
		var stopButtons  = this.find("#action-buttons-" + id + " .stop-buttons");
		if (action.isActive()) {
			// need to show start / hide stop buttons ?
			if (startButtons.is(':visible')) {
				startButtons.hide();
				stopButtons.show();
				// the ui-state-hover is not removed properly on a mouseout sometimes
				stopButtons.find('.stop-button', '.kill-button').removeClass('ui-state-hover');
			}
		}
		else {
			if (stopButtons.is(':visible')) {
				startButtons.show();
				startButtons.find('.start-button').removeClass('ui-state-hover');
				stopButtons.hide()
			}
		}

		// append all dependencies to the array
		for (j in action.dependencies)
		    dependencies.push({'object': action.id, 'target': action.dependencies[j]});

		
		// disable the start buton if either the option is set or the action cannot be started at all
		startButtons.find("a").button({'disabled': !action.canStart() || options['disabled']});
		
		// only disable stop button if the action cannot be stopped
		stopButtons.find(".stop-button").button({'disabled': !action.canStop() || options['disabled']});
	}
	// those buttons do not depend on any action
	this.find(".kill-button").button({'disabled': options['disabled']});
	this.find(".log-buttons input").button({'disabled': options['disabled']});
	
	renderDescription(table, descriptions);
	renderDependencies(table, dependencies, component);
	
	renderFrames(this, component.actions);

	// update the logview if visible
	var logView = this.find(".logView");
	if (logView.is(':visible'))
	    logView.updateLogView(component);
};

function renderDescription(container, descriptions)
{
	var isFirst = true;
	var i = 0;
	
	for (name in descriptions) {
		var tr = $(document.createElement("tr"));
		var myClass = "";
		
		if (isFirst) {
			tr.append("<th>Description: </th>");
			myClass = "ph_action-desc";
		}
		else {
			tr.append("<th></th>");
			myClass = "ph_action-hl ph_action-desc";
		}
		
		tr.append('<td class="' + myClass + '"><span class="name">' + name + ' &raquo; </span>' + descriptions[name] + '</td>');
					
		isFirst = false;
		container.append(tr);
	}
}

function renderDependencies(container, dependencies, component)
{	
	if (dependencies.length > 0) {
		var tr = $(document.createElement('tr')).addClass("dependencies");
		
		var html = '';
		for (i in dependencies) {
			html += '<div>';
			
			var objectId = dependencies[i].object;
			var targetId = dependencies[i].target;
			if (!component.hasAction(objectId) || !component.hasAction(targetId))
				throw new Error('[ComponentView] Dependency-Object "' + objectId + '" or target "' + targetId  + '" not found');
			object = component.getAction(objectId);
			target = component.getAction(targetId);

			var spanClass="ui-icon ui-icon-component ";
			var aClass="";
			if(target.isActive()) {
			    spanClass += "ui-icon-component-action-on";
			    aClass = "running";
			}
			else {
			    spanClass += "ui-icon-component-action-off";
			    aClass = "notRunning";
			}

			html += '<span class="' + spanClass + '"></span><a href="#" class="' + aClass + '">' + object.name + " &raquo; " + target.name + '</a></div>';
		}
		
		tr.append('<th>Dependencies:</th><td class="ph_action-dep">' + html + '</td>')
		container.append(tr);
	}

}

function createActionButtons(action, appendName)
{
	var startText = 'Run';
	var stopText  = 'Stop';
	var killText  = 'Kill';
	
	if (appendName !== false) {
		startText += ' ' + action.name;
		stopText  += ' ' + action.name;
		killText  += ' ' + action.name;
	}
	
	// create divs based on the id, not the name because of special chars
	var div = $(document.createElement('div')).attr('id', 'action-buttons-' + action.id);
	var startButtons = $(document.createElement('div')).addClass('start-buttons');
	var stopButtons = $(document.createElement('div')).addClass('stop-buttons');
	div.append(startButtons);
	div.append(stopButtons);

	var startButton = $(document.createElement('a')).attr('href', '#').addClass('start-button').text(startText);
	var stopButton  = $(document.createElement('a')).attr('href', '#').addClass('stop-button').text(stopText);
	var killButton  = $(document.createElement('a')).attr('href', '#').addClass('kill-button').text(killText);
	startButtons.append(startButton);
	stopButtons.append(stopButton);
	stopButtons.append(killButton);

	startButtons.buttonset();
	stopButtons.buttonset();

	startButton.button({ icons: {primary: "ui-icon-play"} });
	stopButton.button({ icons: {primary: "ui-icon-stop" } });
	killButton.button({ icons: {primary: "ui-icon-notice"} });
	
	
	// set the buttons' actions
	startButton.click(function() { application.startAction(action.id, action.compId); return false; });
	stopButton.click(function() { application.stopAction(action.id, action.compId); return false; });
	killButton.click(function() { application.killAction(action.id, action.compId); return false; });
	
		
	return div;
}

function renderFrames(container, actions)
{
	for (actionId in actions) {
		action = actions[actionId];
		var actionClass = "action-" + action.id;
		var renderedAlready = container.find("." + actionClass).size() > 0;
		
		if (action.url.length && action.isActive() && !renderedAlready)
			$('<div class="iframe" />').addClass(actionClass).append(action.iframe).appendTo(container);
		if (!action.isActive() && renderedAlready)
			$("." + actionClass).remove();
			
	}
}
