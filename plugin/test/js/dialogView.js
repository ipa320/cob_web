var LoadingDialogView = function(title, msg) {
	this.id = null;
	this.title = title;
	this.msg = msg;
	this.container = $(document.createElement('div'));
	this.ul = null;
	

	this.create = function(id) {
		this.id = id;
		this.container.attr('id', id);
		this.container.attr('title', this.title);
		this.container.addClass('dialogView');
		this.container.addClass('loadingDialogView');
		this.container.html('<img src="images/ajax-loader-trans.gif" class="loader"/><p class="msg">' + this.msg + '</p><ul></ul>');
		this.ul = this.container.find('ul'); 
	}
	this.getContainer = function() {
		return this.container;
	}

	this.addBullet = function(text) {
		this.ul.append('<li><span class="ui-icon ui-icon-circle-check"></span>' + text + '</li>');
	}	
}
