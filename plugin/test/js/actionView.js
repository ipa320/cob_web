var actionViewCode = '<h3 class="actionView-name"><a href="#" class="ph_action-name">PH_name <span class="active">Active</span></a></h3>\
				<div>\
					<div class="buttons">\
						<div class="start-buttons"> \
							<a href="#" class="start-button">Run</a>\
						</div>\
						<div class="stop-buttons">\
							<a href="#" class="stop-button">Stop</a>\
							<a href="#" class="kill-button">Kill</a>\
						</div>\
						<div class="log-buttons">\
							<a href="#" class="showLog-button">ShowLog</a>\
							<a href="#" class="refreshLog-button">Refresh</a>\
						</div>\
					</div>\
					<div class="text"><table>\
						<tr class="even"><th>name:</td><td class="ph_action-name">PH_name</td></tr>\
						<tr class="even"><th>Description:</td><td class="ph_action-desc"><i>Keine Beschreibung angegeben</i></div>\</td></tr>\
						<tr class="even"><th>Dependencies:</th><td class="ph_action-dep"><a href="#" class="running">Meine Komponente » Aktive Komponente</a><br /><a href="#" class="notRunning">Meine Komponente » Inaktive Komponente</a></td></tr> \
						</table>\
					</div>\
				</div>';


$.fn.renderActionView = function(action, options) {
	if (! (action instanceof Action))
		throw new Error("Argument must be an instance of Action");


	// it's a new object
	if (!this.hasClass('actionView')) {
		this.addClass('actionView');
		// insert the static id so we can create unique ids
		data = actionViewCode.replace(/\{id\}/g, action.id);
		this.append(data);

		// Accordion
		active = styleDataManager.isActionTabClosed(action.id) ? false : null;
		this.accordion({ header: "h3", collapsible: true, active: active });
		this.bind('accordionchange', function(event, ui) {
			styleDataManager.toggleActionTab(action.id);
		});

		// Create buttonsets
		this.find(".start-buttons").buttonset();
		this.find(".stop-buttons").buttonset();
		this.find(".log-buttons").buttonset();

		// Create buttons
		this.find(".start-button").button({ icons: {primary: "ui-icon-play"} });
		this.find(".stop-button").button({ icons: {primary: "ui-icon-stop" } });
		this.find(".kill-button").button({ icons: {primary: "ui-icon-notice"} });
		this.find(".showLog-button").button({ icons: {primary: "ui-icon-document-b" } });
		this.find(".refreshLog-button").button({ icons: {primary: "ui-icon-refresh" } });
			
		// Set name and description. These values don't change
		this.find(".ph_action-name").text(action.name);

		if (action.description)
			this.find(".ph_action-desc").html(action.description);
			
		this.find('.start-button').click(function() { application.startAction(action.id, action.compId); return false; });
		this.find('.stop-button').click(function() { application.stopAction(action.id, action.compId); return false; });
		this.find('.kill-button').click(function() { application.killAction(action.id, action.compId); return false; });
	}

	this.updateActionView(action, options, true);
}

$.fn.updateActionView = function(action, options, force) {
	if (! (action instanceof Action))
		throw new Error("Argument must be an instance of Action");	
	
	// check whether it's necessary to update the object
	if (force === true || !this.data("lastRefresh") || this.data("lastRefresh") < action.getLastChange()) {
		startButtons = this.find(".start-buttons");
		stopButtons  = this.find(".stop-buttons");
		
		if (action.isActive()) {
			// need to show start / hide stop buttons ?
			if (startButtons.is(':visible')) {
				startButtons.hide();
				stopButtons.show();
				stopButtons.find('.stop-button', '.kill-button').removeClass('ui-state-hover');
			}
		}
		else {
			if (stopButtons.is(':visible')) {
				startButtons.show();
				startButtons.find('.start-button').removeClass('ui-state-hover');
				stopButtons.hide()
			}
		}
		this.data("lastRefresh", new Date().getTime());
		
	
		// have to disable the buttons seperatrely, won't work otherwise
		this.find(".start-buttons").buttonset({'disabled': screenManager.isLockedLocation()});
		this.find(".stop-buttons").buttonset({'disabled': screenManager.isLockedLocation()});
		this.find(".log-buttons").buttonset({'disabled': screenManager.isLockedLocation()});
	}
};
