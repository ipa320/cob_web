items = {}
selectedItem = null

// template data
templateData = {}
currentTemplate = ""


// set by init
syncID = 0
name = ""
privilege = 0
basicHostData = {}
basicCompData = {}
updateHostData = {}
updateCompData = {}

// set to true while making an ajax request
idle = false



$(document).ready(function() {
	selectedItem = wrapItem($("li.active"))
	closeMenus()
	openMenu(selectedItem)

	$("a.title").click(function(c) {
		name = $(this).text()
		if (items[name] == undefined)
			addWarning("This item '" + name + "' could not be found in the navigation.")		
		else
			selectItem(items[name])

		return false
	})

	$("a.grpTitle").click(function(c) {
		name = $(this).text()
/*		if (items[name] == undefined)
			addWarning("This item '" + name + "' could not be found in the navigation.")		
		else
			selectItem(items[name])
*/
		return false
	})

//	initDialog()
	clearWarnings('preStart')
	parseMenu()
	loadTemplates()
	initLoading()

	// tmp
	$("a.grpTitle").attr("href", "javascript:void()")
})
function timestamp()
{
	return new Date().getTime();
}
function wrapItem(jq)
{
	name = jq.children("a.title").text()//.replace(/\s/g, "")
	isGroup = false
	if (name == "") {
		isGroup = true
		name = jq.children("a.grpTitle").text()
	}

	// If the name could not still not be retrieved
	if (name == "")
		return null;	

	return {name: name, isGroup: isGroup, jq: jq}
}


function ajaxRequest(url, fkt, dataType, error)
{
	if (dataType == undefined)
		dataType = "text"

	if (error == undefined)
		error = function() { defaultErrorHandler(url) }

	$.ajax({url: url, success: fkt, error: error, dataType: dataType})
}
function defaultErrorHandler(url)
{
	addError("An unexpected error occured requesting the url: \n\t'" + url + "'.")
}


function loadTemplates()
{
	ajaxRequest(uriRoot + "/control/template/status", function(data) {
		setTemplateData('status', data)
		tryShowStatus()
	}, "text")
	ajaxRequest(uriRoot + "/control/template/log", function(data) { setTemplateData('log', data) }, "text")
}
function setTemplateData(templateName, data)
{
	data = data.replace(/<!DOCTYPE[^>]+>/, "")
	templateData[templateName] = data
}
function applyTemplate(templateName, dataObject, force)
{
	if (templateData[templateName] == undefined)
		addError("Template '" + templateName + "' could not be found")

	else {
		if (currentTemplate != templateName || force == true)
			$("div.tabcontents").html(templateData[templateName])

		if (dataObject != undefined) {
			for (key in dataObject)
				$(".value_" + key).text(dataObject[key])
		}

		currentTemplate = templateName
	}
}

function addWarning(warn, title, time)
{
	box = $("#mainWarnings")
	if (box.size() == 0)
		window.alert("Could not find children '#mainWarnings'. The following warning occured:\n\n'" + warn + "'")

	if (title == undefined)
		title = 'auto'

	ul = box.find("ul")
	ul.append('<li class="' + title + '">' + warn + "</li>")
	//box.fadeIn()
	box.show()

	if (time != undefined && parseInt(time) > 0)
		setTimeout("clearWarnings('" + title + "')", parseInt(time))
}

function clearWarnings(title)
{
	if (title == undefined)
		title = 'auto'

	box = $("#mainWarnings")
	ul = box.find("ul");
	lis = ul.children("." + title)

	if (lis.size() == ul.children().size() && lis.size() > 0) {
		//box.fadeOut(400, function() { $(this).find("ul").children().remove() })
		lis.remove()
		box.hide()
	}
	else
		//lis.fadeOut(400, function() { $(this).remove() } );
		lis.remove()

	if (ul.children().size() == 0)
		box.hide()
}


function addError(err, title, time)
{
	box = $("#mainErrors")
	if (box.size() == 0)
		window.alert("Could not find children '#mainErrors'. The following warning occured:\n\n'" + err + "'")

	if (title == undefined)
		title = 'auto'

	ul = box.find("ul")
	ul.append('<li class="' + title + '">' + err + "</li>")
	box.show()

	if (time != undefined && parseInt(time) > 0)
		setTimeout("clearErrors('" + title + "')", parseInt(time))
}

