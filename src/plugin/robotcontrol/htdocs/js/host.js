var Host = function Host(id, hostname, username, port, online) {
    this.id = id;
    this.hostname = hostname;
    this.username = username;
    this.port = port;

    this.clone = function() {
	return new Host(this.id, this.hostname, this.username, this.port);
    }
}
Host.updateHost = function(data)
{
    var id = data['id'];
    var hostname = data['hostname'];
    var username = data['user'];
    var port = data['port'];
    if (!id || !parseInt(id) || !hostname || !username || !port)
	throw new Error('Invalid Host-Object received');

    id = parseInt(id);
    if (Host._hosts[id]) {
	var host = Host._hosts[id];
	host.hostname = hostname;
	host.username = username;
	host.port = port;
    } else {
	Host._hosts[id] = new Host(id, hostname, username, port);
    }
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
		if (!id || !parseInt(id) || !host.hostname || !host.user || !host.port)
		    throw new Error('Invalid Host-Object received');
	
		Host._hosts[parseInt(id)] = new Host(id, host.hostname, host.user, host.port);
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

Host.getHostById = function(id)
{
    if (Host._hosts[id])
	return Host._hosts[id];
    return null;
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

Host.createSelectHtmlCode = function(selectedId, firstItem)
{
    html = '<select size="1">';
    if (firstItem !== null) {
	if (typeof(firstItem) == 'object' && firstItem['label'] && firstItem['hostId'])
	    html += '<option hostId="' + firstItem['hostId'] + '" label="' + firstItem['label'] + '">' + firstItem['label'] + '</option>';
	else
	    html += '<option label= " - "> - </option>';
    }
	
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
