var actionViewCode = '<h3 class="actionView-title"><a href="#" class="ph_action-title">PH_TITLE({id}) <span class="active">Active</span></a></h3>\
				<div>\
					<div class="buttons">\
						<div class="start-buttons">\
							<input type="checkbox" class="start-button" id="start-button-{id}" /><label for="start-button-{id}">Run</label>\
						</div>\
						<div class="stop-buttons">\
							<input type="radio" class="stop-button" id="stop-button-{id}" name="stop-button-{id}" /><label for="stop-button-{id}">Stop</label>\
							<input type="radio" class="kill-button" id="kill-button-{id}" name="stop-button-{id}" /><label for="kill-button-{id}">Kill</label>\
						</div>\
						<div class="log-buttons">\
							<input type="checkbox" class="showLog-button" id="showLog-button-{id}" /><label for="showLog-button-{id}">Show Log</label>\
							<input type="checkbox" class="refreshLog-button" id="refreshLog-button-{id}" /><label for="refreshLog-button-{id}">&nbsp;</label>\
						</div>\
					</div>\
					<div class="text"><table>\
						<tr class="even"><th>Title:</td><td class="ph_action-title">PH_TITLE</td></tr>\
						<tr class="even"><th>Description:</td><td class="ph_action-desc">Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.</div>\</td></tr>\
						<tr class="even"><th>Dependencies:</th><td class="ph_action-dep"><a href="#" class="running">Meine Komponente » Aktive Komponente</a><br /><a href="#" class="notRunning">Meine Komponente » Inaktive Komponente</a></td></tr> \
						</table>\
					</div>\
				</div>';


$.fn.actionView = function(action, options) {
	if (! action instanceof Action)
		return;

	// it's a new object
	if (!this.hasClass('actionView')) {
		this.addClass('actionView');
		// insert the static id so we can create unique ids
		data = actionViewCode.replace(/\{id\}/g, action.id);
		this.append(data);

		// Accordion
		this.accordion({ header: "h3", collapsible: true });
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
	}

	this.updateActionView(action, options);
}

$.fn.updateActionView = function(action, options, force) {
	// check whether it's necessary to update the object
	if (force === true || !this.data("lastRefresh") || this.data("lastRefresh") < action.lastChange) {

		this.find(".ph_action-title").text(action.title);
		this.data("lastRefresh", new Date().getTime());
	}
};