function clearErrors(title)
{
	if (title == undefined)
		title = 'auto'

	box = $("#mainErrors")
	ul = box.find("ul");
	ul.children("." + title).remove();

	if (ul.children().size() == 0)
		box.hide()
}

function initDialog()
{
	$('div.tabcontents').dialog({
		autoOpen: false,
		width: 600,
		buttons: {
			"Ok": function() { 
				$(this).dialog("close"); 
			}, 
			"Cancel": function() { 
				$(this).dialog("close"); 
			} 
		}
	});
}

function parseMenu()
{
	lis = $("div.navtabs li")
	lis.each(function(i, item) {
		wI = wrapItem($(item))		

		if (wI != null)
			items[wI.name] = wI
	})
}

function initLoading()
{
	ajaxRequest(uriRoot + "/.bs/basicData", initDataReceived, "json", initDataFailed);
}

function initDataReceived(data)
{
	if (data && data != null) {
		syncID = data.syncID
		privilege = data.privilege
		name = data.name
		basicHostData = data.data[0];
		basicCompData = data.data[1];
		loadUpdates()
	}
	else
		initDataFailed()
}
function initDataFailed()
{
	addError('Could not establish an ajax connection. Maybe the server is down or the proxy is not set. Disabling ajax.')
}

function loadUpdates()
{
	ajaxRequest(uriRoot + "/.bs/updateData/" + timestamp(), updateDataReceived, "json", updateDataFailed)
}
function updateDataReceived(data)
{
	if (idle) {
		setTimeout("loadUpdates()", 2000)
		return
	}

	if (!data) {
		updateDataFailed()
		setTimeout("loadUpdates()", 2000)
		return
	}

	clearErrors()
	clearWarnings()
		

	updateHostData = data.data[0]
	for (key in updateHostData) {
		host = updateHostData[key]
		hostData = basicHostData[key]
		if (host.on == "False")
			addWarning ("Host #" + key + " (" + hostData.ip + " : " + hostData.port + ") is down")
	}

	updateCompData = data.data[1]
	for (key in updateCompData) {
		if (items[key] == undefined) {
			addWarning("Update brought up an unknown component: " + key + ". Configuration might have changed. Try reloading (F5)")
			break;
		}

		if (!items[key].isGroup)
			setItemState(items[key], updateCompData[key].pid != '')
	}

	

	if (currentTemplate == "status")
		showStatus()

	if (currentTemplate == "")
		tryShowStatus() // Maybe not every remote data is loaded yet

	setTimeout("loadUpdates()", 2000)
}
function updateDataFailed(data)
{
	if (idle) {
		setTimeout("loadUpdates()", 2000)
		return;
	}
		
	clearErrors()
	clearWarnings()
	addError("An error occured trying to fetch updates. Disabling ajax for the moment.")
	setTimeout("loadUpdates()", 2000)
}
	

function selectItem(item)
{
	if (item.name == selectedItem.name) {
		showStatus()
		return
	}

	// unidle
	idle = false

	selectedItem.jq.addClass("inactive")
	selectedItem.jq.removeClass("active")
	item.jq.removeClass("inactive")
	item.jq.addClass("active")

	selectedItem = item

	closeMenus()
	openMenu(item)
	showStatus()
}

function closeMenus()
{
	$("li.attribute").remove()
}

function openMenu(item)
{
	ul = item.jq.children("ul")
	indent = item.jq.children("a").css("padding-left")

	menu = $(document.createElement("li"))
	menu.addClass("attribute")
	menu.css("padding-left", indent)
	menu.html('» <a href="javascript:showStatus()"> Status </a> | <a href="javascript:showLog()"> Logs </a>')

	if (ul.children().size() > 0)
		menu.insertBefore(ul.first())
	else
		ul.append(menu)
}

function setItemState(item, running)
{
	//img = item.img
	if (running)
		item.jq.css("backgroundImage", "url('" + chromePath + "/cl/images/gruen.png')")

	else
		item.jq.css("backgroundImage", "url('" + chromePath + "/cl/images/grau.png')")
}

