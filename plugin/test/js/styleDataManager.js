var styleDataManager = new (function() {
	this.actionTabsClosed = {};
	this.isActionTabClosed = function(id) {
		return this.actionTabsClosed[id] === true;
	};
	this.actionTabOpened = function(id) {
		this.actionTabsClosed[id] = false;
	};
	this.actionTabClosed = function(id) {
		this.actionTabsClosed[id] = true;
	};
	this.toggleActionTab = function(id) {
		if (this.isActionTabClosed(id))
			this.actionTabOpened(id);
		else
			this.actionTabClosed(id);
	};
})();
