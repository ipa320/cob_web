function chkCompFormular() 
{
	var elements = new Array('title', 'search_name', 'start', 'host_ip');
	for (var i = 0; i < elements.length; i++)
	{
		if (document.compadmin_form[elements[i]].value == "") 
  	{
  		explain( elements[i] );
    	document.compadmin_form[elements[i]].focus();
    	return false;
  	}
  }
  document.compadmin_form.submit()
  return true;
}

function chkHostFormular() 
{
	var elements = new Array('ip', 'user', 'passwd');
	for (var i = 0; i < elements.length; i++)
	{
		if (document.hostadmin_form[elements[i]].value == "") 
  	{
  		if (document.hostadmin_form[elements[0]].value != "localhost")
  		{
  			explain( elements[i] );
    		document.hostadmin_form[elements[i]].focus();
    		return false;
    	}
  	}
  }
	document.hostadmin_form.submit()
  return true;
}

function explain( element )
{
	var explanation = '';
	switch (element) 
	{
  	case "tail_length":
    	explanation = "Durch die Zeilenanzahl beschränken Sie\n die Anzeige der Skriptlog-Datei.\nDefault-Wert ist 15.";
    	break;
    case "title":
    	explanation = "Geben Sie hier den Anzeigetitel dieser Komponente an.\nDiese Angabe ist Pflicht.";
    	break;
    case "start":
    	explanation = "Geben Sie hier den Pfad für das ausführbare Skript ein.\nDiese Angabe ist Pflicht.";
    	break;
    case "host_ip":
    	explanation = "Geben Sie hier den Host-IP-Adresse für das Skript ein.\nDefault-Wert ist localhost.";
    	break;
    case "log":
    	explanation = "Geben Sie hier den Pfad zur Log-Datei an.\nDiese Angabe ist optional.";
    	break;
    case "vars":
    	explanation = "Geben Sie hier die Argumente für den Skriptaufruf an.\nDiese Angabe ist optional.";
    	break;
    case "search_name":
    	explanation = "Die Aktivität eines Skripts auf dem Server wird durch \neine 'grep'-Anfrage festgestellt.\nBitte geben Sie hier das Muster für die 'grep'-Suche ein.\nBsp.: 'Skript '\nDiese Angabe ist Pflicht.";
    	break;  
    case "stop":
    	explanation = "Geben Sie hier den Pfad zum Stoppskript ein.\n";
    	break; 	
    default:
      explanation = "Das Werk eines Meisters riecht nicht nach Schweiß,\n verrät keine Anstrengung und ist von Anfang an fertig.\n-- James McNeill Whistler";
    	break;    
  }
  alert(explanation);
}