function createDesireButton(name, href)
{
	span = $(document.createElement('span'))
	span.addClass("desire_button")
	span.html('<a href="' + href + '">' + name + '</a>')
	return span
}

function tryShowStatus()
{
	if (updateCompData[selectedItem.name] != undefined && basicCompData[selectedItem.name] != undefined && templateData['status'] != undefined)
		showStatus()
}

function showStatus()
{
	comp = basicCompData[selectedItem.name]
	if (comp == undefined) {
		addError("Could not find the component '" + selectedItem.name + "'.", 'permanent')
		return;
	}

	updateComp = updateCompData[selectedItem.name];
	if (updateComp == undefined) {
		addError("Could not find the update component '" + selectedItem.name + "'.", 'permanent')
		return;
	}

	host_id = comp['host_id']
	updateHost = updateHostData[host_id]
	if (updateHost == undefined) {
		addError("Could not find update-data for component '" + selectedItem.name + "'.", 'permanent')
		return
	}

	host_id = comp['host_id']
	host = basicHostData[host_id]
	if (host == undefined)
		addError("Could not find the host that belongs to the component '" + selectedItem.name + "'", 'permanent')

//	console.log("show status: pid: '" + updateComp.pid + "', vnc: '" + updateComp.vnc + "'")

	row = comp
	row['host_ip'] = host.ip
	row['host_port'] = host.port

	$(".status_buttons").html("").removeClass("buttonHostUnavailable")

	applyTemplate('status', row)

	// If no display is defined, we dont need vnc
	if (comp.display == '')
		$(".status_vnc").hide()	

	// Vnc Status
	else {
		$(".status_vnc").show()
		if (updateComp.vnc != "") {
			url = 'http://' + host.ip + ':' + (8080+parseInt(comp.display))
			$(".status_vnc #display").html('<a href="' + url + '" target="_blank">' + url + '</a>')
		}
		else
			$(".status_vnc #display").html('inactive')
	}

	statusButtons = $(".status_buttons")

	// if the app is idle at the moment
	if (idle) {
		statusButtons.append('<img src="' + chromePath + '/cl/images/ajax-loader-trans.gif" class="loading" />')
	}

	// Corresponding Host is online ?
	else if (updateHost.on != "True") {
		statusButtons.addClass("buttonHostUnavailable")
		statusButtons.text("Host is unavailable")
	}

	// Sufficient privileges ?
	else if (privilege < comp.privilege) {
		statusButtons.addClass("insufficientRights")
		statusButtons.text("Insufficient Rights")
	}

	// Show the buttons
	else {

		// COMP up
		if (updateComp.pid != '')  {
			$(".value_status").text("active (" + updateComp.pid + ")")

			statusButtons.append(createDesireButton("stop", "javascript:stopComponent()"))



		}
		// COMP down
		else {
			// VNC na
			if (comp.display == "")
				statusButtons.append(createDesireButton("start", "javascript:startComponent()"))

			// VNC up
			if (comp.display != "" && updateComp.vnc != "") {
				statusButtons.append(createDesireButton("start", "javascript:startComponent()"))
				statusButtons.append("&nbsp;")
				statusButtons.append(createDesireButton("stop vnc", "javascript:stopVNC()"))		
			}
		
			// VNC down
			if (comp.display != "" && updateComp.vnc == "")
				statusButtons.append(createDesireButton("start vnc", "javascript:startVNC()"))
		}

		// has Childs
		if (comp.children.length != 0) {
			statusButtons.append("&nbsp;")
			statusButtons.append(createDesireButton("start group", "javascript:startGroup()"))
			statusButtons.append("&nbsp;")
			statusButtons.append(createDesireButton("stop group", "javascript:stopGroup()"))
		}
	}
		
}
function showLog()
{
	applyTemplate('log')
	ajaxRequest(uriRoot + "/.bs/log/" + selectedItem.name, outputLog, "text")	
}
function outputLog(text)
{
	if (currentTemplate != "log" )
		return

	pos = text.indexOf('\n')
	title = text.substring(0, pos)
	tailOut = text.substr(pos+1, text.length-pos)

	applyTemplate('log', {title: selectedItem.name, log:title, tail_out: tailOut})

	// work around to keep html entities, especially <b> wich is turned into &lt;b&rt; in the log view
	logDiv = $("pre.value_tail_out")
	text = logDiv.html().replace(/&lt;b&gt;/g,"<b>").replace(/&lt;\/b&gt;/g,"</b>")
	logDiv.html(text)
}

