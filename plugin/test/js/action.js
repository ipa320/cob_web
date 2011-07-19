var Action = function(id, name, compId, description, dependencies, startCmds, stopCmds) {
	this.id = id;
	this.name = name;
	this.compId = compId;
	this.description = description	 || "";
	this.dependencies = dependencies || [];
	this.startCommands = startCmds   || [];
	this.stopCommands = stopCmds	 || [];
	
	
	this._active = false;
	this._lastChange = 0;

	this.getLastChange = function() {
		return this._lastChange;
	}
	this.updateLastChange = function() {
		this._lastChange = new Date().getTime();
	}
	
	this.isActive = function() {
		return this._active === true;
	}
	// returns true if the status was changed, false otherwise
	this.setActive = function(active) {
		newActive = active === true;
		if (newActive != this._active) {
			this._active = newActive;
			this.updateLastChange();
			return true;
		}
		return false;
	}
	
	this.canStart = function() {
		return this.startCommands.length > 0;
	}
	this.canStop = function() {
		return this.stopCommands.length > 0;
	}
	
	this.createJSONObject = function() {
		return {
			'id':			this.id,
			'name':			this.name,
			'compId':		this.compId,
			'description':	this.description,
			'dependencies':	this.dependencies,
			'startCommands':this.startCommands,
			'stopCommands':	this.stopCommands
		};
	}
	this.createJSONString = function()
	{
		return JSON.stringify(this.createJSONObject());
	}
	
	// clone
	this.clone = function() {
		// slice(0) creates a copy of the array
		return new Action(this.id, this.name, this.compId, this.description, this.dependencies.slice(0), this.startCommands.slice(0), this.stopCommands.slice(0));
	}
}
