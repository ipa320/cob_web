//control_files/log2.png
///trac/demo/chrome/cl/images/log2.png


$(document).ready(function() {
	// work around to keep html entities, especially <b> wich is turned into &lt;b&rt; in the log view
	logDiv = $("pre.value_tail_out")
	if (logDiv.size() > 0) {
		text = logDiv.html().replace(/&lt;b&gt;/g,"<b>").replace(/&lt;\/b&gt;/g,"</b>")
		logDiv.html(text)
	}
})

curCompId = -1;
function startTree()
{
	$("#status").append('<div id="StartStopTree" style="display:none"><h1>Starting Tree</h1><table id="StartStopTable"></table></table></div>')

	$("#statustable").fadeOut('fast', function() {	$("#StartStopTree").fadeIn('fast') })

	curCompId = -1;
	startNextComponent();
}

function startNextComponent()
{
	curCompId++;
	if (curCompId >= startTreeOrder.length) {
		window.location.reload();
		return;
	}

	$("#StartStopTable").append(
		"<tr class='row-" + curCompId + "'>" +
			"<td class='compName'>Starting Component '" + startTreeOrder[curCompId] + "'</td>" +
			"<td class='compNo')>(" + (curCompId+1) + " of " + startTreeOrder.length + ")</td>" +
//			"<td class='compResult'></td>" +
		"</tr>"
	)
	$.ajax({url: uriRoot + "control/ajax/start?comp=" + startTreeOrder[curCompId], 
		dataType: "text", success: startCompResult, error: startCompError });
}

function startCompResult(data)
{
	result = parseInt(data)
	if (result == -6) {
		$("tr.row-" + curCompId).append('<td class="compResult compResultFail">[ IR ]</td>')
		startNextComponent();
	}
	else if (result == -2 || result == -1) {
		$("tr.row-" + curCompId).append('<td class="compResult compResultFail">[ Fail ]</td>')
		$("#StartStopTable").append('<tr><td colspan="3">Could not start the component. <a href="' + uriRoot + startTreeOrder[curCompId] + '?operation=refresh&attr=log">Click here to watch the log file</a></td></tr>');
	}

	
	else if (result == 1 || result == 2) {
		$("tr.row-" + curCompId).append('<td class="compResult compResultOk">[ ' + (result == 1 ? 'AR' : 'Ok') + ' ]</td>')
		startNextComponent();
	}

	else	
		window.alert("Unexpected result code: " + data)
}
function startCompError(data, txt, thrown)
{
	window.alert("An unexpected error occured:\n" + data.toString() + "\n\n" + txt + "\n\n" + thrown)
}


function stopTree()
{
	$("#status").append('<div id="StartStopTree" style="display:none"><h1>Stopping Tree</h1><table id="StartStopTable"></table></table></div>')

	$("#statustable").fadeOut('fast', function() {	$("#StartStopTree").fadeIn('fast') })

	curCompId = startTreeOrder.length;
	stopNextComponent();
}

function stopNextComponent()
{
	curCompId--;
	if (curCompId < 0) {
		window.location.reload();
		return;
	}

	$("#StartStopTable").append(
		"<tr class='row-" + curCompId + "'>" +
			"<td class='compName'>Stopping Component '" + startTreeOrder[curCompId] + "'</td>" +
			"<td class='compNo')>(" + (startTreeOrder.length-curCompId) + " of " + startTreeOrder.length + ")</td>" +
//			"<td class='compResult'></td>" +
		"</tr>"
	)
	$.ajax({url: uriRoot + "ajax/stop?comp=" + startTreeOrder[curCompId], 
		dataType: "text", success: stopCompResult, error: stopCompError });
}
function stopCompResult(data)
{
	result = parseInt(data)

	if (result == -6) {
		$("tr.row-" + curCompId).append('<td class="compResult compResultFail">[ IR ]</td>')
		stopNextComponent();
	}
	else if (result == -3 || result == -1) {
		$("tr.row-" + curCompId).append('<td class="compResult compResultFail">[ Fail ]</td>')
		$("#StartStopTable").append('<tr><td colspan="3">Could not stop the component. <a href="' + uriRoot + startTreeOrder[curCompId] + '?operation=refresh&attr=log">Click here to watch the log file</a></td></tr>');
	}

	
	else if (result == 0 || result == 3) {
		$("tr.row-" + curCompId).append('<td class="compResult compResultOk">[ ' + (result == 0 ? 'NR' : 'Ok') + ' ]</td>')
		stopNextComponent();
	}

	else	
		window.alert("Unexpected result code: " + data)
}
function stopCompError(data, txt, thrown)
{
	window.alert("An unexpected error occured:\n" + data.toString() + "\n\n" + txt + "\n\n" + thrown)
}
