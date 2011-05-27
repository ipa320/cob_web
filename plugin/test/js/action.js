var Action = function(id, name, compId, description, dependencies) {
	this.id = id;
	this.name = name;
	this.compId = compId;
	this.description = description;
	this.dependencies = dependencies;
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
	
	// update last Change
	this.updateLastChange();
}
