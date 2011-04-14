function getDateStr(date)
{
	dayNames   = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
	monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

	suffix = 'th'
	if (date.getDate() == 1)
		suffix = 'st'
	if (date.getDate() == 2)
		suffix = 'nd'

	return dayNames[date.getDay()] + ", " + date.getDate() + suffix + " of " + monthNames[date.getMonth()] + " " + date.getFullYear()
}

function parseTime(time)
{
	regexp = /^([0-1]?[0-9]|[2][0-3]):([0-5]?[0-9])$/
	result = time.match(regexp)
	if (result != null)
		return [parseInt(result[1]), parseInt(result[2])]
	
	return null;
}

function formatTime(timeArr)
{
	return timeArr[0] + ":" + timeArr[1];
}

function urlEscapeDate(date)
{
	return date.getFullYear() + "-" + (date.getMonth()+1) + "-" + date.getDate() + "-" + date.getHours() + "-" + date.getMinutes()
}

function add(start)
{
	var end = new Date(start)

	response = window.confirm('Book server on ' + getDateStr(start) + " ?");
	if (response) {
		var now = new Date()
		now.setSeconds(0)
		now.setMilliseconds(0)

		var startTime = parseTime(window.prompt("Please Enter Startpoint (HH:MM 24-hrs.)?", new Date().getHours() + ":" + new Date().getMinutes()))
		if (!startTime) {
			window.alert("Invalid value entered. Aborting.");
			return;
		}
		start.setHours(startTime[0])
		start.setMinutes(startTime[1])

		if (start < now) {
			window.alert("Cannot create events in the past")
			return;
		}

		var endTime = parseTime(window.prompt("Please Enter EndPoint (HH:MM 24-hrs.)?", (new Date().getHours()+1) + ":" + new Date().getMinutes()))		
		if (!endTime) {
			window.alert("Invalid value entered. Aborting.");
			return;
		}
		end.setHours(endTime[0])
		end.setMinutes(endTime[1])

		if (end < start) {
			window.alert("Invalid EndPoint. EndPoint must cannot be set before StartPoint")
			return;
		}
		window.location = reqBaseUrl + "/control/book/book?start=" + urlEscapeDate(start) + "&end=" + urlEscapeDate(end)
	}
}


function extend(e)
{
	var end = new Date(start)
	var start = e.start;
	var end = e.end

	response = window.confirm('Change booking starting at ' + getDateStr(start) + " ?");
	if (response) {
		var now = new Date()
		now.setSeconds(0)
		now.setMilliseconds(0)


		var endTime = parseTime(window.prompt("Please Enter EndPoint (HH:MM 24-hrs.)?", end.getHours() + ":" + end.getMinutes()))		
		if (!endTime) {
			window.alert("Invalid value entered. Aborting.");
			return;
		}
		end.setHours(endTime[0])
		end.setMinutes(endTime[1])

		if (end < start) {
			window.alert("Invalid EndPoint. EndPoint must cannot be set before StartPoint")
			return;
		}
		window.location = reqBaseUrl + "/control/book/extend?start=" + urlEscapeDate(start) + "&end=" + urlEscapeDate(end)
	}
}


function kill(start, end)
{
	

	response = window.confirm('Are you sure to delete your reservation on ' + getDateStr(start) + ' ?')
	if (response)
		window.location = reqBaseUrl + "/control/book/kill?start=" + urlEscapeDate(start) + "&end=" + urlEscapeDate(end)
}

// Checks only if the day is after today
function afterToday(date)
{
	now = new Date()
	return (date.getFullYear() > now.getFullYear() || 
		date.getFullYear() == now.getFullYear() && date.getMonth() > now.getMonth() ||
		date.getFullYear() == now.getFullYear() && date.getMonth() == now.getMonth() && date.getDate() >= now.getDate())
}



$(document).ready(function() {

	
	$('#calendar').fullCalendar({
		editable: false,
		events: events,
		year: year,
		month: month,
		day: day,
		firstDay: 1,

		dayClick: function(date) {
			// admins can delete events in the past
			if (afterToday(date)) {

				for (id in events) {
					e = events[id]
					if (e.start.getDate() == date.getDate() && e.start.getMonth() == date.getMonth() &&
					    e.start.getFullYear() == date.getFullYear())
					{
						if (e.owner.toLowerCase() == name.toLowerCase()) {
							extend(e)
							return
						}
					}
				}
			}

			// nobody is supposed to create events in the past
			if (afterToday(date))
				add(date)
		},

		eventClick: function(calEvent, jsEvent, view) {
			if ((calEvent.owner.toLowerCase() == name.toLowerCase() && afterToday(calEvent.start)) || isAdmin)
			{
				kill(calEvent.start, calEvent.end)
			}

			

		}
	});
	
});
