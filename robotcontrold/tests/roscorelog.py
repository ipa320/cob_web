import re

if __name__=='__main__':
	f = open('roscore.log', 'r')
	text = ''
	for l in f:
		text += l

	regex1 = re.compile('\x1b\[1m((?:.(?!\x1b))*.)\x1b\[0m', re.DOTALL)
	regex2 = re.compile('\x1b\]2;(.*)\x07')
	regex3 = re.compile('\x1b\[31m((?:.(?!\x1b))*.)\x1b\[0m', re.DOTALL)

	l = text
	l = re.sub(regex1, '<b>\\1</b>', l)
	l = re.sub(regex2, '', l, re.DOTALL)
	l = re.sub(regex3, '<font color="red">\\1</font>', l)

	print l
