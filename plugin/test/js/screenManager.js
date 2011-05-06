var screenManager = new (function() {
	this.lock = function() {
		$("#dialog-loading").dialog({
			height: 140,
			modal: true
		});

	}
})();
