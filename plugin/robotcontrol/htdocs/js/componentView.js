var componentViewCode = '\<h1>Component "<span class="ph_comp-name"></span>"</h1><div class="actionsView">\
	<div class="componentView">\
		<div class="componentView-topBar componentView-name"> \
			<div class="componentView-topBar-leftBorder" /> \
			<div class="componentView-topBar-rightBorder" /> \
			<div class="componentView-topBar-text"><span class="ui-icon ui-icon-triangle-1-s" />Control Panel</div> \
		</div> \
		<div class="componentView-content" >\
			<div class="componentView-buttons">\
				<div class="group-buttons">\
					<a href="#" class="start-group-button">Start Group</a>\
					<a href="#" class="stop-group-button">Stop Group</a>\
				</div>\
				<div class="log-buttons">\
					<input type="checkbox" class="showLog-button" id="showLog" /><label for="showLog">ShowLog</label>\
				</div>\
				<div class="parameters-buttons">\
				</div>\
				<div class="actions-buttons"></div>\
			</div>\
			<div><table class="componentView-summary" cellspacing="0" cellpadding="0">\
			</table></div>\
		</div>\
		<div class="logView"></div>\
		<div class="parametersView"></div>\
	</div>';
//<a href="javascript:application.editComponent()" class="edit-button">Edit</a><h1>Component "<span class="ph_comp-name"></span>"</h1><div class="actionsView">

$.fn.renderComponentView = function(component, components, options) {
    if (!(component instanceof Component))
        throw new Error("Render: Argument must be an instance of Component");

    // Every component must have a main action
    var mainAction = component.getMainAction();

    // clear the html
    this.addClass("componentView");
    this.html(componentViewCode);

    // set the values that stay forever
    this.find(".ph_comp-name").text(component.name);
    

    // The container for the various buttons
    var buttons = this.find('.componentView-buttons')

    // if this component has children, create buttons to start/stop the
    // entire group
    var groupButtons = this.find('.group-buttons');
    if (!$.isEmptyObject(component.children)) {
        var startGroup = groupButtons.find('.start-group-button');
        var stopGroup  = groupButtons.find('.stop-group-button');
        
        groupButtons.buttonset();
        startGroup.button({'icons': { 'primary': 'ui-icon-play'} });
        stopGroup.button({'icons':  { 'primary': 'ui-icon-stop'} });

        startGroup.click(function() { application.startGroup(component.id); });
        stopGroup.click(function()  { application.stopGroup(component.id); });
    }
    else
        groupButtons.hide();
    
    // append the start/stop buttons for the main action to the button container
    groupButtons.after(createActionButtons(mainAction, component));
    
    // Create log buttonset
    this.find(".log-buttons").buttonset();
    var showLogButton = this.find(".showLog-button");
    showLogButton.button({ 'icons': {primary: "ui-icon-document-b" } });
    var logView = this.find(".logView").hide();
    var toggleLogView = createToggleLogView( logView, component );
    showLogButton.click( toggleLogView );

    $( '.parametersView' ).hide();
    

    // render the buttons
    var actionsButtons = this.find(".actions-buttons");
    for (i in component.actions) {
        // main action was added already
        if (component.actions[i] != mainAction)

            actionsButtons.append(createActionButtons(component.actions[i], component));
    }
    
    
    this.updateComponentView(component, components, options);
};

function createToggleParametersView( action ){
    return function(){
        var parametersView = $( '.parametersView' );
        console.log( 'do it for action: ', action, parametersView.is( ':visible' ) );
        if( !parametersView.is( ':visible' )){
            parametersView.show();
            parametersView.renderParametersView( action.id );
            var addFieldCallback = function( name, value ){
                parametersView.addParameterField( name, value );
            };
            var finishedCallback = function(){
                parametersView.parametersLoadedCallback();
            };
            application.loadParameters( action, finishedCallback, addFieldCallback );
        }
        else{
            parametersView.hide();
        }
    };
}
function createToggleLogView( logView, component ){
    return function(){
        if (!logView.is(":visible")) {
            var setTextCallback = function(html) {
                logView.setLogContent(html);
            };
            
            logView.show();
            logView.renderLogView(component, function(id) { 
                application.loadLog(id, setTextCallback); 
            });
        }
        else {
            logView.hide();
        }
    };
}

