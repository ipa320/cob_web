var actionEditViewCode = '<h3 class="actionEditView-name"><a href="#" class="ph_action_edit-name">PH_name</a></h3>\
				<div >\
					<div class="actionEditView-content">\
						<div class="actionEditView-text"><table>\
							<tr class="even"><th>Name:</th><td><input type="text" class="ph_action_edit-name" value="PH_name" /></td></tr>\
							<tr class="even ph_action_edit-host"><th>Host:</th><td class="ph_action_edit-host"></td></tr>\
							<tr class="even"><th>Description:</th><td><textarea class="ph_action_edit-desc"></textarea></div>\</td></tr>\
							<tr class="even"><th>URL:</th><td><input class="ph_action_edit-url" /></div>\</td></tr>\
							<tr class="even"><th>Dependencies:</th><td class="ph_action_edit-dep"></td></tr> \
						</table></div>\
						<div class="shellCommandsEditView">\
							<div class="shellStartCommandsEditView"><h4>StartCommands</h4></div>\
							<div class="shellStopCommandsEditView"><h4>StopCommands</h4></div>\
						</div>\
					</div>\
				</div>';


$.fn.renderActionEditView = function(action, component, isMain, options) {
	if (! (action instanceof Action))
		throw new Error("Argument must be an instance of Action");
		

	// it's a new object
	if (!this.hasClass('actionEditView')) {
		this.addClass('actionEditView');
		this.html(actionEditViewCode);

		// Accordion
		this.accordion({ header: "h3", collapsible: true });

		// render the host selection if this is the main action
		if (isMain) {
			console.log(component);
			var hostSelect = $(Host.createSelectHtmlCode(component.hostId));
			this.find("td.ph_action_edit-host").append(hostSelect);
			hostSelect.change(function() {
				var selected = $(this).find('option:selected')
				var hostId = parseInt(selected.attr("hostId"));
				component.hostId = hostId;
			});
		}
		// else hide the row
		else 
			this.find("tr.ph_action_edit-host").hide();
			
		
	
			
		// Set name and description. These values don't change
		this.find("a.ph_action_edit-name").text(action.name);
		
		var inputName = this.find("input.ph_action_edit-name");
		inputName.val(action.name);
		inputName.focusout(function() {
			action.name = this.value;
			//TODO:
			if (isMain) component.name = this.value;
		});
		
		var inputDesc = this.find("textarea.ph_action_edit-desc");
		inputDesc.focusout(function() { action.description = this.value; });
		if (action.description)
			inputDesc.val(action.description);
			
		var inputUrl = this.find("input.ph_action_edit-url");
		inputUrl.val(action.url);
		inputUrl.focusout(function() { action.url = this.value; });
	}


	//  dependencies
	var dep = this.find(".ph_action_edit-dep");

	// function to create a new dependency list
	var onDependencyChange = function() {
	    var list = []
	    
	    // get all inputs
	    var inputs = dep.find('select');
	    inputs.each(function(i, obj) {
		var selected = $(this).find('option:selected')
		var actionId = parseInt(selected.attr("actionId"));
		if (actionId)
		    list.push(actionId);
	    });

	    action.dependencies = list;
	    console.log(list);
	};

	for (var i in action.dependencies) {
		dependency = action.dependencies[i];
		var selectObj = $( dependencySelectCode( component, dependency ) );
		selectObj.change(onDependencyChange);
		dep.append(selectObj);
		dep.append( '<br />' );
	}

	// link to add new dependencies
	$(document.createElement("a")).attr("href", "#").text("Append new dependency").appendTo(dep).click(function() { 
		var selectObj = $(dependencySelectCode(component));
		selectObj.change(onDependencyChange);
		
		dep.find("a").before(selectObj);
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
		var cmd = {'id': id, 'command':'', 'blocking': false, 'hideLog': false};
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
		var cmd = {'id': id, 'command':'', 'blocking': false, 'hideLog': false};
		action.stopCommands.push(cmd);

		div = $(document.createElement("div"));
		shellStopCommandsEditView.find("a").before(div);
		div.attr("id", "shellCommand-" + id);
		div.renderShellCommandEditView(cmd);
		return false;
	});
};

function dependencySelectCode(component, depId)
{
	html = '<select size="1"><option label=" - "> - </option>';
	html += '<optgroup label="' + component.name + '">';
		
	for (j in component.actions) {
		action = component.actions[j];
		var selected = '';
		if (action.id == depId)
			selected = 'selected="selected"'
		
		html += '<option actionId="' + j + '" label="' + component.name + ' &raquo; ' + action.name + '" ' + selected + '>' + component.name + ' &raquo; ' + action.name + '</option>';
	}
	
	html += '</select>';
	select = $(html);
	select.addClass("test");
	
	return select;
}


var shellCommandEditViewCode = '<div class="buttons"><a href="#" class="delete-button">-</a></div><div class="options">Hide<br />Log<br /><input type="checkbox" class="ph_shell_command_hide_log" /></div><div class="options">Join<br />Thread<br /><input type="checkbox" class="ph_shell_command_edit_blocking" /></div><textarea class="ph_edit_shell_command-command">PH_EDIT_SHELL_COMMAND-COMMAND</textarea>';
$.fn.renderShellCommandEditView = function(command)
{
	this.addClass('editShellCommand');
	this.html(shellCommandEditViewCode);
	
	// init the blocking checkbox
	var inputBlocking = this.find("input.ph_shell_command_edit_blocking");
	inputBlocking.focusout(function() { command.blocking = this.checked === true; } );
	if (command.blocking)
		inputBlocking.attr("checked", "checked");
		
	// init the hidelog checkbox
	var inputHideLog = this.find("input.ph_shell_command_hide_log")
	inputHideLog.focusout(function() { command.hideLog = this.checked === true; } );
	if (command.hideLog)
		inputHideLog.attr("checked", "checked");
	
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
