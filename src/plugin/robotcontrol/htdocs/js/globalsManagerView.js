var globalsManagerCode = '<table id="globalsManagerTable"></table><a id="newVariable" href="#">Add new Variable</a> &nbsp;&nbsp;<a id="saveVariables" href="#">Save</a>',
    tableRow = '<tr><td><input type="text" style="width:200px" /></td><td><input type="text" style="width:500px" /></td></tr>';

function onAddNewVariable( key, value ){
    addNewRow();
	return false;
}

function addNewRow( key, value ){
	var table = $( '#globalsManagerTable' ),
        row = $( tableRow );

    key = key || '';
    value = value || '';
    var inputs = row.find( 'input' );
    inputs[ 0 ].value = key;
    inputs[ 1 ].value = value;

	table.append( row )
}

function onSaveVariables( ){
	var table = $( '#globalsManagerTable' ),
	    variables = {}
	
	table.find( 'tr' ).each( function( i, tr ){
		var inputs = $( tr ).find( 'input' );
		console.log( inputs );
 		var name = inputs[ 0 ].value,
		    value = inputs[ 1 ].value.replace( '"', '\"' );
		if( name && name.length )
			variables[ name ] = value
	});
	application.saveGlobals( variables );
}

$.fn.renderGlobalsManagerView = function( data ){
    console.log( arguments );

	this.html( globalsManagerCode )
	this.find( '#newVariable' ).click( onAddNewVariable );
	this.find( '#saveVariables' ).click( onSaveVariables );

    for( var key in data ){
        addNewRow( key, data[ key ]);
    }
}
