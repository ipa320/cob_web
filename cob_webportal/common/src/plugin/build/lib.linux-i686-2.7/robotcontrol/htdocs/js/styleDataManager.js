var styleDataManager = new (function() {
    this._expandedComponents = [];

    // all functions can be passed either a number (the component's id)
    // or the component object itself (with a id property)
    this.getId = function(component) {
	var id = null;
	if (!isNaN(parseInt(component)))
	    return parseInt(component);
	else if (component.id)
	    return component.id;
	else
	    throw new Error('Invalid parameter passed for styleDataManager');
    };

    this.expand = function(component) {
	this._expandedComponents.push(this.getId(component));
    };

    this.close = function(component) {
	var pos = $.inArray(this.getId(component), this._expandedComponents);
	if (pos > -1)
	    this._expandedComponents.splice(pos,1);
    }
	
    this.isExpanded = function(component) {
	return $.inArray(this.getId(component), this._expandedComponents) > -1;
    }
})();