/*
 * START VNC
 */
function startVNC()
{
	clearWarnings('vncWarning')
	if (currentTemplate != "status")
		return


	ajaxRequest(uriRoot + "/.bs/startVNC/" + selectedItem.name, vncStartResult, "json", vncStartFailed)

	idle = true
	showStatus()	
}
function vncStartResult(data)
{
	idle = false
	clearWarnings('vncWarning')


	if (!data || data.data.error != "False") {
		msg = "&lt;EmptyMessage&gt;"
		code = "N/A"
		if (data && data.data.errorMsg != undefined && data.data.errorMsg != "")
			msg = data.data.errorMsg
		if (data && data.data.code != undefined && data.data.code != "")
			code = data.data.code

		addWarning("Starting VNC for component '" + selectedItem.name + "' failed. Server returned Error Message: '" + msg + "' (Code #" + code + ")" , "vncWarning", 5000)
	}

	else {
//		console.log("vnc Start Result, no errors: " + data.data.error + ", " + data.data.errorMsg)

		// manually update "updateCompData" until we receive the next update
		updateCompData[selectedItem.name].vnc = "1"
	}

	showStatus()
}
function vncStartFailed(data)
{
	idle = false

	clearWarnings('vncWarning')
	addWarning("Could not connect to the server. Starting VNC for component '" + selectedItem.name + "' failed.", "vncWarning", 5000)

	showStatus()
}

/*
 * STOP VNC
 */
function stopVNC()
{
	clearWarnings('vncWarning')
	if (currentTemplate != "status")
		return

	ajaxRequest(uriRoot + "/.bs/stopVNC/" + selectedItem.name, vncStopResult, "json", vncStopFailed)

	idle = true
	showStatus()
}
function vncStopResult(data)
{
	// unidle
	idle = false

	clearWarnings('vncWarning')
	if (!data || data.data.error != "False") {
		msg = "&lt;EmptyMessage&gt;"
		code = "N/A"
		if (data && data.data.errorMsg != undefined && data.data.errorMsg != "")
			msg = data.data.errorMsg
		if (data && data.data.code != undefined && data.data.code != "")
			code = data.data.code

		addWarning("Stopping VNC for component '" + selectedItem.name + "'failed. Server returned Error Message: '" + msg + "' (Code #" + code + ")" , "vncWarning", 5000)
	}

	else {
//		console.log("vnc Start Result, no errors: " + data.data.error + ", " + data.data.errorMsg)

		// manually update "updateCompData" until we receive the next update
		updateCompData[selectedItem.name].vnc = ""
	}

	showStatus()
}
function vncStopFailed(data)
{
	// unidle
	idle = false

	clearWarnings('vncWarning')
	addWarning("Could not connect to the server. Stopping VNC for component '" + selectedItem.name + "' failed.", "vncWarning", 5000)

	showStatus()
}


/*
 * START COMPONENT
 */
function startComponent()
{
	clearWarnings('compWarning')
	if (currentTemplate != "status")
		return

	// ignore the next incoming update
	idle = true
	ajaxRequest(uriRoot + "/.bs/start/" + selectedItem.name, startResult, "json", startFailed)

	showStatus()
}
function startResult(data)
{
	clearWarnings('compWarning')
	idle = false

	if (!data || data.data.error != "False") {
		msg = "&lt;EmptyMessage&gt;"
		code = "N/A"
		if (data && data.data.errorMsg != undefined && data.data.errorMsg != "")
			msg = data.data.errorMsg
		if (data && data.data.code != undefined && data.data.code != "")
			code = data.data.code

		addWarning("Starting Component '" + selectedItem.name + "' failed. Server returned Error Message: '" + msg + "' (Code #" + code + ")" , "compWarning", 5000)
	}

	else {
//		console.log("vnc Start Result, no errors: " + data.data.error + ", " + data.data.errorMsg)

		setItemState(selectedItem, true)
		updateCompData[selectedItem.name].pid = data.data.pid
	}

	showStatus()
}
function startFailed(data)
{
	idle = false
	clearWarnings('compWarning')
	addWarning("Could not connect to the server. Starting Component '" + selectedItem.name + "' failed.", "compWarning", 5000)

	showStatus()
}

