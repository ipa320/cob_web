var componentViewCode = '\<h1>Component "<span class="ph_comp-name"></span>"</h1><div class="actionsView">\
	<div class="componentView">\
		<div class="componentView-topBar componentView-name"><span class="ui-icon ui-icon-triangle-1-s" />PH_COMP-NAME</div>\
		<div class="componentView-content" >\
			<div class="componentView-buttons">\
				<div class="log-buttons">\
					<a href="#" class="showLog-button">ShowLog</a>\
					<a href="#" class="refreshLog-button">Refresh</a>\
				</div>\
				<div class="actions-buttons"></div>\
			</div>\
			<div><table class="componentView-summary" cellspacing="0" cellpadding="0">\
			</table></div>\
		</div>\
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
	this.find(".showLog-button").button({ icons: {primary: "ui-icon-document-b" } });
	this.find(".refreshLog-button").button({ icons: {primary: "ui-icon-refresh" } });
	

	// render the buttons
	var actionsButtons = this.find(".actions-buttons");
	for (i in component.actions) {
		 // main action was added already
		 if (component.actions[i] != mainAction)
			actionsButtons.append(createActionButtons(component.actions[i]));
	}
	
	this.accordion({ header: "h3", collapsible: false });
	this.updateComponentView(component, components, options, true);
};

$.fn.updateComponentView = function(component, components, options, force) {

	if (!(component instanceof Component))
		throw new Error("Argument must be an instance of Component");

	
	var defaultOptions = {'disabled': screenManager.isLockedLocation()};
	options = $.extend(defaultOptions, options);

	// clear the summary and rerender it
	var table = this.find('.componentView-summary');
	table.html('');
	
	
	// Render Description / Dependencies
	var descriptions = {}
	var dependencies = []
	
	// update all the actions
	for (i in component.actions) {
		var action = component.actions[i];
		var id = action.id;
		if (action.description)
			descriptions[action.name] = action.description;
		
		if (action.dependencies.length > 0)
			$.merge(dependencies, action.dependencies.slice(0));
			
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
		
		// disable the start buton if either the option is set or the action cannot be started at all
		startButtons.find("a").button({'disabled': !action.canStart() || options['disabled']});
		
		// only disable stop button if the action cannot be stopped
		stopButtons.find(".stop-button").button({'disabled': !action.canStop() || options['disabled']});
	}
	// those buttons do not depend on any action
	this.find(".kill-button").button({'disabled': options['disabled']});
	this.find(".log-buttons a").button({'disabled': options['disabled']});
	
	renderDescription(table, descriptions);
	renderDependencies(table, dependencies, components);
	//	actionView.updateActionView(component.actions[i], components, options, force);
};

function renderDescription(container, descriptions)
{
	var isFirst = true;
	var i = 0;
	
	for (name in descriptions) {
		var tr = $(document.createElement("tr"));
		var class = "";
		
		if (isFirst) {
			tr.append("<th>Description: </th>");
			class = "ph_action-desc";
		}
		else {
			tr.append("<th></th>");
			class = "ph_action-hl ph_action-desc";
		}
		
		tr.append('<td class="' + class + '"><span class="name">' + name + ' &raquo; </span>' + descriptions[name] + '</td>');
					
		isFirst = false;
		container.append(tr);
	}
}

function renderDependencies(container, dependencies, components)
{	
	if (dependencies.length > 0) {
		var tr = $(document.createElement('tr')).addClass("dependencies");
		
		var html = '';
		for (i in dependencies) {
			html += '<div>';
			
			dependency = dependencies[i];
			if (components[dependency.compId] === undefined)
				throw new Error('Component "' + dependency.compId + '" not found')
			component = components[dependency.compId];
			
			if (!component.hasAction(dependency.actionId))
				throw new Error('Action "' + dependency.actionId + '" not found');
			a = component.getAction(dependency.actionId);
			
			if(a.isActive()) 
				html += '<span class="ui-icon ui-icon-component-action-on"></span><a href="#" class="running">' + component.name + " &raquo; " + a.name + '</a>';
			else
				html += '<span class="ui-icon ui-icon-component-action-off"></span><a href="#" class="notRunning">' + component.name + " &raquo; " + a.name + '</a>';
			html += '</div>'
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
