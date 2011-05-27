var application = new (function() {
	this.SERVER_AVAILABLE = 1;
	this.SERVER_IN_CHARGE = 2;
	this.SERVER_NOT_AVAILABLE = -1;
	
	this.hosts = null;
	this.components = null;
	this.selectedComponent = null;
	
	// timeout for frequent updates
	this.updateTimeoutId = -1;
	
	// timestamp of last request
	this.lastUpdateTimestamp = 0;
	
	// available events
	this.ACTION_STATUS_EVENT=1;
	this.HOST_EVENT = 2;
	
	// options defined for the next redraw
	this.refreshOptions = {}
	
	
	

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
		requiredViews = ['menuView', 'componentView', 'infoBoxView'];
		for (i in requiredViews) {
			view = requiredViews[i];
			if (!views[view] instanceof jQuery || views[view].size() == 0) {
				handler.error('View "' + view + '" is not an valid jQuery-Object');
				return;
			}
		}
		
		this.menuView = views.menuView;
		this.componentView = views.componentView;
		this.infoBoxView = views.infoBoxView;
		
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
			throw new Error('Invalid component id');
			
		component = this.components[compId];
		if (component === undefined)
			throw new Error('Invalid Component Id passed');
			
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
			this.loadHostData(handler);
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
	 * Load / parse Host Data from Remote Server
	 */
	this.loadHostData = function(handler)  {
		var obj = this;
		$.ajax({
			url: this.urlPrefix + '/data/host',
			success: function(data) { obj.hostDataSuccess(data, handler); },
			error:   function(data) { obj.hostDataError(data, handler);   }
		});
	}
	this.hostDataSuccess = function(hostData, handler) {
		try {
			this.hosts = {}
			
			for (id in hostData) {
				host = hostData[id];
				if (!id || !host.hostname || !host.user || !host.port)
					throw new Error('Invalid Host-Object received');
				this.hosts[id] = new Host(id, host.hostname, host.user, host.port);
			}
				
			handler.success('Host Data Received');

			// load component data next
			this.loadCompData(handler);
		}
		catch (err) {
			handler.error('Error occured while parsing host data:\n' + err);
		}

	}
	this.hostDataError = function(data, handler) {
		handler.error('Host Data could not be loaded [' + data.status + ']');
	}


	/*
	 * Load / parse Component Data from Remote Server
	 */
	this.loadCompData = function(handler)  {
		var obj = this;
		$.ajax({
			url: this.urlPrefix + '/data/comp',
			success: function(data) { obj.compDataSuccess(data, handler); },
			error:   function(data) { obj.compDataError(data, handler);   }
		});
	}
	this.compDataSuccess = function(compData, handler) {
		try {
			this.components = {}
			
			for (id in compData) {
				comp = compData[id];
				// check whether all required fields are set. host, parentId may be null
				if (!id || !comp || !comp.name || !comp.actions || !(comp.actions instanceof Object))
					throw new Error('Invalid Comp-Object received')

				// parse the actions first
				actions = {};
				for (actionId in comp.actions) {
					action = comp.actions[actionId];
					// check whether all required fields are set. description might be null
					if (!actionId || !action || !action.name || !action.dependencies || !(action.dependencies instanceof Object))
						throw new Error('Invalid Action-Object received')
					
					actions[actionId] = new Action(actionId, action.name, id, action.desc, action.dependencies)
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
			
			// load event history data next
			this.loadEventHistoryData(handler);
		}
		catch (err) {
			handler.error('Error occured while parsing component data:\n' + err);
		}

	}
	this.compDataError = function(data, handler) {
		handler.error('Comp Data could not be loaded [' + data.status + ']');
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
		handler.error('Event History Data could not be loaded [' + data.status + ']');
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
		// if the location is locked, do not allow to change location
		if (screenManager.isLockedLocation())
			return;
		
		
		// check whether components-object is empty. its a associative array, so 
		// we cannot use length
		var hasComponents=false;
		for (i in this.components) {
			hasComponents=true;
			break;
		}
		
		// components may be empty 
		if (hasComponents) {
			targetId = null;
			for (id in this.components) {
				if (id === selectId || (!selectId && this.components[id].parentId === null)) {
					targetId = id;
					break;
				}
			}

			if (targetId === null)
				throw new Error('Passed id was not found "' + selectId + '"');

			if (this.selectedComponent === this.components[targetId])
				return;

			this.selectedComponent = this.components[targetId];
			this.componentView.renderComponentView(this.selectedComponent, this.components, {'disabled': this.status==this.SERVER_NOT_AVAILABLE});
		}
		else {
			this.selectedComponent = null;
		}

		this.menuView.renderMenuView(this.components, {selected: this.selectedComponent});
		this.infoBoxView.renderInfoBox(this.username, this.statusToString());
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
	 * Function for frequently updating event History
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
	this.updateEventHistorySuccess = function(data, handler) {
		try {
			options = {'forceComponentUpdate': false};
			$.extend(options, this.refreshOptions);
			
			changes = this.processEventHistoryData(data);
			if (changes) {
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
	this.updateEventHistoryError = function(data, handler) {
		alert('Event History Data could not be loaded [' + data.status + ']');
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
				url: this.urlPrefix + '/exec/' + compId + '/' + actionId + '/start',
				success: function(data) { application.startActionSuccess(data) },
				error:   function(data) { application.startActionSuccess(data) }//startActionError
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

		
	this.stopAction = function(actionId, compId) {
		try {
			component = this.getComponent(compId);
			action = component.getAction(actionId);
			
			screenManager.lockLocation();
			this.componentView.updateComponentView(this.selectedComponent, this.components, null, true);
			this.menuView.renderMenuView(this.components);
			
			$.ajax({
				url: this.urlPrefix + '/exec/' + compId + '/' + actionId + '/stop',
				success: function(data) { application.startActionSuccess(data); },
//				success: function(data) { application.stopActionSuccess(data); },
				error:   function(data) { application.startActionSuccess(data); }
//				error:   function(data) { application.stopActionSuccess(data); }
			});
		}
		catch (err) {
			alert("Error occured trying to stop an Action:\n" + err);
		}
	}
	this.stopActionSuccess = function(data)
	{
	}
	
	this.killAction = function(actionId, compId) {
		try {
			component = this.getComponent(compId);
			action = component.getAction(actionId);
			
			screenManager.lockLocation();
			this.componentView.updateComponentView(this.selectedComponent, this.components, null, true);
			this.menuView.renderMenuView(this.components);
			
			$.ajax({
				url: this.urlPrefix + '/exec/' + compId + '/' + actionId + '/kill',
				success: function(data) { application.startActionSuccess(data); },
//				success: function(data) { application.stopActionSuccess(data); },
				error:   function(data) { application.startActionSuccess(data); }
//				error:   function(data) { application.stopActionSuccess(data); }
			});
		}
		catch (err) {
			alert("Error occured trying to stop an Action:\n" + err);
		}
	}
	this.stopActionSuccess = function(data)
	{
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
})();
