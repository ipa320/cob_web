import re

if __name__=='__main__':
	f = open('2d.log', 'r')
	text = ''
	for l in f:
		text += l

#	regex1 = re.compile('\x1b\[1m((?:.(?!\x1b))*.)\x1b\[0m', re.DOTALL)
#	regex2 = re.compile('\x1b\]2;(.*)\x07')
#	regex3 = re.compile('\x1b\[31m((?:.(?!\x1b))*.)\x1b\[0m', re.DOTALL)

	regex1 = re.compile('\x1b\[1m((?:.(?!\x1b))*.)\x1b\[0m', re.DOTALL)
	regex2 = re.compile('\x1b\]2;(.*)\x07')
	# red
	regex3 = re.compile('\x1b\[31m((?:.(?!\x1b))*.)\x1b\[0m', re.DOTALL)
	# yellow
	regex4 = re.compile('\x1b\[33m((?:.(?!\x1b))*.)\x1b\[0m', re.DOTALL)
	regex5 = re.compile('\x00', re.DOTALL)
	regex6 = re.compile('\x1b[^\s\.]*')

	l = text
#	l = re.sub(regex1, '<b>\\1</b>', l)
#	l = re.sub(regex2, '', l, re.DOTALL)
#	l = re.sub(regex3, '<font color="red">\\1</font>', l)
	l = re.sub(regex1, '<b>\\1</b>', l)
	l = re.sub(regex2, '', l, re.DOTALL)
	l = re.sub(regex3, '<font color="red"><b>\\1</b></font>', l)
	l = re.sub(regex4, '<font color="orange"><b>\\1</b></font>', l);
	l = re.sub(regex5, '', l)
	l = re.sub(regex6, '', l)

	print l
