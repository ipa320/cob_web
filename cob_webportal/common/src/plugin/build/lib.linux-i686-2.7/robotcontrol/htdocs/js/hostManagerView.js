(function($) {
	var htmlCode = '<div class="hostSelect"></div><table class="options">\
	    <tr><td><label for="hostname">Hostname</label></td><td><input id="hostname" type="text" class="hostname" /></td></tr>\
	    <tr><td><label for="username">Username</label></td><td><input id="username" type="text" class="username" /></td></tr>\
	    <tr><td><label for="password">Password</label></td><td><input id="password" type="password" class="password" /></td></tr>\
	    <tr><td><label for="port">Port</label></td><td><input id="port" type="text" class="port" /></td></tr>\
	</table>\
	<a href="#" id="submitHost">Submit Host</a>';

	$.fn.renderHostManagerView  = function() {
	    this.addClass('hostManagerView');
	    this.html(htmlCode);

	    var hostId = null;
	    
	    var hostname = this.find('#hostname');
	    var username = this.find('#username');
	    var password = this.find('#password');
	    var port = this.find('#port');
	    var submit = this.find('#submitHost');

	    var onChange = function(id) {
		hostId = id;
		submit.show();
	
	  	if (hostId > 0) {
		    var host = Host.getHostById(hostId);
		    hostname.val(host.hostname);
		    username.val(host.username);
		    port.val(host.port);

		    if (application.hostHasRunningComponent(host)) {
			hostname.attr('disabled', 'disabled');
			username.attr('disabled', 'disabled');
			password.attr('disabled', 'disabled');
			port.attr('disabled', 'disabled');
			submit.hide();
			alert('One or more components are running on that host.\nMake sure to stop them first.');
		    } else {
			hostname.removeAttr('disabled');
			username.removeAttr('disabled');
			password.removeAttr('disabled');
			port.removeAttr('disabled');
		    }
		}
		else {
		    hostname.val('').removeAttr('disabled');
		    username.val('').removeAttr('disabled');
		    password.val('').removeAttr('disabled');
		    port.val('22').removeAttr('disabled');
		}
	    }

	    var code = $(Host.createSelectHtmlCode(null, {'hostId': -1, 'label': 'New Host'}));
	    code.change(function() {
		var id = $(this).find("option:selected").attr("hostId");
		onChange(id);
	    });
	    this.find(".hostSelect").html(code);

	    // call the onChange on the default id
	    onChange(-1);
	    
	    // validate the input
	    var validateInput = function() {
		hostname.removeClass('error');
		username.removeClass('error');
		port.removeClass('error');

		var valid = true;
		if (hostname.val().length == 0 && hostname.val().indexOf('/')==-1) {
		    valid = false;
		    hostname.addClass('error');
		}
		if (username.val().length == 0 && username.val().indexOf('/')==-1) {
		    valid = false;
		    username.addClass('error');
		}
		if (password.val().length == 0 && password.val().indexOf('/')==-1) {
		    valid = false;
		    password.addClass('error');
		}
		if (!port.val().match(/^[0-9]+$/)) {
		    valid = false;
		    port.addClass('error');
		}
		return valid;
	    };
	
	    this.find('#submitHost').click(function() {
		if (validateInput()) {
		    application.submitHost(hostId, hostname.val(), username.val(), password.val(), port.val());
		}
	    });
	}
})(jQuery);
