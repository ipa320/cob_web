var application = new (function() {
	this.SERVER_AVAILABLE = 1;
	this.SERVER_IN_CHARGE = 2;
	this.SERVER_NOT_AVAILABLE = -1;
	
	this.hosts = null;
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
	
	// options defined for the next redraw
	this.refreshOptions = []
	
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
		if (!(views instanceof Object)) { // || !(views.menuView instanceof jQuery) || views.menuView.size() == 0 || !(views.componentView) instanceof jQuery || views.componentView.size() == 0) {
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
			'autoDimensions'	: false,
			'autoScale'			: false,
			'width'				: '95%',
			'height'			: '95%',
			'type'				: 'inline',
			'href'				: '#' + this.serverReservationView.attr('id'),
			'transitionIn'		: 'none',
			'transitionOut'		: 'none'
		});		
		
		
		this.username = username;

		// set some basic ajax settings
		$.ajaxSetup({
			dataType: 'json'
		});
		handler.success('Initialized JavaScript');

		// Check whether the server is online and a user logged in
		this.checkServerStatus(handler);
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
	this.checkServerStatus = function(handler) {
		$.ajax({
			url: this.urlPrefix + '/status',
			success: function(data) { application.statusDataSuccess(data, handler); },
			error:   function(data) { application.statusDataError(data, handler);   }
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
				
			// load host data next
			Host.loadHostData(this.urlPrefix,
				function() {
					handler.success('Host Data Received');

					// load component data next
					application.loadCompData(handler);
				},
				function(data) {
					console.log(data);
					handler.error('Host Data could not be loaded [' + data.status + '; ' + data.responseText + ']');
				}
			);
		}
		catch (err) {
			handler.error('Error occured while parsing host data:\n' + err);
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
	this.loadCompData = function(handler)  {
		$.ajax({
			url: this.urlPrefix + '/data/comp',
			success: function(data) { application.compDataSuccess(data, handler); },
			error:   function(data) { application.compDataError(data, handler);   }
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
			
			// load the reservations
			this.loadReservations(handler);
		}
		catch (err) {
			handler.error('Error occured while parsing component data:\n' + err);
		}
	}
	this.compDataError = function(data, handler) {
		handler.error('Comp Data could not be loaded [' + data.status + '; ' + data.responseText + ']');
	}
	
	/*
	 * Load Reservations
	 */
	this.loadReservations = function(handler)  {
		$.ajax({
			url: this.urlPrefix + '/reservations/get',
			success: function(data) { application.reservationDataSuccess(data, handler); },
			error:   function(data) { application.reservationDataError(data, handler);   }
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
			
			// load event history data next
			this.loadEventHistoryData(handler);
		}
 		catch (err) {
			handler.error('Error occured while parsing component data:\n' + err);
		}
	}
	this.reservationDataError = function(data, handler) {
		handler.error('Reservation data could not be loaded [' + data.status + '; ' + data.responseText + ']');
	}
	

	
	/*
	 * Load / parse Event History Data from Remote Server+
	 * only load data if we're in charge. Otherwise skip this step
	 */
	this.loadEventHistoryData = function(handler) {
		if (this.status == this.SERVER_IN_CHARGE) {
			$.ajax({
				url: this.urlPrefix + '/data/eventHistory/0',
				success: function(data) { application.eventHistoryDataSuccess(data, handler); },
				error:   function(data) { application.eventHistoryDataError(data, handler);   }
			});
		}
		else {
			handler.success('Skipping History Data');
			this.finalApplicationInitialization(handler);
		}
	}
	this.eventHistoryDataSuccess = function(data, handler) {
		try {
			this.processEventHistoryData(data);
			handler.success('Event History Data Received');
			this.finalApplicationInitialization(handler);
		}
		catch (err) {
			handler.error('An error occured processing History Data: ' + err);
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
			if (selectId != null && typeof(selectId) != 'number')
				throw Error('Parameter for select must be either null or a number.');
			
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
			
			if (type !== this.ACTION_STATUS_EVENT && type !== this.HOST_EVENT)
				throw new Error('Unknown event type "' + item.type + "'");
			
			if (type === this.ACTION_STATUS_EVENT) {
				compId = parseInt(item.comp);
				comp = this.components[compId];
				if (!comp)
					throw new Error('Component with id "' + item.comp + '" not found');
				
				if (!comp.hasAction(id))
					throw new Error('Action does not belong to component (id: ' + item.id + ', comp: ' + compId + ')');
					
				if (status !== 1 && status !== 0)
					throw new Error('Invalid Status code received "' + item.status + '"');
				
				if (actionsProcessed[id] !== true) {
					comp.getAction(id).setActive(status === 1);
					actionsProcessed[id] = true;
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
			options = {'forceComponentUpdate': false};
			$.extend(options, this.refreshOptions);
			
			changes = this.processEventHistoryData(data);
			if (changes && this.selectedComponent) {
				this.componentView.updateComponentView(this.selectedComponent, this.components, null, options.forceComponentUpdate);
				this.menuView.renderMenuView(this.components);
			}
			
			// empty the refreshOptions
			this.refreshOptions = {}
			
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
			this.componentView.updateComponentView(this.selectedComponent, this.components, null, true);
			this.menuView.renderMenuView(this.components);
			
			$.ajax({
				dataType: 'text',
				url: this.urlPrefix + '/exec/' + compId + '/' + actionId + '/start',
				success: function(data) {
					application.startActionSuccess(data);
					
					// if func is a function, it's used for the success
					if (typeof(func) === 'function')
						func(data);
					
					// if it's an object, check for a success function
					if(typeof(func) === 'object' && typeof(func.success) === 'function')
						func.success(data);
				},
				error:   function(data) {
					application.startActionError(data);
					
					// check for an error function in the func object
					if(typeof(func) === 'object' && typeof(func.success) === 'function')
						func.success(data);
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
		this.refreshOptions['forceComponentUpdate'] = true;		
	}
	this.startActionError = function(data)
	{
		alert('Component could not be started [' + data.status + '; ' + data.responseText + ']');
	}

	this.stopAction = function(actionId, compId, func)
	{
		try {
			component = this.getComponent(compId);
			action = component.getAction(actionId);
			
			screenManager.lockLocation();
			this.componentView.updateComponentView(this.selectedComponent, this.components, null, true);
			this.menuView.renderMenuView(this.components);
			
			$.ajax({
				dataType: 'text',
				url: this.urlPrefix + '/exec/' + compId + '/' + actionId + '/stop',
				success: function(data) {
					application.stopActionSuccess(data);
					
					// if func is a function, it's used for the success
					if (typeof(func) === 'function')
						func(data);
					
					// if it's an object, check for a success function
					if(typeof(func) === 'object' && typeof(func.success) === 'function')
						func.success(data);
				},
				error:   function(data) {
					application.stopActionSuccess(data);
					
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
	this.stopActionSuccess = function(data)
	{
		screenManager.unlockLocation();
		this.refreshOptions['forceComponentUpdate'] = true;		
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
			this.componentView.updateComponentView(this.selectedComponent, this.components, null, true);
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
		this.refreshOptions['forceComponentUpdate'] = true;	
	}
	this.killActionError = function(data)
	{
		alert('Component could not be killed [' + data.status + '; ' + data.responseText + ']');
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
	
	this.extendReservation = function(id, end)
	{
		
		escapedEnd = this.urlEncodeDate(end);
		
		if (end === null)
			throw new Error('End-Date')
			
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
				this.componentView.renderComponentEditView(this.selectedComponent.clone());

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
			$.ajax({
				url: this.urlPrefix + '/store/?json=' + component.createJSONString(),
				success: function(data) { application.saveComponentSuccess(data, component) },
				error:   application.saveComponentError
			});
		}
		catch (err) {
			alert ("Error occured trying to save component: \n" + err);
		}
	}
	
	this.saveComponentSuccess = function(idMap, component)
	{
		try {
			if (component.id < 0)
				component.id = idMap[component.id];
			
			// remap the actions
			newActions = {}
			
			// go through all the component's actions, delete empty actions / commands
			// and remap the ids
			
			for (id in component.actions) {
				console.log(id)
				id = parseInt(id);
				var action = component.actions[id];
				
				// update the action's id. If the id was remapped, store it in a 
				// newly created array with the remapped id as key value.
				if (id < 0) {
					action.id = idMap[id];
					newActions[idMap[id]] = action;
				}
				else
					newActions[id] = action;
				
				// set the compId (dont bother to check if it's negative, since it
				// must be the same as the component's in any case)
				action.compId = component.id
									
				// remap the shellCommands
				for (i in action.startCommands) {
					id = action.startCommands[i].id;
					
					// skip the command if it's empty
					if (!action.startCommands[i].command.trim())
						action.startCommands.splice(i, 1);
					else if (id < 0)
						action.startCommands[i].id = idMap[id];
				}
				for (i in action.stopCommands) {
					id = action.stopCommands[i].id;
					if (!action.stopCommands[i].command.trim())
						action.stopCommands.splice(i, 1);
					else if (id < 0)
						action.stopCommands[i].id = idMap[id];
				}
			}
			component.actions = newActions;
					
			application.components[component.id] = component;
			application.select(component.id);
		}
		catch (err) {
			alert("Error occured updating the component: \n" + err);
		}
	}
	this.saveComponentError = function(data) {
		alert('Component could not be updated [' + data.status + '; ' + data.responseText + ']');
	}
	
	this.deleteComponent = function()
	{
		try {
			// if the location is locked, do not allow to change location
			if (screenManager.isLockedLocation())
				return;
				
			// if no component is selected, simply return
			if (!this.selectedComponent)
				return;
				
			// send a request to the server
			var compId = this.selectedComponent.id;
			$.ajax({
				url: this.urlPrefix + '/delete/' + compId,
				dataType: 'text',
				success: function(data) { application.deleteComponentSuccess(compId) },
				error:   function(data) { application.deleteComponentError(data) }
			});
		}
		catch (err) {
			alert("Error occured trying to delete the component:\n" + err);
		}
	}
	this.deleteComponentSuccess = function(id)
	{
		delete this.components[id];
		
		// rerender 
		this.select(null)
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
})();