/*
 * STOP COMPONENT
 */
function stopComponent()
{
	clearWarnings('compWarning')
	if (currentTemplate != "status")
		return

	// make it idle
	idle = true
	ajaxRequest(uriRoot + "/.bs/stop/" + selectedItem.name, stopResult, "json", stopFailed)

	showStatus()
}
function stopResult(data)
{
	// unidle
	clearWarnings('compWarning')
	idle = false

	clearWarnings('compWarning')
	if (!data || data.data.error != "False") {
		msg = "&lt;EmptyMessage&gt;"
		code = "N/A"
		if (data && data.data.errorMsg != undefined && data.data.errorMsg != "")
			msg = data.data.errorMsg
		if (data && data.data.code != undefined && data.data.code != "")
			code = data.data.code

		addWarning("Stopping Component '" + selectedItem.name + "' failed. Server returned Error Message: '" + msg + "' (Code #" + code + ")" , "compWarning", 5000)
	}

	else {
//		console.log("vnc Start Result, no errors: " + data.data.error + ", " + data.data.errorMsg)

		// manually update "updateCompData" until we receive the next update
		updateCompData[selectedItem.name].pid = ""
		setItemState(selectedItem, false)
	}

	showStatus()
}
function stopFailed(data)
{
	idle = false
	clearWarnings('compWarning')
	addWarning("Could not connect to the server. Stopping Component '" + selectedItem.name + "' failed.", "compWarning", 5000)

	showStatus()
}


/*
 * START GROUP
 */
curCompId = -1;
function startGroup()
{
	//
	currentTemplate = "startGroup"

	$("#status").append('<div id="StartStopTree" style="display:none"><h1>Starting Group</h1><table id="StartStopTable"></table></table></div>')
	$("#statustable").fadeOut('fast', function() {	$("#StartStopTree").fadeIn('fast', function() { 

		setTimeout("startGroupVNCServers()", 200)

	}) })
}

function startGroupVNCServers()
{
	curCompId = -1
	children = basicCompData[selectedItem.name].children
	vncComps = []
	
	for (i=0; i<children.length; i++) {
		compBasic = basicCompData[children[i]]

		// if any component in the group is assigned to a vnc server, make sure to start that first
		if (compBasic.display != '') {
			$('#StartStopTable').append("<tr><td colspan='3'><h3>Starting VNC assigned to the components</h3></td></tr>")
			startNextGroupVNCServer()
			return;
		}
	}

	// if no vnc server is assigned, start the components
	startGroupComponents()
}

function startNextGroupVNCServer()
{
	curCompId++
	children = basicCompData[selectedItem.name].children
	vncFound = false

	if (curCompId < children.length) {
		for (i=curCompId; i<children.length; i++) {
			compBasic = basicCompData[children[i]]
			compUpdate = updateCompData[children[i]]

			if (compBasic.display != '') {
				curCompId = i
				vncFound = true

				// in case vnc server is already running
				if (compUpdate.vnc != "") {
					$("#StartStopTable").append(
						"<tr class='row-" + curCompId + "-vnc'>" +
							"<td class='compName' colspan='2'>Starting VNC Server for component '" + children[i] + "'</td>" +
							"<td class='compResult compResultOk'>[ AR ]</td>" +
						"</tr>"
					)

					startNextGroupVNCServer()
					return;
				}
				else {
					$("#StartStopTable").append(
						"<tr class='row-" + curCompId + "-vnc'>" +
							"<td class='compName' colspan='2'>Starting VNC Server for component '" + children[i] + "'</td>" +
						"</tr>"
					)

					ajaxRequest(uriRoot + "/.bs/startVNC/" + children[i], startGroupVncResult, "json", vncStartFailed)
					return;
				}
			}
		}
	}

	// if no more component was found, start the components
	if (!vncFound)
		setTimeout("startGroupComponents()", 500)
}

