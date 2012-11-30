$.fn.autoSet = function(obj) {

	autoSet = obj.autoSet();
	for (key in autoSet) {
		value = autoSet[key];
		this.find(".autoSet_" + key).text(value);
	}

};
