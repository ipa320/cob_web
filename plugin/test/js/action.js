var Action = function(id, title, description) {
	this.id = id;
	this.title = title;
	this.lastChange = new Date().getTime();
	this.description = description;
}