function startGroupVncResult(data)
{
	if (!data || data.data.error != "False") {
		msg = "&lt;EmptyMessage&gt;"
		code = "N/A"
		if (data && data.data.errorMsg != undefined && data.data.errorMsg != "")
			msg = data.data.errorMsg
		if (data && data.data.code != undefined && data.data.code != "")
			code = data.data.code

		// if the error happend because of insufficent rights (code 1), simply skip that component
		if (code == "1") {
			$("tr.row-" + curCompId + "-vnc").append('<td class="compResult compResultIR">[ IR ]</td>')
			startNextGroupVNCServer()
		}

		// else abort the starting process
		else {
			$("tr.row-" + curCompId + "-vnc").append('<td class="compResult compResultFail">[ Fail ]</td>')
			$("#StartStopTable").append("<tr><td colspan='3'><i>Starting VNC Server failed.</i> Server-Message: <b>" + msg + "</b> (Code <b>#" + code + "</b>)<br /><a href='javascript:showLog()'>Click here to watch the log file</a></td></tr>")
		}
	}

	else {
		// success -> start the component now
		$("tr.row-" + curCompId + "-vnc").append('<td class="compResult compResultOk">[ Ok ]</td>')
		startNextGroupVNCServer()
	}
}


function startGroupComponents()
{
	curCompId = -2
	$('#StartStopTable').append("<tr><td colspan='3'><h3>Starting Components</h3></td></tr>")
	startNextGroupComponent()
}


function startNextGroupComponent()
{
	clearWarnings('vncWarning')
	clearWarnings('compWarning')
	clearErrors("startGroup")

	curCompId++;
	childrenCount = basicCompData[selectedItem.name].children.length
	if (curCompId >= childrenCount) {
		setTimeout("$('#StartStopTable').fadeOut('fast', showStatus)", 300)
		return;
	}

	// make sure we start the parent itself as the first component
	if (curCompId >= 0)
		nextCompName = basicCompData[selectedItem.name].children[curCompId]
	else
		nextCompName = selectedItem.name

	nextCompBasic = basicCompData[nextCompName]
	nextCompUpdate = updateCompData[nextCompName]
	if (nextCompBasic == undefined || nextCompUpdate == undefined) {
		addError("The component '" + selectedItem.name + "' could not be found", "startGroup")
		return;
	}

	if (nextCompUpdate.pid != "") {
		$("#StartStopTable").append(
			"<tr class='row-" + curCompId + "'>" +
				"<td class='compName'>Starting Component '" + nextCompName + "'</td>" +
				"<td class='compNo')>(" + (curCompId+2) + " of " + (childrenCount+1) + ")</td>" +
				"<td class='compResult compResultOk'>[ AR ]</td>" +
			"</tr>"
		)
		startNextGroupComponent();
	}

	else {
		$("#StartStopTable").append(
			"<tr class='row-" + curCompId + "'>" +
				"<td class='compName'>Starting Component '" + nextCompName + "'</td>" +
				"<td class='compNo')>(" + (curCompId+2) + " of " + (childrenCount+1) + ")</td>" +
			"</tr>"
		)

		ajaxRequest(uriRoot + "/.bs/start/" + nextCompName, startGroupCompResult, "json", startFailed)
	}
}
function startGroupCompResult(data)
{
	if (!data || data.data.error != "False") {
		msg = "&lt;EmptyMessage&gt;"
		code = "N/A"
		if (data && data.data.errorMsg != undefined && data.data.errorMsg != "")
			msg = data.data.errorMsg
		if (data && data.data.code != undefined && data.data.code != "")
			code = data.data.code


		// if the error happend because of insufficent rights (code 1), simply skip that component
		if (code == "1") {
			$("tr.row-" + curCompId).append('<td class="compResult compResultIR">[ IR ]</td>')
			startNextGroupComponent()
		}

		// else abort the starting process
		else {
			$("tr.row-" + curCompId).append('<td class="compResult compResultFail">[ Fail ]</td>')
			$("#StartStopTable").append("<tr><td style='padding-left:30px' colspan='3'><i>Starting Component failed.</i> Server-Message: <b>" + msg + "</b> (Code <b>#" + code + "</b>)<br /><a href='javascript:showLog()'>Click here to watch the log file</a></td></tr>")
		}
	}

	else {
		// success -> start next compnent
		$("tr.row-" + curCompId).append('<td class="compResult compResultOk">[ Ok ]</td>')
		startNextGroupComponent()
	}
}


