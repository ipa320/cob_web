var Host = function Host(id, hostname, username, port, online) {
	this.id = id;
	this.hostname = hostname;
	this.username = username;
	this.port = port;
}
Host.loadHostData = function(urlPrefix, successCallback, errorCallback)
{
	if (typeof(errorCallback) !== "function")
		errorCallback = function(data) { alert('Host Data could not be loaded [' + data.status + ']:\n\n' + data.responseText); };
	
	var onSuccess = function(hostData) {
		try {
			Host._hosts = {}
			
			for (id in hostData) {
				host = hostData[id];
				if (!id || !host.hostname || !host.user || !host.port)
					throw new Error('Invalid Host-Object received');
				Host._hosts[id] = new Host(id, host.hostname, host.user, host.port);
			}
			
			if (typeof(successCallback) == 'function')
				successCallback(hostData);
		}
		catch (err) {
			alert('Error occured while parsing host data:\n' + err);
		}
	};
	
	var onError = function(data) {
		errorCallback(data);
	};
	
	$.ajax({
		url: urlPrefix + '/data/host',
		success: onSuccess,
		error:   onError
	});
}

Host.getIdNameArray = function()
{
	var array = {};
	for (hostId in Host._hosts) {
		var host = Host._hosts[hostId];
		array[hostId] = host.username + "@" + host.hostname + ":" + host.port;
	}
	return array;
}
Host.createSelectHtmlCode = function(selectedId) 
{
	html = '<select size="1"><option label= " - "> - </option>';
	
	var hostData = Host.getIdNameArray();
	for (hostId in hostData) {
		var selected = '';
		if (hostId == selectedId)
			selected = 'selected="selected"';
			
		html += '<option hostId="' + hostId + '" label="' + hostData[hostId] + '" ' + selected + '>' + hostData[hostId] + '</option>';
	}
	html += '</select>';
	
	return html;
}
