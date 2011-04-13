itemPriority = -1
activeItem = null
relativePosition = 0

$(document).ready(function() {
	activeItem = $($("li.active")[1])

	$(".arrow_up").css("cursor", "pointer")
	$(".arrow_down").css("cursor", "pointer")
	$(".arrow_up").click(moveItemUp)
	$(".arrow_down").click(moveItemDown)
	
	itemPriority = getItemPriority(activeItem)

	$("input#title").keydown( updateName )
	$("input#title").keyup( updateName )

	$("#parent").change( parentChange )

	updateArrows()
	updateForm()
})

function updateName(str, str2)
{
	activeItem.children(".title").text($("input#title").val())
}

function getItemPriority(activeItem)
{
	prioString = activeItem.attr("class")
	result = prioString.match(/priority-(-?[0-9])/)

	if (result == null || result.length != 2)
		window.alert("Could not parse the class-string: " + prioString)
	else
		return parseInt(result[1])
}

function parentChange()
{
	newParentName = $("#parent").val().replace(/\s+/g, '')
	if (newParentName == "")
		newParent = $("div.navtabs")
	else
		newParent = $("li.comp-" + newParentName)

	itemPriority = -1
	relativePosition = 0

	list = newParent.children("ul")
	if (list.children().size() > 0)
		activeItem.insertBefore(list.children().first())
	else
		list.append(activeItem)

	updateArrows()
	updateForm()
}

function moveItemUp()
{
//	window.alert("prev:\t" + activeItem.prev().attr("class") + "\nnext:\t" + activeItem.next().attr("class"))

	relativePosition--
	exchangeItems(activeItem.prev())
	updateArrows()
	updateForm()
}
function moveItemDown()
{
//	window.alert("prev:\t" + activeItem.prev().attr("class") + "\nnext:\t" + activeItem.next().attr("class"))

	relativePosition++
	exchangeItems(activeItem.next())
	updateArrows()
	updateForm()
}
function exchangeItems(partnerItem)
{
	newPriority = getItemPriority(partnerItem)

	if (partnerItem.size() != 1)
		window.alert("Unexpected error occured: Couldn't find partner node with priority: " + newPriority)

	else {
		if (newPriority < itemPriority)
			activeItem.insertBefore(partnerItem)
		else
			activeItem.insertAfter(partnerItem)
		
		activeItem.removeClass("priority-" + itemPriority)
		activeItem.addClass("priority-" + newPriority)
		partnerItem.removeClass("priority-" + newPriority)
		partnerItem.addClass("priority-" + itemPriority)

		itemPriority = newPriority
	}
}

function updateArrows()
{
	if (activeItem.prev().size() > 0)
		$(".arrow_up").show()
	else
		$(".arrow_up").hide()

	if (activeItem.next().size() > 0 && !activeItem.next().hasClass("priority-null"))
		$(".arrow_down").show()
	else
		$(".arrow_down").hide()
}

function updateForm()
{
	if (relativePosition > 0)
		$("#form_priority").attr("value", itemPriority+0.5)

	else if (relativePosition < 0)
		$("#form_priority").attr("value", itemPriority-0.5)

	else
		$("#form_priority").attr("value", itemPriority)
}