/*
 * STOP GROUP
 */
curCompId = -1;
function stopGroup()
{
	//
	currentTemplate = "stopGroup"

	$("#status").append('<div id="StartStopTree" style="display:none"><h1>Stopping Group</h1><table id="StartStopTable"></table></table></div>')
	$("#statustable").fadeOut('fast', function() {	$("#StartStopTree").fadeIn('fast', function() { 

		setTimeout("stopGroupComponents()", 200)

	}) })
}
function stopGroupComponents()
{
	curCompId = basicCompData[selectedItem.name].children.length
	$('#StartStopTable').append("<tr><td colspan='3'><h3>Stopping Components</h3></td></tr>")
	stopNextGroupComponent()
}


function stopNextGroupComponent()
{
	clearWarnings('vncWarning')
	clearWarnings('compWarning')
	clearErrors("stopGroup")

	curCompId--;
	childrenCount = basicCompData[selectedItem.name].children.length
	if (curCompId <= -2) {
		setTimeout("$('#StartStopTable').fadeOut('fast', showStatus)", 300)
		return;
	}

	// make sure we stop the parent at the end
	if (curCompId >= 0)
		nextCompName = basicCompData[selectedItem.name].children[curCompId]
	else
		nextCompName = selectedItem.name

	nextCompBasic = basicCompData[nextCompName]
	nextCompUpdate = updateCompData[nextCompName]
	if (nextCompBasic == undefined || nextCompUpdate == undefined) {
		addError("The component '" + selectedItem.name + "' could not be found.", "stopGroup")
		return;
	}

	if (nextCompUpdate.pid == "") {
		$("#StartStopTable").append(
			"<tr class='row-" + curCompId + "'>" +
				"<td class='compName'>Stopping Component '" + nextCompName + "'</td>" +
				"<td class='compNo')>(" + (childrenCount-curCompId) + " of " + (childrenCount+1) + ")</td>" +
				"<td class='compResult compResultOk'>[ NR ]</td>" +
			"</tr>"
		)
		stopNextGroupComponent();
	}

	else {
		$("#StartStopTable").append(
			"<tr class='row-" + curCompId + "'>" +
				"<td class='compName'>Stopping Component '" + nextCompName + "'</td>" +
				"<td class='compNo')>(" + (childrenCount-curCompId) + " of " + (childrenCount+1) + ")</td>" +
			"</tr>"
		)

		ajaxRequest(uriRoot + "/.bs/stop/" + nextCompName, stopGroupCompResult, "json", stopFailed)
	}
}



function stopGroupCompResult(data)
{
	if (!data || data.data.error != "False") {
		msg = "&lt;EmptyMessage&gt;"
		code = "N/A"
		if (data && data.data.errorMsg != undefined && data.data.errorMsg != "")
			msg = data.data.errorMsg
		if (data && data.data.code != undefined && data.data.code != "")
			code = data.data.code


		// if the error happend because of insufficent rights (code 1), simply skip that component
		if (code == "1") {
			$("tr.row-" + curCompId).append('<td class="compResult compResultIR">[ IR ]</td>')
			startNextGroupComponent()
		}

		// else abort the starting process
		else {
			$("tr.row-" + curCompId).append('<td class="compResult compResultFail">[ Fail ]</td>')
			$("#StartStopTable").append("<tr><td style='padding-left:30px' colspan='3'><i>Stopping Component failed.</i> Server-Message: <b>" + msg + "</b> (Code <b>#" + code + "</b>)<br /><a href='javascript:showLog()'>Click here to watch the log file</a></td></tr>")
		}
	}

	else {
		// success -> start next compnent
		$("tr.row-" + curCompId).append('<td class="compResult compResultOk">[ Ok ]</td>')
		stopNextGroupComponent()
	}
}
