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
	this.destroy = function() {
		this.container.remove();
	}
	this.getContainer = function() {
		return this.container;
	}

	this.addBullet = function(text) {
		this.ul.append('<li><span class="ui-icon ui-icon-circle-check"></span><span class="bullet-item">' + text + '</span></li>');
	}	
	
	this.getPrefferedHeight = function() {
		return 265;
	}
}

var WaitDialogView = function() {
	this.container = $(document.createElement('div'))
	
	this.create = function(id) {
		this.id = id;
		this.container.attr('id', id);
		this.container.attr('title', 'Please Wait...');
		this.container.addClass('dialogView');
		this.container.addClass('loadingDialogView');
		this.container.html('<img style="padding:10px 0 0 60px;" src="images/ajax-loader-trans.gif" class="loader"/>');
		this.ul = this.container.find('ul'); 
	}
	this.destroy = function() {
		this.container.remove();
	}
	this.getContainer = function() {
		return this.container;
	}
	
	this.getPrefferedHeight = function() {
		return 100;
	}
	this.getPrefferedWidth = function() {
		return 180;
	}
}
