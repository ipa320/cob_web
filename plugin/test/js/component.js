var Component = function(id, hostId, name, parentId, actions) {
	this.id = id;
	this.name = name;
	this.running = false;

	// make sure it's null if not defined
	this.hostId = hostId || null;
	
	// make sure it's null if not defined
	this.parentId = parentId || null;

	// associative array with action id as key
	this.actions = actions || {};

	this.parent = null;
	this.children = {};
	
	// Every componetn must have a main action that has the same name as the
	// component
	this._mainAction = null;
	for (i in this.actions) 
		if (this.actions[i].name == this.name) {
			this._mainAction = this.actions[i];
			break;
		}
	
	if (this._mainAction === null)
		throw new Error("The Component has no main Component. Name: " + this.name);
	
	
	
	this.getMainAction = function() {
		return this._mainAction;
	}


	this.hasAction = function(actionId) {
		return this.actions[actionId] != undefined;
	}
	this.getAction = function(actionId) {
		if (!this.hasAction(actionId))
			throw new Error('Requested Action does not exist: ' + actionId)
		return this.actions[actionId];
	}
	// returns true if all actions are running
	this.allActionsRunning = function() {
		for (actionId in this.actions)
			if (!this.actions[actionId].isActive())
				return false;
		return true;
	}
	// returns true if at least one action is running
	this.actionsRunning = function() {
		for (actionId in this.actions)
			if (this.actions[actionId].isActive())
				return true;
		return false;
	}
	
	this.addAction = function(action) {
	    if (! (action instanceof Action))
		throw new Error("Action is of a wrong type");
	    this.actions[action.id] = action;
	}

	this.createJSONObject = function()
	{
		// create the json data
		var json_object = {
			'id': 		this.id,
			'hostId':	this.hostId,
			'parentId':	this.parentId,
			'actions':	[]
		};
		
		for (i in this.actions)
			json_object.actions.push(this.actions[i].createJSONObject());
		
		return json_object;
	}
	this.createJSONString = function()
	{
//		alert(JSON.stringify(this.createJSONObject()));
		return JSON.stringify(this.createJSONObject());
	}
	
	

	// clone
	this.clone = function() {
		// clone all the actions
		clonedActions = [];
		for (i in actions)
			clonedActions[i] = actions[i].clone();
		return new Component(this.id, this.hostId, this.name, this.parentId, clonedActions);
	}
}

