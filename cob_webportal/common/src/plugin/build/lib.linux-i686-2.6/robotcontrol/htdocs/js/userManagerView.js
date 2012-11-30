(function($) {
	var htmlCode = '<form id="savePrivileges"><div class="userManager"><div class="errorMsg"></div><table class="">\
		<tr class="availablePrivileges"><td class="label">Available Privileges:</td><td class="privilegesList"></td></tr>\
	</table>\
	<input type="submit" value="save" /></form></div>';


	$.fn.renderUserManagerView  = function(data) {
		console.log(data);
	
	    this.addClass('hostManagerView');
	    this.html(htmlCode);

	    var privileges = data.labels;
	    var users = data.users;

	    var concatenatedPrivilegesString = $(".privilegesList");
	    for (var key in privileges)
	        concatenatedPrivilegesString.append(key + ",  ");
	        
		// hide the error msg box at the beginning
		$(".errorMsg").hide();
	    
	    function bitmaskToString(bitmask) {
	        var result = "";
	        var isFirst = true;
	        for (var key in privileges) {
	            if ((privileges[key] & bitmask) == privileges[key]) {
       	            if (!isFirst)
       	                result += " ";
       	                
	                result += key;
	                isFirst = false;
	            }
	        }
	        
	        return result;
	    }
	    
	    function stringToBitmask(string) {
	    	var bitmask = 0;
	    	var part = string.split(/,?\s+/);
	    	console.log(part, string);
	    	
	    	if (string.trim() != "") {
				for (var i=0; i<part.length; i++) {
					if (privileges[part[i].toUpperCase()] == undefined)
						throw new Error('Illegal privilege "' + part[i].toUpperCase() + '" entered');
					bitmask |= privileges[part[i].toUpperCase()];
				}
			}
	    	return bitmask;
	    }
	    
		// render all the users
		var table = $("div.userManager table");
		for (var user in users) {

			table.append($('<tr class="user" />')
				.append($('<td class="label">').text(user))
				.append($('<td />')
					.append($('<input type="text" class="text" />')
						.attr('name', user).val(bitmaskToString(users[user])))
				)
			);
			
		}
		
	    var inputs = $("div.userManager input[type=text]");
	    console.log(inputs)

		console.log("jo hier", $("#savePrivileges"));
		$("#savePrivileges").submit(function(e) {
			try {
				var bitmasks = {}
			
				inputs.each(function(i, input) {
					bitmasks[input.name] = stringToBitmask(input.value);
				});
				$(".errorMsg").hide();
				application.submitPrivileges(bitmasks);
				
			} catch (err) {
				$(".errorMsg").text(err.toString()).show();
			}
			
			e.preventDefault();
			return false;
		});
	}
})(jQuery);
