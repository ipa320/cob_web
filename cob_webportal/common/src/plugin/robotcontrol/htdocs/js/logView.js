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
    var refreshButton = this.find(".refreshLog-button");
	
    navigation.html(ul);

    var liClickAction = function(id, li) {
	return function() {
	    callbackOnClick(id);
	    refreshButton.unbind('click');

	    // remove the class actionSelecrted from all siblings, making this the only selected item
	    li.siblings().removeClass('actionSelected');
	    li.addClass('actionSelected');
	    refreshButton.click(function() {
		    callbackOnClick(id);
		    // jquery bug: remove the active state
		    refreshButton.removeClass('ui-state-focus');
		    return false;
	   });
	}
    };

    for (var actionId in component.actions) {
        var action = component.actions[actionId];
        var actionClass = "log-tab-action-" + action.id;
                
        if (component.getMainAction().id == actionId)
            actionClass += " actionSelected";
            
        var li = $('<li class="' + actionClass + '"><span class="ui-icon"></span><span class="actionName">' + action.name + "</span></li>");
        ul.append(li);

        li.click(liClickAction(action.id, li));
    }


    this.setLogContent = function(html) {
        logContent.text(html);
        var escaped_html = logContent.html();

        var replacements = {
            '%br%':      '<br />',
            '%bold%':    '<b>',
            '%/bold%':   '</b>',
            '%red%':     '<span style="color:red"><b>',
            '%/red%':    '</b></span>',
            '%yellow%':  '<span style="color:yellow"><b>',
            '%/yellow%': '</b></span>'
        };

        for( var key in replacements ){
           var regex = new RegExp( key, 'g' );
           escaped_html = escaped_html.replace( regex, replacements[ key ]);
       }

        logContent.html( escaped_html );
        logContent.scrollTop( logContent[ 0 ].scrollHeight );
    };

    this.updateLogView(component);
}

	    
$.fn.updateLogView = function(component)
{
    var ul = this.find('ul');
    for (var actionId in component.actions) {
	var action = component.actions[actionId];
	var li = ul.find(".log-tab-action-" + action.id);

	var icon;
	if (action.isActive())
	    icon = "ui-icon-menu-component-on";
	else
	    icon = "ui-icon-menu-component-off";

	// update the icon for the action
	li.find('.ui-icon').attr('class', 'ui-icon ' + icon);

	// if this is the main action, execute the click function
	if (component.getMainAction() == action)
	    li.click();
    }
};
