$.fn.renderInfoBox = function(username, status, args) {
	this.html('<table><tr><th>User:</th><td>' + username + '</tr><th>Status:</th><td>' + status + '</td></tr><tr><th colspan="2"><a href="#" onclick="javascript:application.showServerReservation()">Server Reservation</a></th></tr></table>')
}
