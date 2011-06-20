var actionEditViewCode = '<h3 class="actionEditView-name"><a href="#" class="ph_action_edit-name">PH_name</a></h3>\
				<div >\
					<div class="actionEditView-content">\
						<div class="actionEditView-text"><table>\
							<tr class="even"><th>name:</td><td><input type="text" class="ph_action_edit-name" value="PH_name" /></td></tr>\
							<tr class="even"><th>Description:</td><td><textarea class="ph_action_edit-desc">Keine Beschreibung angegeben</textarea></div>\</td></tr>\
							<tr class="even"><th>Dependencies:</th><td class="ph_action_edit-dep"></td></tr> \
						</table></div>\
						<div class="shellCommandsEditView">\
							<div class="shellStartCommandsEditView"><h4>StartCommands</h4></div>\
							<div class="shellStopCommandsEditView"><h4>StopCommands</h4></div>\
						</div>\
					</div>\
				</div>';


$.fn.renderActionEditView = function(action, components, options) {
	if (! (action instanceof Action))
		throw new Error("Argument must be an instance of Action");
		

	// it's a new object
	if (!this.hasClass('actionEditView')) {
		this.addClass('actionEditView');
		this.html(actionEditViewCode);

		// Accordion
		active = styleDataManager.isActionTabClosed(action.id) ? false : null;
		this.accordion({ header: "h3", collapsible: true, active: active });
		this.bind('accordionchange', function(event, ui) {
			styleDataManager.toggleActionTab(action.id);
		});
			
		// Set name and description. These values don't change
		this.find("a.ph_action_edit-name").text(action.name);
		
		inputName = this.find("input.ph_action_edit-name");
		inputName.val(action.name);
		inputName.focusout(function() { action.name = this.value; });
		
		inputDesc = this.find("textarea.ph_action_edit-desc");
		inputDesc.focusout(function() { action.description = this.value; });
		if (action.description)
			inputDesc.val(action.description);
	}


	var defaultOptions = {'disabled': screenManager.isLockedLocation()};
	options = $.extend(defaultOptions, options);
	
	
	// render dependencies
	dep = this.find(".ph_action_edit-dep");
	var html = ''
	for (i in action.dependencies) {
		dependency = action.dependencies[i];
		html += dependencySelectCode(dependency, components);
		html += '<br />'
	}
	// remove the last <br />
	html = html.substring(0, html.length-6);
	dep.html(html)
	
	
	// render shell commands
	// render startCommands
	shellStartCommandsEditView = this.find('.shellStartCommandsEditView');
	for (i in action.startCommands) {
		command = action.startCommands[i];
		
		div = $(document.createElement("div"))
		shellStartCommandsEditView.append(div);
		div.attr("id", "shellCommand-" + command.id);
		div.renderShellCommandEditView(command);
	}
	
	// render stopCommands
	shellStopCommandsEditView = this.find('.shellStopCommandsEditView');
	for (i in action.stopCommands) {
		command = action.stopCommands[i];
		
		div = $(document.createElement("div"))
		shellStopCommandsEditView.append(div);
		div.attr("id", "shellCommand-" + command.id);
		div.renderShellCommandEditView(command);
	}
};

function dependencySelectCode(dep, components)
{
	actionId = dep.actionId;
	
	html = '<select size="1">';
	for (i in components) {
		component = components[i];
		html += '<optgroup label="' + component.name + '">';
		
		for (j in component.actions) {
			action = component.actions[j];
			selected = '';
			if (action.id == dep.actionId)
				selected = 'selected="selected"'
			
			html += '<option label="' + component.name + ' &raquo; ' + action.name + '" ' + selected + '>' + component.name + ' &raquo; ' + action.name + '</label>';
		}
	}
	html += '</select>';
	return html;
}

var shellCommandEditViewCode = '<div>Join<br />Thread<br /><input type="checkbox" class="ph_shell_command_edit_blocking" /></div><textarea class="ph_edit_shell_command-command">PH_EDIT_SHELL_COMMAND-COMMAND</textarea>';
$.fn.renderShellCommandEditView = function(command)
{
	this.addClass('editShellCommand');
	this.html(shellCommandEditViewCode);
	
	inputBlocking = this.find("input.ph_shell_command_edit_blocking");
	inputBlocking.focusout(function() { command.blocking = this.checked === true; } );
	
	if (command.blocking)
		inputBlocking.attr("checked", "checked");
	
	inputCommand = this.find('textarea.ph_edit_shell_command-command');
	inputCommand.val(command.command);
	inputCommand.focusout(function() { command.command = this.value; });
}
