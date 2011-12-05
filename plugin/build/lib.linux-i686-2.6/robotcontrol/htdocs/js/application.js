var application = new (function() {
    this.SERVER_AVAILABLE = 1;
    this.SERVER_IN_CHARGE = 2;
    this.SERVER_NOT_AVAILABLE = -1;
    
    this.components = null;
    this.selectedComponent = null;
    
    this.reservations = null;
    
    // timeout for frequent updates (only if in charge)
    this.updateTimeoutId = -1;
    
    // timeout for status checks (only if not in charge)
    this.statusTimeoutId = -1;
    
    // timestamp of last request
    this.lastUpdateTimestamp = 0;
    
    // available events
    this.ACTION_STATUS_EVENT=1;
    this.HOST_EVENT = 2;
    
    this._nextTempId=-1;
    
    this.getUniqueTemporaryId = function() {
	return this._nextTempId--;
    }
    
    
    this.init = function(urlPrefix, username, views, handler) {
	// urlPrefix without trailing /
	this.urlPrefix = urlPrefix;

	// if no handler was passed, or no finished function was passed, raise an error
	if (!handler || !(handler instanceof Object) || !handler['finished'])
	    throw new Error('The passed handler is invalid');
	// create a default success handler which does nothing if none is defined
	if (!handler['success'] || !(handler['success'] instanceof Function))
	    handler.success = function() {};
	// create a default error handler which alerts the message if none is defined
	if (!handler['error'] || !(handler['error'] instanceof Function))
	    handler.error = function(data) { alert('DEFAULT AJAX ERROR HANDLER:\n\n' + data); };

	// views must contain both menuView and componentView
	if (!(views instanceof Object)) { 
	    handler.error('View Argument is not an object');
	    return;
	}
	requiredViews = ['menuView', 'componentView', 'infoBoxView', 'serverReservationView'];
	for (i in requiredViews) {
	    viewName = requiredViews[i];
	    if (!views[viewName] instanceof jQuery || views[viewName].size() == 0) {
		handler.error('View "' + viewName + '" is not an valid jQuery-Object');
		return;
	    }
	    this[viewName] = views[viewName];
	}
	
	// Todo: remove this workaround
	resId = this.serverReservationView.attr('id');
	if (!resId instanceof String || resId.length == 0) {
	    handler.error('Server Reservation View must have an unique id');
	    return;
	}

	// create a trigger to show the fancybox
	this.calendarTrigger = $(document.createElement('a'));
	this.calendarTrigger.fancybox({
	    'autoDimensions' : false,
	    'autoScale'      : false,
	    'width'          : '95%',
	    'height'         : '95%',
	    'type'           : 'inline',
	    'href'           : '#' + this.serverReservationView.attr('id'),
	    'transitionIn'   : 'none',
	    'transitionOut'  : 'none'
	});		
	
	
	this.username = username;

	// set some basic ajax settings
	$.ajaxSetup({
	    dataType: 'json'
	});
	handler.success('Initialized JavaScript');

	// Check whether the server is online and a user logged in
	var onServerStatusSuccess = function(data) {
	    application.statusDataSuccess(data, handler);
	    Host.loadHostData(application.urlPrefix, onHostDataSuccess, onHostDataError);
	};
	var onServerStatusError = function(data) {
	    application.statusDataError(data, handler);
	};
	// host does have its own callback handlers
	var onHostDataSuccess = function(data) {
	    handler.success('Host Data Received');
	    application.loadCompData(onComponentSuccess, onComponentError);
	};
	var onHostDataError = function(data) {
	    console.log(data);
	    handler.error('Host Data could not be loaded [' + data.status + '; ' + data.responseText + ']');
	};
	var onComponentSuccess = function(data) {
	    application.compDataSuccess(data, handler);
	    application.loadReservations(onReservationSuccess, onReservationError);
	};
	var onComponentError = function(data) {
	    application.compDataError(data, handler);
	};
	var onReservationSuccess = function(data) {
	    application.reservationDataSuccess(data, handler);

    	    if (application.status == application.SERVER_IN_CHARGE) {
		application.loadEventHistoryData(onEventHistorySuccess, onEventHistoryError);
	    }
	    else {
		handler.success('Skipping History Data');
		application.finalApplicationInitialization(handler);
	    }
	};
	var onReservationError = function(data) {
	    application.reservationDataError(data, handler);
	};
	var onEventHistorySuccess = function(data) {
	    application.eventHistoryDataSuccess(data, handler);
	    application.finalApplicationInitialization(handler);
	};
	var onEventHistoryError = function(data) {
	    application.eventHistoryDataError(data, handler);
	};
	    
	
	
	this.checkServerStatus(onServerStatusSuccess, onServerStatusError);
    }
    
    /*
     * Helper Functions
     */
    this.getComponent = function(compId) {
	if (!(parseInt(compId) > 0))
	    throw new Error('Invalid component id "' + compId + '"');
	
	component = this.components[compId];
	if (component === undefined)
	    throw new Error('Invalid Component Id "' + compId + '" passed');
	
	return component;
    }

    /*
     * Check whether the server is online and a user logged in
     */
    this.checkServerStatus = function(callbackSuccess, callbackError) {
	$.ajax({
	    url: this.urlPrefix + '/status',
	    success: callbackSuccess,
	    error:   callbackError || function(){}
	});
    }
    this.statusDataSuccess = function(data, handler) {
	try {
	    this.status = parseInt(data['status'])
	    if (this.status != this.SERVER_AVAILABLE && this.status != this.SERVER_IN_CHARGE && this.status != this.SERVER_NOT_AVAILABLE)
		throw new Error('The status code is invalid "' + data['status'] + '"')
	    
	    
	    if (this.status == this.SERVER_AVAILABLE) 
		handler.success('Server online, User authenticated, Server available');
	    if (this.status == this.SERVER_IN_CHARGE)
		handler.success('Server online, User authenticated, you\'re in charge');
	    if (this.status == this.SERVER_NOT_AVAILABLE)
		handler.success('Server online, User authenticated, Server is not available');
	}
	catch (err) {
	    handler.error('Error occured while parsing host data:\n' + err);
	    throw err;
	}
    }
    this.statusDataError = function(data, handler) {
	if (data.status === 503)
	    handler.error('The server is not online');
	else if (data.status === 401)
	    handler.error('Authorization denied');
	else if (data.status === 500)
	    handler.error('Internal Server error');
	else
	    handler.error('Unknwon error code received: ' + data.status);
    }



    /*
	 * Load / parse Component Data from Remote Server
	 */
    this.loadCompData = function(callbackSuccess, callbackError)  {
	$.ajax({
	    url: this.urlPrefix + '/data/comp',
	    success: callbackSuccess,
	    error:   callbackError || function(){}
	});
    }
    this.compDataSuccess = function(compData, handler) {
	try {
	    this.components = {}
	    
	    for (id in compData) {
		id = parseInt(id);
		comp = compData[id];
		// check whether all required fields are set. host, parentId may be null
		if (!id || isNaN(id) || !comp.name || !comp.actions || !(comp.actions instanceof Object))
		    throw new Error('Invalid Comp-Object received')

		// parse the actions first
		actions = {};
		for (actionId in comp.actions) {
		    actionId = parseInt(actionId);
		    action = comp.actions[actionId];
		    // check whether all required fields are set. description might be null
		    if (!actionId || isNaN(actionId) || !action ||/* !action.name ||*/ !action.dependencies || !(action.dependencies instanceof Object) || !(action.startCmds instanceof Object) || !(action.stopCmds instanceof Object)) {
			console.log(action);
			throw new Error('Invalid Action-Object received')
		    }

		    actions[actionId] = new Action(actionId, action.name, id, action.desc, action.url, action.dependencies, action.startCmds, action.stopCmds)
		}

		this.components[id] = new Component(id, comp.host, comp.name, comp.parentId, actions);
	    }

	    // sort the data
	    for (id in this.components) {
		parentId = this.components[id].parentId;
		if (parentId) {
		    this.components[id].parent = this.components[parentId];
		    this.components[parentId].children[id] = this.components[id];
		}
	    }
	    
	    handler.success('Component Data Received');
	}
	catch (err) {
	    handler.error('Error occured while parsing component data:\n' + err);
	    throw err;
	}
    }
    this.compDataError = function(data, handler) {
	handler.error('Comp Data could not be loaded [' + data.status + '; ' + data.responseText + ']');
    }
    
    /*
	 * Load Reservations
	 */
    this.loadReservations = function(callbackSuccess, callbackError)  {
	$.ajax({
	    url: this.urlPrefix + '/reservations/get',
	    success: callbackSuccess,
	    error:   callbackError || function(){}
	});
    }
    this.reservationDataSuccess = function(data, handler) {
	try {
	    this.reservations = []
	    for (id in data) {
		item = data[id]
		start = this.urlDecodeDate(item.start);
		end = this.urlDecodeDate(item.end);
		// check whether start / end is invalid				
		if (start === null || end === null)
		    throw new Error('Invalid start or end date ["' + item.start + '", "' + item.end + '"]')			    

		this.reservations.push({'id': id, 'title': item.title, 'owner': item.owner, 'start': start, 'end': end});
	    }
	    handler.success('Reservation Data Received');
	}
 	catch (err) {
	    handler.error('Error occured while parsing component data:\n' + err);
	    throw err;
	}
    }
    this.reservationDataError = function(data, handler) {
	handler.error('Reservation data could not be loaded [' + data.status + '; ' + data.responseText + ']');
    }
    

    
    /*
	 * Load / parse Event History Data from Remote Server+
	 * only load data if we're in charge. Otherwise skip this step
	 */
    this.loadEventHistoryData = function(callbackSuccess, callbackError) {
	$.ajax({
	    url: this.urlPrefix + '/data/eventHistory/0',
	    success: callbackSuccess,
	    error:   callbackError || function() {}
	});
    }
    this.eventHistoryDataSuccess = function(data, handler) {
	try {
	    this.processEventHistoryData(data);
	    handler.success('Event History Data Received');
	}
	catch (err) {
	    handler.error('An error occured processing History Data: ' + err);
	    throw err;
	}
    }
    this.eventHistoryDataError = function(data, handler) {
	console.log(data);
	handler.error('Event History Data could not be loaded [' + data.status + '; ' + data.responseText + ']');
    }
    
    /*
	 * Some final stuff (timeout etc.)
	 */
    this.finalApplicationInitialization = function(handler)
    {
	try {
	    // set the timout only if we're in charge
	    if (this.status == this.SERVER_IN_CHARGE)
		this.updateTimeoutId = setTimeout("application.updateEventHistory()", 2000);
	    
	    // if not in charge, set a timeout to frequently request the server status and check
	    // whether we're now in charge
	    else
		this.statusTimeoutId = setTimeout("application.checkServerStatusChanged()", 2000);
	    
	    handler.success('Application initialized');
	}
	catch (err) {
	    handler.error('An error occured initializing the Application: ' + err);
	    throw err;
	}
	handler.finished();
    }
    

    /*
	 * Render Menu etc.
	 */
    this.render = function() {
	// select(null) renders the default view
	this.select(null);

    }

    /*
	 * Select a component. If id is null, select the first item on root level
 	 */
    this.select = function(selectId) {
	try {
	    // selectId must be either null or a number
	    if (selectId !== null && isNaN(parseInt(selectId)) )
		throw Error('Parameter for select must be either null or a number.');
	    
	    if (selectId !== null)
		selectId = parseInt(selectId);
	    
	    // if the location is locked, do not allow to change location
	    if (screenManager.isLockedLocation())
		return;
	    
	    
	    // check whether components-object is empty. its a associative array, because
	    // components may be empty 
	    if (!$.isEmptyObject(this.components)) {
		targetId = null;
		for (id in this.components) {
		    // dont use the strict === here, because id is a string and selectId a number
		    if (id == selectId || (!selectId && this.components[id].parentId === null)) {
			targetId = parseInt(id);
			break;
		    }
		}

		if (targetId === null || isNaN(targetId))
		    throw new Error('Passed id was not found "' + selectId + '"');


		this.selectedComponent = this.components[targetId];
		this.componentView.renderComponentView(this.selectedComponent, this.components, {'disabled': this.status!=this.SERVER_IN_CHARGE});
	    }
	   else {
		this.selectedComponent = null;
	    }

	    this.menuView.renderMenuView(this.components, {selected: this.selectedComponent});
	    this.infoBoxView.renderInfoBox(this.username, this.statusToString());
	}
	catch (err) {
	    alert("Error occured selecting the component: " + selectId + " (" + typeof(selectId) + ")\n" + err);
	}
    }
    
    
    
    /*
	 *  Process the update data given by /data/eventHistory/#timestamp
	 *  Returns true if at least one action changed / host changed its status. I.e, item.events.length > 0
	 */
    this.processEventHistoryData = function(data, options) {
	actionsProcessed = {};
	hostProcessed = {};
	
	if (!(parseInt(data.timestamp) > 0))
	    throw new Error('Invalid data object received. Timestamp: ' + data.timestamp)
	this.lastUpdateTimestamp = parseInt(data.timestamp);
	
	if (!(data.events instanceof Object))
	    throw new Error('Invalid data object received. events is not an object')
	
	
	for (i in data.events) {
	    item = data.events[i];
	    type = parseInt(item.type);
	    id = parseInt(item.id);
	    status = parseInt(item.status);

	    if (type != this.ACTION_STATUS_EVENT && type != this.HOST_EVENT)
		throw new Error('Unknown event type "' + item.type + "'");
	    
	    if (type == this.ACTION_STATUS_EVENT) {
		compId = parseInt(item.comp);
		comp = this.components[compId];
		if (!comp)
		    throw new Error('Component with id "' + item.comp + '" not found');

		if (!comp.hasAction(id))
		    throw new Error('Action does not belong to component (id: ' + item.id + ', comp: ' + compId + ')');

		if (status != 1 && status != 0)
		    throw new Error('Invalid Status code received "' + item.status  + ' (' + status + ')"');
		
		if (!actionsProcessed[compId] || actionsProcessed[compId][id] != true) {
		    comp.getAction(id).setActive(status == 1);
		    if (!actionsProcessed[compId])
			actionsProcessed[compId] = {};
		    actionsProcessed[compId][id] = true;
		}
	    }
	}
	
	
 	return data.events.length > 0;
    }
    
    
    /*
	 * Functions for frequently requesting eventHistoryData and updating user interface
	 * Only used if in charge fo the server. Otherwise see checkServerStatusChanged
	 */
    this.updateEventHistory = function()
    {
	var obj = this;
	$.ajax({
	    url: this.urlPrefix + '/data/eventHistory/' + this.lastUpdateTimestamp,
	    success: function(data) { obj.updateEventHistorySuccess(data); },
	    error:   function(data) { obj.updateEventHistoryError(data);   }
	});
    }
    this.updateEventHistorySuccess = function(data) {
	try {	    
	    changes = this.processEventHistoryData(data);
	    if (changes && this.selectedComponent) {
		this.componentView.updateComponentView(this.selectedComponent, this.components);
		this.menuView.renderMenuView(this.components);
	    }
	    
	    this.updateTimeoutId = setTimeout("application.updateEventHistory()", 2000);
	}
	catch (err) {
	    alert('An error occured processing History Data: ' + err);
	}
    }
    /*
	 * Callback function if requesting eventHistoryData failed.
	 * If error Code is 401 Unauthorized, check whether the server owner changed!
	 */
    this.updateEventHistoryError = function(data) {
	// check status for 401
	if (data.status == 401) {
	    // lock the screen
	    screenManager.lockDisplay(new WaitDialogView())
	    
	    // request the status data and check whether owner changed
	    $.ajax({
		url: this.urlPrefix + '/status',
		success: function(statusData) { 
		    if (statusData.status != this.SERVER_IN_CHARGE) {
			screenManager.unlock();
			screenManager.lockDisplay(new OwnerChangedDialogView())
		    }
		    else
			alert('Event History Data could not be loaded: 401 Unauthorized. Yet still in charge of the server [' + data.responseText + ']');
		},
		error:  function(data) { alert('Event History Data could not be loaded: 401 Unauthorized. Server Status could not be requested either [' + data.status + '; ' + data.responseText + ']'); }
	    });
	}
	else
	    alert('Event History Data could not be loaded [' + data.status + '; ' + data.responseText + ']');
    }
    
    /*
	 * Functions for checking whether the server status changed so that we're in charge.
	 * Only used if not in charge. Otherwise see updateEventHistory
	 */
    this.checkServerStatusChanged = function()
    {
	var obj = this;
	$.ajax({
	    url: this.urlPrefix + '/status',
	    success: function(data) { obj.checkServerStatusChangedSuccess(data); },
	    error:   function(data) { obj.checkServerStatusChangedError(data);   }
	});
    }
    this.checkServerStatusChangedSuccess = function(data) {
	try {
	    // if now in charge, reload
	    if (data.status == this.SERVER_IN_CHARGE)
		location.reload(true);
	    
	    // if not, check the stauts again soon
	    else
		this.statusTimeoutId = setTimeout("application.checkServerStatusChanged()", 2000);
	}
	catch (err) {
	    alert('An error occured processing Server Status ' + err);
	}
    }
    this.checkServerStatusChangedError = function(data) {
	alert('Server Status Data could not be loaded [' + data.status + '; ' + data.responseText + ']');
    }
    
    
    /*
	 * Start / Stop / Kill actions
	 */
    this.startAction = function(actionId, compId) {
	try {
	    component = this.getComponent(compId);
	    action = component.getAction(actionId);
	    
	    screenManager.lockLocation();
	    this.componentView.updateComponentView(this.selectedComponent, this.components);
	    this.menuView.renderMenuView(this.components);
	    
	    $.ajax({
		dataType: 'text',
		url: this.urlPrefix + '/exec/' + compId + '/' + actionId + '/start',
		success: function(data) {
		    application.startActionSuccess(data);
		},
		error:   function(data) {
		    application.startActionError(data);
		}
	    });
	}
	catch (err) {
	    alert("Error occured trying to start an Action:\n" + err);
	}
    }
    this.startActionSuccess = function(data)
    {
	screenManager.unlockLocation();
    }
    this.startActionError = function(data)
    {
	alert('Component could not be started [' + data.status + '; ' + data.responseText + ']');
    }

    this.stopAction = function(actionId, compId)
    {
	try {
	    component = this.getComponent(compId);
	    action = component.getAction(actionId);
	    
	    screenManager.lockLocation();
	    this.componentView.updateComponentView(this.selectedComponent, this.components);
	    this.menuView.renderMenuView(this.components);
	    
	    $.ajax({
		dataType: 'text',
		url: this.urlPrefix + '/exec/' + compId + '/' + actionId + '/stop',
		success: function(data) {
		    application.stopActionSuccess(data);
		},
		error:   function(data) {
		    application.stopActionSuccess(data);
		}
	    });
	}
	catch (err) {
	    alert("Error occured trying to stop an Action:\n" + err);
	}
    }

    
    this.stopActionSuccess = function(data)
    {
	screenManager.unlockLocation();
    }
    this.stopActionError = function(data)
    {
	alert('Component could not be stopped [' + data.status + '; ' + data.responseText + ']');
    }
    
    this.killAction = function(actionId, compId, func) {
	try {
	    component = this.getComponent(compId);
	    action = component.getAction(actionId);
	    
	    screenManager.lockLocation();
	    this.componentView.updateComponentView(this.selectedComponent, this.components);
	    this.menuView.renderMenuView(this.components);
	    
	    $.ajax({
		dataType: 'text',
		url: this.urlPrefix + '/exec/' + compId + '/' + actionId + '/kill',
		success: function(data) {
		    application.killActionSuccess(data);
		    
		    // if func is a function, it's used for the success
		    if (typeof(func) === 'function')
			func(data);
		    
		    // if it's an object, check for a success function
		    if(typeof(func) === 'object' && typeof(func.success) === 'function')
			func.success(data);
		},
		error:   function(data) {
		    application.killActionError(data);
		    
		    // check for an error function in the func object
		    if(typeof(func) === 'object' && typeof(func.success) === 'function')
			func.success(data);
		}
	    });
	}
	catch (err) {
	    alert("Error occured trying to stop an Action:\n" + err);
	}
    }
    this.killActionSuccess = function(data)
    {
	screenManager.unlockLocation();
    }
    this.killActionError = function(data)
    {
	alert('Component could not be killed [' + data.status + '; ' + data.responseText + ']');
    }

    /*
     * Start/Stop an entire Group
     */
    this.startGroup = function(compId)
    {
	var component = this.components[compId];
	// start the main action first
	this.startAction(component.getMainAction().id, component.id);

	// start all children afterwards
	for (var id in component.children)
	    this.startGroup(id);
    }
    this.stopGroup = function(compId)
    {
	var component = this.components[compId];
	// stop all child components first
	for (var id in component.children)
	    this.stopGroup(id);

	// when all children are stopped, stop the action itself
	this.stopAction(component.getMainAction().id, component.id);
    }
	    
    
    this.statusToString = function() {
	if (this.status == this.SERVER_AVAILABLE)
	    return 'Server available';
	if (this.status == this.SERVER_IN_CHARGE)
	    return 'In charge';
	if (this.status == this.SERVER_NOT_AVAILABLE)
	    return 'Server not available';
	return 'ERROR';
    }
    
    this.showServerReservation = function() 
    {
	this.calendarTrigger.trigger('click');
	this.serverReservationView.renderCalendarView();
	return false;
    }
    
    this.addReservation = function(start, end)
    {
	
	escapedStart = this.urlEncodeDate(start);
	escapedEnd = this.urlEncodeDate(end);
	
	if (start === null || end === null)
	    throw new Error('Invalid Start or End-Date')

	// check if we are reserving the server for right now
	var now = new Date();
	if (start < now && now < end)
	    screenManager.lockDisplay(new ServerPreparesReservation());
	
	$.ajax({
	    url: this.urlPrefix + '/reservations/add/' + escapedStart + '/' + escapedEnd,
	    dataType: 'text',
	    success: function(data) { application.addReservationSuccess(data, start, end) },
	    error:   function(data) { application.addReservationError(data) }
	});
    }
    this.addReservationSuccess = function(data, start, end) 
    {
	id = parseInt(data);
	if (isNaN(id))
	    return this.addReservationError({'status': 200, 'responseText': 'The returned id is not a valid number: "' + data + '"'});
	
	title = this.username + ' ' + start.getHours() + ':' + start.getMinutes() + ' - ' + end.getHours() + ':' + end.getMinutes();
	this.reservations.push({'title': title, 'id': id, 'start': start, 'end': end, 'owner': true});
	this.serverReservationView.renderCalendarView();
    }
    this.addReservationError = function(data)
    {
	alert('ERROR: ' + data.responseText);
    }
    this.killReservation = function(id)
    {
	$.ajax({
	    url: this.urlPrefix + '/reservations/kill/' + id,
	    dataType: 'text',
	    success: function(data) { application.killReservationSuccess(data, id) },
	    error:   function(data) { application.killReservationError(data) }
	});
    }
    this.killReservationSuccess = function(data, id) 
    {
	for (i in this.reservations)
	    if (this.reservations[i].id == id) {
		this.reservations.splice(i, 1);
		break;
	    }
	this.serverReservationView.renderCalendarView();
    }
    this.killReservationError = function(data)
    {
	alert('ERROR: ' + data.responseText);
    }
    
    this.extendReservation = function(id, end, oldEnd)
    {
	escapedEnd = this.urlEncodeDate(end);
	
	if (end === null)
	    throw new Error('End-Date')

	var now = new Date();
	if (now < end && this.status != this.SERVER_IN_CHARGE)
	    screenManager.lockDisplay(new ServerPreparesReservation());
	
	$.ajax({
	    url: this.urlPrefix + '/reservations/extend/' + id + '/' + escapedEnd,
	    dataType: 'text',
	    success: function(data) { application.extendReservationSuccess(data, id, end) },
	    error:   function(data) { application.extendReservationError(data) }
	});
    }
    this.extendReservationSuccess = function(data, id, end) 
    {
	for (i in this.reservations)
	    if (this.reservations[i].id == id) {
		start = this.reservations[i].start;
		title = this.username + ' ' + start.getHours() + ':' + start.getMinutes() + ' - ' + end.getHours() + ':' + end.getMinutes();
		this.reservations[i].title = title;
		this.reservations[i].end = end;
		
		this.serverReservationView.renderCalendarView();
		break;
	    }
    }
    this.extendReservationError = function(data)
    {
	alert('ERROR: ' + data.responseText);
    }
    
    this.urlEncodeDate = function(date)
    {
	if (!(date instanceof Date))
	    return null;
	
	return date.getFullYear() + "-" + (date.getMonth()+1) + "-" + date.getDate() + "-" + date.getHours() + "-" + date.getMinutes()
    }
    
    this.urlDecodeDate = function(dateStr)
    {
	if (typeof(dateStr) != "string" || !(dateStr.match instanceof Function))
	    return null;
	
	result = dateStr.match(/(\d+)\-(\d+)\-(\d+)\-(\d+)\-(\d+)/);
	if (result === null)
	    return null;
	
	
	// months in javascript -1
	date = new Date(result[1], result[2]-1, result[3], result[4], result[5]);
	if (isNaN(date.valueOf()))
	    return null;
	
	return date;
    }
    
    
    this.editComponent = function()
    {
	try {
	    // if the location is locked, do not allow to change location
	    if (screenManager.isLockedLocation())
		return;
	    
	    // if no component is selected, simply return
	    if (!this.selectedComponent)
		return;
	    
	    // if the current component is running, ask the user to stop it first
	    if (this.selectedComponent.actionsRunning()) 
		alert('The current component is still running. Please stop it first');
	    
	    else {
		// clone the current component, to avoid changes being made to the actual component
		this.componentView.renderComponentEditView(this.selectedComponent.clone(), this.components);

		// no more component selected
		this.selectedComponent = null;
	    }
  	}	
	catch (err) {
	    alert ("Error occured trying to edit component: \n" + err);
	    console.log(err);
	}
    }
    
    this.createComponent = function() 
    {
	try {
	    // if the location is locked, do not allow to change location
	    if (screenManager.isLockedLocation())
		return;
	    
	    var compId = this.getUniqueTemporaryId();
	    var actionId = this.getUniqueTemporaryId();
	    var actions = {}
	    actions[actionId] = new Action(actionId, "New Component");
	    
	    var comp = new Component(compId, null, "New Component", null, actions);
	    this.componentView.renderComponentEditView(comp, this.components);

	    // no more component selected
	    this.selectedComponent = null;
	}
	catch (err) {
	    alert ("Error occured trying to create a new component: \n" + err);
	    console.log(err);
	}
    }
    
    this.saveComponent = function(component)
    {
	try {
	    // reset the last update timestamp
	    this.lastUpdateTimestamp = 0;
	    
	    // lock the interface
	    this.select(component.id > 0 ? component.id : null);
	    screenManager.lockLocation();
	    if (this.selectedComponent)
		    this.componentView.updateComponentView(this.selectedComponent, this.components);
	    this.menuView.renderMenuView(this.components);
	    
	    $.ajax({
		url: this.urlPrefix + '/store/component?json=' + component.createJSONString(),
		success: function(data) { application.reloadComponents() },
		error:   function(data) { application.saveComponentError(data) }
	    });
	}
	catch (err) {
	    alert ("Error occured trying to save component: \n" + err);
	    console.log(err);
	}
    }
    
    this.reloadComponents = function(selectId)
    {
	try {
	    // if nothing was passed for selectId, use the current id
	    if (selectId === undefined) {
	    	if (this.selectedComponent)
			selectId = this.selectedComponent.id;
		else
			selectId = null;
	    }
	    
	    // reload all components
	    var compDataSuccess = function(data) {
		// when the comp data is successfully loaded and parsed,
		// unlock the application and update the views
		var handler = {
		    'success': function() { application.reloadComponentsSuccess(selectId); },
		    'error': function(msg) { alert(msg); }
		};
		application.compDataSuccess(data, handler);
	    };
	    this.loadCompData(compDataSuccess, application.saveComponentError);
	}
	catch (err) {
	    alert("Error occured updating the component: \n" + err);
	    console.log(err);
	}
    }
    this.saveComponentError = function(data) {
		alert('Component could not be updated [' + data.status + '; ' + data.responseText + ']');
    }
    this.reloadComponentsSuccess = function(selectId) {
	screenManager.unlockLocation();
	// we must reselect, since the objects were recreated
	this.select(selectId);
    };

    
    this.deleteComponent = function()
    {
	try {
	    // if the location is locked, do not allow to change location
	    if (screenManager.isLockedLocation())
		return;
	    
	    // if no component is selected, simply return
	    if (!this.selectedComponent)
		return;

    	    if (this.selectedComponent.actionsRunning()) {
		alert('The current component is still running. Please stop it first');
		return;
	    }

	    	    
	    // send a request to the server
	    var compId = this.selectedComponent.id;
	    $.ajax({
		url: this.urlPrefix + '/delete/' + compId,
		dataType: 'text',
		success: function(data) { application.reloadComponents(null) },
		error:   function(data) { application.deleteComponentError(data) }
	    });
	}
	catch (err) {
	    alert("Error occured trying to delete the component:\n" + err);
	}
    }

    this.deleteComponentError = function(data) {
	alert('Component could not be deleted [' + data.status + '; ' + data.responseText + ']');
    }
	
    // used to load the log file
    this.loadLog = function(actionId, callback) 
    {
	try {
	    // if the location is locked, do not allow to change location
	    if (screenManager.isLockedLocation())
		return;
				
	    // if no component is selected, simply return
	    if (!this.selectedComponent)
		return;
				
	    var compId = this.selectedComponent.id;
	    // send a request to the server
	    var compId = this.selectedComponent.id;
	    $.ajax({
		url: this.urlPrefix + '/exec/' + compId + '/' + actionId + '/status',
		dataType: 'text',
		success: function(data) { if(application.selectedComponent && compId == application.selectedComponent.id) callback(data); },
		error:   function(data) { application.loadLogError(data); }
	    });
	}
	catch (err) {
	    alert("Error occured trying to load the component's logfiles:\n" + err);
	}
    }
    this.loadLogError = function(data) {
	alert('Component\'s logfiles could not be loaded [' + data.status + '; ' + data.responseText + ']');
    }

    this.hostManager = function()
    {
	try {
	    this.componentView.renderHostManagerView();
	}
	catch(err) {
	    alert('Host Manager could not be rendered. Error:\n' + err);
	}
    }

    // function is used by hostmanager to check if the currenlty selected
    // host has active comopnents
    this.hostHasRunningComponent = function(host)
    {
	for (compId in this.components) {
	    var component = this.components[compId];
	    if (component.hostId == host.id && component.actionsRunning())
		return true;
	}
	return false;
    }
    this.submitHost = function(hostId, hostname, username, password, port)
    {
	$.ajax({
	    // TODO: send data via post
	    url: this.urlPrefix + '/store/host/' + hostId + '/' + hostname + '/' + username + '/' + password + '/' + port,
	    success: function(data) { application.submitHostSuccess(data); },
	    error:   function(data) { application.submitHostError(data); }
	});
    }
    this.submitHostSuccess = function(data)
    {
	try {
	    Host.updateHost(data);
	    this.select(null);
	}
	catch (err) {
	    alert('Error occured updating the host. Error:\n' + err);
	}
    }
    this.submitHostError = function(data)
    {
	alert('Remote Host could not be updated [' + data.status + '; ' + data.responseText + ']');
    }
    
    // User management 
    this.userManager = function()
    {
	try {
	    // if the location is locked, do not allow to change location
	    if (screenManager.isLockedLocation())
		return;
	    
	    	    
	    // send a request to the server
	    var view = this.componentView;
	    $.ajax({
		url: this.urlPrefix + '/privileges/all',
		success: function(data) { view.renderUserManagerView(data); },
		error:   function(data) { alert('User Privileges could not be loaded [' + data.status + '; ' + data.responseText + ']'); }
	    });
	}
	catch (err) {
	    alert("Error occured trying to manage the users:\n" + err);
	}
    }
    this.submitPrivileges = function(bitmasks)
    {
	$.ajax({
	    url: this.urlPrefix + '/privileges/submit',
	    data: bitmasks,
	    dataType: 'text',
	    success: function(data) { application.submitPrivilegesSuccess(data); },
	    error:   function(data) { application.submitPrivilegesError(data); }
	});
    }
    this.submitPrivilegesSuccess = function(data)
    {
	try {
	    this.select(null);
	}
	catch (err) {
	    alert('Error occured to go home. Error:\n' + err);
	}
    }
    this.submitPrivilegesError = function(data)
    {
	alert('Remote Privileges could not be updated [' + data.status + '; ' + data.responseText + ']');
    }

})();
