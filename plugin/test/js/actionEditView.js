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
		var active = styleDataManager.isActionTabClosed(action.id) ? false : null;
		this.accordion({ header: "h3", collapsible: true, active: active });
		this.bind('accordionchange', function(event, ui) {
			styleDataManager.toggleActionTab(action.id);
		});
			
		// Set name and description. These values don't change
		this.find("a.ph_action_edit-name").text(action.name);
		
		var inputName = this.find("input.ph_action_edit-name");
		inputName.val(action.name);
		inputName.focusout(function() { action.name = this.value; });
		
		inputDesc = this.find("textarea.ph_action_edit-desc");
		inputDesc.focusout(function() { action.description = this.value; });
		if (action.description)
			inputDesc.val(action.description);
	}


	var defaultOptions = {'disabled': screenManager.isLockedLocation()};
	var options = $.extend(defaultOptions, options);
	
	
	// render dependencies
	var dep = this.find(".ph_action_edit-dep");
	for (i in action.dependencies) {
		dependency = action.dependencies[i];
		dep.append( dependencySelectCode( components, dependency ) );
		dep.append( '<br />' );
	}
	// remove the last <br />
//	html = html.substring(0, html.length-6);
//	dep.html(html)
	// link to add new dependencies
	$(document.createElement("a")).attr("href", "#").text("Append new dependency").appendTo(dep).click(function() { 
		var depObj={'compId': null, 'actionId': null};
		action.dependencies.push(depObj);
		dep.find("a").before($(dependencySelectCode(components, depObj)));
		return false;
	});
	
	// render shell commands
	// render startCommands
	var shellStartCommandsEditView = this.find('.shellStartCommandsEditView');
	for (i in action.startCommands) {
		command = action.startCommands[i];
		
		var div = $(document.createElement("div"))
		shellStartCommandsEditView.append(div);
		div.attr("id", "shellCommand-" + command.id);
		div.renderShellCommandEditView(command);
	}
	// link to append new commands
	var a = $(document.createElement("a")).attr("href", "#").text("Append new start command");
	shellStartCommandsEditView.append(a);
	a.click(function() { 
		id = application.getUniqueTemporaryId();
		var cmd = {'id': id, 'command':'', 'blocking': false};
		action.startCommands.push(cmd);

		div = $(document.createElement("div"));
		shellStartCommandsEditView.find("a").before(div);
		div.attr("id", "shellCommand-" + id);
		div.renderShellCommandEditView(cmd);
		return false;
	});
	
	// render stopCommands
	var shellStopCommandsEditView = this.find('.shellStopCommandsEditView');
	for (i in action.stopCommands) {
		command = action.stopCommands[i];
		
		div = $(document.createElement("div"))
		shellStopCommandsEditView.append(div);
		div.attr("id", "shellCommand-" + command.id);
		div.renderShellCommandEditView(command);
	}
	// link to append new commands
	var a = $(document.createElement("a")).attr("href", "#").text("Append new stop command");
	shellStopCommandsEditView.append(a);
	a.click(function() { 
		id = application.getUniqueTemporaryId();
		var cmd = {'id': id, 'command':'', 'blocking': false};
		action.stopCommands.push(cmd);

		div = $(document.createElement("div"));
		shellStopCommandsEditView.find("a").before(div);
		div.attr("id", "shellCommand-" + id);
		div.renderShellCommandEditView(cmd);
		return false;
	});
};

function dependencySelectCode(components, dep)
{
	html = '<select size="1"><option label=" - "> - </option>';
	for (i in components) {
		component = components[i];
		html += '<optgroup label="' + component.name + '">';
		
		for (j in component.actions) {
			action = component.actions[j];
			selected = '';
			if (action.id == dep.actionId)
				selected = 'selected="selected"'
			
			html += '<option compId="' + i + '" actionId="' + j + '" label="' + component.name + ' &raquo; ' + action.name + '" ' + selected + '>' + component.name + ' &raquo; ' + action.name + '</option>';
		}
	}
	html += '</select>';
	select = $(html);
	select.addClass("test");
	alert(select.size() + "\n" + select[0] + "\n" + select + "\n" + select.hasClass("test"));
	
	select.change(function() {
		var selected = $(this).find('option:selected')
		dep.compId = parseInt(selected.attr("compId"));
		dep.actionId = parseInt(selected.attr("actionId"));
	});
	return select;
}

var shellCommandEditViewCode = '<div class="buttons"><a href="#" class="delete-button">-</a></div><div class="options">Join<br />Thread<br /><input type="checkbox" class="ph_shell_command_edit_blocking" /></div><textarea class="ph_edit_shell_command-command">PH_EDIT_SHELL_COMMAND-COMMAND</textarea>';
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
	
	deleteButton = this.find('.delete-button')
	deleteButton.button();// {icons: {primary: 'ui-icon-circle-close' }} );
	var obj = this;
	deleteButton.click((function() { 
		command.command = ""
		$(obj).remove();
		return false;
	}));
}