$.fn.updateComponentView = function(component, components, options) {

    if (!(component instanceof Component))
	throw new Error("Update: Argument must be an instance of Component");

    
    var defaultOptions = {'disabled': screenManager.isLockedLocation()};
    options = $.extend(defaultOptions, options);

    // clear the summary and rerender it
    var table = this.find('.componentView-summary');
    table.html('');
    
    
    // Render Description
    var descriptions = {},
        dependencies = [],
        states = {};

    
    // update all the actions
    for (i in component.actions) {
        var action = component.actions[i];
        var id = action.id;
        if (action.description)
            descriptions[action.name] = action.description;
        if( action.state )
            states[ action.name ] = action.state;
        
        // update buttons
        var actionButtons = this.find( '#action-buttons-' + id );
        var startButtons = actionButtons.find( '.start-buttons' );
        var stopButtons  = actionButtons.find( '.stop-buttons' );
        var parametersButton = actionButtons.find( '.parameters-button' );
        if (action.isActive()) {
            // need to show start / hide stop buttons ?
            if (startButtons.is(':visible')) {
                startButtons.hide();
                stopButtons.show();
                // the ui-state-hover is not removed properly on a mouseout sometimes
                stopButtons.find('.stop-button', '.kill-button').removeClass('ui-state-hover');
            }
            parametersButton.button({ 'disabled': true });
        }
        else {
            if (stopButtons.is(':visible')) {
                startButtons.show();
                startButtons.find('.start-button').removeClass('ui-state-hover');
                stopButtons.hide()
            }
            parametersButton.button({ 'disabled': false });
        }

        if( !action.parameterFile )
            parametersButton.hide();
        if (application.status != application.SERVER_IN_CHARGE) 
            parametersButton.button({ 'disabled': true });

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

    // disable the group start button either if it disabled in the options array
    // is true or if no child action of this component is running
    this.find('.group-buttons .start-group-button').button({'disabled': options['disabled'] || !component.hasInactiveChild() });

    // disable the group button if options['disabled'] is true, no action is running
    // or any of the child action cannot be stopped
    this.find('.group-buttons .stop-group-button').button({'disabled': options['disabled'] || !component.hasActiveChild() });

    
    renderStates( table, states );
    renderDescription(table, descriptions);
    renderDependencies(table, dependencies, component);
    
    renderFrames(this, component.actions);

    // update the logview if visible
    var logView = this.find(".logView");
    if (logView.is(':visible'))
        logView.updateLogView(component);
};

function renderStates( container, states )
{
    var isFirst = true;
    
    for( name in states ){
        var tr = $( '<tr />' ),
            myClass = "";
        
        if (isFirst) {
            tr.append("<th>State: </th>");
            myClass = "ph_action-state";
        }
        else {
            tr.append("<th></th>");
            myClass = "ph_action-hl ph_action-state";
        }
        
        var state = states[ name ],
            stateString = '';
        if( state.code )
            stateString += '<b>' + states[ name ].code + '</b>';
        if( state.message )
            stateString += ': &nbsp;' + state.message;

        tr.append('<td class="' + myClass + '"><span class="name">' + name + ' &raquo; </span>' + stateString + '</td>');
        
        isFirst = false;
        container.append(tr);
    }
}

function renderDescription(container, descriptions)
{
    var isFirst = true;
    
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

function createActionButtons( action, component )
{
    var startText = 'Run ' + action.name,
        stopText  = 'Stop ' + action.name,
        killText  = 'Kill ' + action.name,
        changeParametersText = 'Parameters for ' + action.name;
    
    // create divs based on the id, not the name because of special chars
    var div = $(document.createElement('div')).attr('id', 'action-buttons-' + action.id);
    var startButtons = $(document.createElement('div')).addClass('start-buttons');
    var stopButtons = $(document.createElement('div')).addClass('stop-buttons');
    div.append(startButtons);
    div.append(stopButtons);

    var startButton = $('<a href="#" class="start-button">' + startText + '</a>');
    var stopButton  = $('<a href="#" class="stop-button">'  + stopText  + '</a>');
    var killButton  = $('<a href="#" class="kill-button">'  + killText  + '</a>');
    //var changeParametersButton = $( '<input type="checkbox" class="changeParameters-button" id="changeParameters-' + action.id + '" /><label for="changeParameters-' + action.id + '">' + changeParametersText + '</label>' );
    var changeParametersButton = $( '<a href="javascript:void(0)" class="parameters-button">' + changeParametersText + '</a>' );
    startButtons.append(startButton);
    stopButtons.append(stopButton);
    stopButtons.append(killButton);
    div.append( changeParametersButton );

    startButtons.buttonset();
    stopButtons.buttonset();

    startButton.button({ icons: {primary: "ui-icon-play"} });
    stopButton.button({ icons: {primary: "ui-icon-stop" } });
    killButton.button({ icons: {primary: "ui-icon-notice"} });
    changeParametersButton.button({ icons: { primary: 'ui-icon-gear' }});
    
    
    // set the buttons' actions
    startButton.click(function() { application.startAction(action.id, action.compId); return false; });
    stopButton.click(function() { application.stopAction(action.id, action.compId); return false; });
    killButton.click(function() { application.killAction(action.id, action.compId); return false; });
    
    changeParametersButton.click( createToggleParametersView( action ));
    
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
