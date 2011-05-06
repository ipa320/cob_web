var Component = function(id, title, parentId) {
	this.id = id;
	this.title = title;

	this.parentId = parentId;
	this.parent = null;

	this.actions = []
	this.addAction = function(action) {
		if (! action instanceof Action)
			throw new Error("Action is of a wrong type");
		this.actions.push(action);
	}


	this.autoSet = function() {
		dict = {};
		dict['id'] = this.id;
		dict['title'] = this.title;
	}
}
