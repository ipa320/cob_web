var screenManager = new (function() {
	this._lockDialog = null;
	this._lockLocation = false;
	
	
	this.unlock = function() {
		this.unlockDisplay();
		this.unlockLocation();
	}

	this.isLockedDisplay = function() {
		return this._lockDialog != null;
	}
	this.lockDisplay = function(dialogView) {
		if (this._lockDialog === null) {
			this._lockDialog = dialogView;

			this._lockDialog.create('dialog-box');
			$('body').prepend(this._lockDialog.getContainer());
			$(this._lockDialog.getContainer()).dialog({
				beforeClose: function() { return false; },
				height: 230,
				modal: true
			});
		}

	}
	this.unlockDisplay = function() {
		if (this._lockDialog !== null) {
			this._lockDialog.getContainer().remove();
			this._lockDialog = null;
		}
	}
	

	this.isLockedLocation = function() {
		return this._lockLocation;
	}
	this.lockLocation = function() {
		this._lockLocation = true;
	}
	this.unlockLocation = function() {
		this._lockLocation = false;
	}
})();
