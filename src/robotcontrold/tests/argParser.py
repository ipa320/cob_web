values={};
string = 'a=1&b=2&c=etwas \& "besonderes"&d=3&e=4&ab=a\&b';

# seperate the string by the escaped amp
i=0;
keyValuePairs=[]
for part in string.split('\&'):
	# split the string by amp
	split = part.split('&')

	# if this is not the first part, append the first item to
	# the last item of the previous part. Remove the item 
	# afterwards
	if i != 0:
		keyValuePairs[-1] += ' & ' + split[0];
		split = split[1:]
	keyValuePairs += split
	i += 1


# split the key / values
for keyValuePair in keyValuePairs:
	key, value = keyValuePair.split('=', 1) if keyValuePair.find('=') > 0 else (keyValuePair, None)
	values[key] = value

print values
#print parts
