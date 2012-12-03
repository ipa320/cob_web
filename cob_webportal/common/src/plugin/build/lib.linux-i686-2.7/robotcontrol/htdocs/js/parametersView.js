var parametersViewCode = '<div class="parametersView componentView-content" >\
        <p class="loading">Loading ...</p>\
		<div class="componentView-buttons">\
			<a href="#" class="addField-button">Add Field</a>\
		</div>\
        <table></table>\
    </div>';

var normalFieldRowCode = '<tr class=".row">\
        <td class="name"></td>\
        <td class="value"></td>\
        <td class="edit"><a href="#" class="editButton">Edit</a></td>\
    </tr>';

var editFieldRowCode  = '<tr class=".row">\
        <td class="name"><input type="text" /></td>\
        <td class="value"><input type="text" /></td>\
        <td class="save"><a href="#" class="saveButton">Save</a></td>\
    </tr>';

    
$.fn.renderParametersView = function( actionId ){
    this.html( parametersViewCode );
    this.find( 'table' ).data( 'actionId', actionId );
    var addFieldButton = this.find( '.addField-button' )
        .button({ icons: { primary: 'ui-icon-plus' }})
        .click( $.proxy( addNewBlankField, this ))
        .hide();
}

$.fn.parametersLoadedCallback = function(){
    $( '.loading', this ).remove();
    $( '.addField-button', this ).show();
}
$.fn.addParameterField = function( name, value ){
    var table = $( 'table', this ),
        rows = table.find( '.name' ),
        rowExistsAlready = false;

    rows.each( function( i, row ){
        if( row.innerHTML == name ){
            rowExistsAlready = true;
            return false;
        }
    });

    if( rowExistsAlready )
        return;

    var newRow = createNormalRow( name, value );

    table.append( newRow );
    return newRow;
};

function createNormalRow( name, value, options ){
    var defaultOptions = {
        editable: true
    };

    options = $.extend( {}, defaultOptions, options );

    var newRow = $( normalFieldRowCode );
    var editRowCallback = function(){
        editRow( newRow );
    };
    newRow.find( '.name' ).text( name );
    newRow.find( '.value' ).text( value );
    newRow.find( '.editButton' )
        .button({ icons: { primary: 'ui-icon-pencil' }})
        .click( editRowCallback )
        [ options[ 'editable' ] === false ? 'hide' : 'show' ]();
        
    return newRow;
}

function addNewBlankField(){
    var $this = $( this ),
        newRow = $this.addParameterField( '', '' );

    editRow( newRow );
}

    
function editRow( row ){
    var $row = $( row ),
        name = $row.find( '.name' ).text(),
        value = $row.find( '.value' ).text();

    var editRow = $( editFieldRowCode ),
        nameInput = editRow.find( '.name input' ),
        valueInput = editRow.find( '.value input' );
    var saveRowsCallback = function(){
        var table = editRow.closest( 'table' );
        if( !nameInput.val() || !valueInput.val() ){
            editRow.remove();
        }
        else{
            var normalRow = createNormalRow( nameInput.val(), 
                    valueInput.val(), { editable: false });
            editRow.replaceWith( normalRow );
        }
        saveAllRows( table );
    };
    nameInput.val( name );
    valueInput.val( value );
    editRow.find( '.saveButton' )
        .button({ icons: { primary: 'ui-icon-check' }})
        .click( saveRowsCallback );
    $row.replaceWith( editRow );

    $( '.editButton' ).hide();
}

function saveAllRows( table ){
    var actionId = table.data( 'actionId' ),
        data = {};
    table.find( 'tr' ).each( function(){
        var $this = $( this ),
            name = $this.find( '.name' ).text(),
            value = $this.find( '.value' ).text();
        data[ name ] = value;
    });
    var successCallback = function(){
        table.find( '.editButton' ).show();
    };
    application.saveParameters( actionId, data, {
        success: successCallback
    });
}
    
$.fn.removeParameterField = function( name ){

    var table = $( 'table', this ),
        nameElement = table.find( '.name:contains("' + name + '")' ),
        parent = nameElement.closest( 'tr' );
    parent.remove();
};
