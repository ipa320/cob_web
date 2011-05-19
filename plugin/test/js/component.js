var Component = function(id, hostId, name, parentId, actions) {
	this.id = id;
	this.name = name;
	this.running = false;

	// make sure it's null if not defined
	this.hostId = hostId || null;
	
	// make sure it's null if not defined
	this.parentId = parentId || null;

	this.actions = actions;

	this.parent = null;
	this.children = {};
	


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
	
/*	this.actions = []
	this.addAction = function(action) {
		if (! action instanceof Action)
			throw new Error("Action is of a wrong type");
		this.actions.push(action);
	}
*/
}
