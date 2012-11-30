$.fn.renderMenuView = function(components, args) {
    try {
        options = {selected: null};
        $.extend(options, args);

        //  if (this.html() != '') return;
        this.html('');
        var navButtons = $(document.createElement('div'));
        navButtons.attr('id', 'nav-buttons');
        this.append(navButtons);

        
        i=0, size=0;
        // figure out the size of the associative array. No intern method available
        for (id in components)
            size++;

        renderMenuElements(navButtons, null, components);
        return true;
    }
    catch (err) {
        throw new Error('An error occured render the menu:\n' + err);
    }
}


function renderMenuElements(container, parentId, components)
{
    for (var id in components) {
        var component = components[id];
        if (component.parentId === parentId) {
            var btnClass = parentId !== null ? 'nav-button-indent' : '';
            var button = $('<div class="nav-button ' + btnClass + '"></div>');

            // if it has children, add an arrow
            var expandIndicator = $('<span class="menu-icon-expandIndicator ui-icon"></span>');
            if (!$.isEmptyObject(component.children)) {
                if (styleDataManager.isExpanded(component)) {
                    button.addClass('menu-item-expanded');
                    expandIndicator.addClass("menu-icon-expandable ui-icon-carat-1-s");
                }
                else {
                    button.addClass('menu-item-closed');
                    expandIndicator.addClass("menu-icon-expandable ui-icon-carat-1-e");
                }

                if (!component.hasInactiveChild()) {
                    expandIndicator.attr('title', 'All children of this component are running. Click to expand/close.');
                    expandIndicator.addClass('menu-icon-expandIndicator-allOn');
                }
                else if (component.hasActiveChild()) {
                    expandIndicator.attr('title', 'Some children of this component are running. Click to expand/close.');
                    expandIndicator.addClass('menu-icon-expandIndicator-partlyOn');
                }
                else {
                    expandIndicator.attr('title', 'No children of this component is running. Click to expand/close.');
                    expandIndicator.addClass('menu-icon-expandIndicator-allOff');
                }


                expandIndicator.click((function(id, button, expandIndicator) { return function() {
                    if (styleDataManager.isExpanded(id)) {
                    styleDataManager.close(id);
                    button.removeClass('menu-item-expanded');
                    button.addClass('menu-item-closed');
                    }
                    else {
                    styleDataManager.expand(id);
                    button.removeClass('menu-item-closed');
                    button.addClass('menu-item-expanded');
                    }
                }})(id, button, expandIndicator));
            }
            else
                expandIndicator.addClass("menu-icon-none");
                
            button.append(expandIndicator);
        

            // append the name
            var name=$('<span class="menu-item-name">' + component.getName() + '</span>');
            name.click((function(id) { return function() {
                application.select(id);
            }})(id));
            button.append(name);
            

            var span = $('<span class="menu-icon-status ui-icon"></span>');
            // append the running circles
            if (component.allActionsRunning()) {
                span.attr('title', "All component's actions are running");
                span.addClass("ui-icon-menu-component-on");
            }
            else if (component.actionsRunning()) {
                span.attr('title', "Some of the component's actions are running");
                span.addClass("ui-icon-menu-component-partlyOn");
            }
            else {
                span.attr('title', "None of the component's actions is running");
                span.addClass("ui-icon-menu-component-off");
            }
            button.append(span);


    /*      if (!$.isEmptyObject(component.children)) {o
            // add a float left to the previous bobble
            span.css('float', 'left');
            
            // indicating whether all children are running
            // think of a better classname
            var span = $('<span class="menu-icon-status-children ui-icon"></span>');
            button.append(span);
            }
    */      
            // seperately again
            if (screenManager.isLockedLocation())
                button.addClass('disabled');
            else
                button.removeClass('disabled');
                
            // render all children
            renderMenuElements(button, id, components);
        
            container.append(button);
        }
    }
}

