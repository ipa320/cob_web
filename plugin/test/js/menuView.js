$.fn.renderMenuView = function(components, args) {
	options = {selected: null};
	$.extend(options, args);

//	if (this.html() != '') return;
	this.html('');
	navButtons = $(document.createElement('div'));
	navButtons.attr('id', 'nav-buttons');
	this.append(navButtons);

	
	i=0, size=0;
	// figure out the size of the associative array. No intern method available
	for (id in components)
		size++;

	renderMenuElements(null, 1, components, options, i, size);
	return true;
}


function renderMenuElements(parentId, level, components, options, i, size)
{
	for (id in components) {
		component = components[id];
		if (component.parentId === parentId) {
			btnClass = 'btn-middle'
			if (i == 0) btnClass = 'btn-top';
			if (i == size - 1) btnClass = 'btn-bottom'

			checked = '';
			if (options.selected instanceof Object && options.selected.id === id)
				checked = 'checked="checked"';

			navButtons.append('<div class="level-' + level + '"><input type="checkbox" ' + checked + ' onchange="javascript:application.select(\'' + id + '\')" class="nav-button" name="nav" id="nav-' + id + '" /><label for="nav-' + id + '" class="' + btnClass + '">' + components[id].name + '</label></div>');
			if (component.allActionsRunning())
				icon = "ui-icon-check";
			else if (component.actionsRunning())
				icon = "ui-icon-gear";
			else
				icon = "ui-icon-power";
			button = $("#nav-" + id);
			button.button({ 'icons': {'primary': icon } }); // ui-icon-check // ui-icon-close
			
			// seperately again
			if (screenManager.isLockedLocation()) {
				button.button({ 'disabled': true });
			}

			i++;

			// render all children
			renderMenuElements(id, level+1, components, options, i, size);
		}
	}
	return true;
}
