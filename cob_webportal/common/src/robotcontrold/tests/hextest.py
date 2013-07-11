import binascii, re

def asciirepl(match):
  # replace the hexadecimal characters with ascii characters
  s = match.group()  
  return ''# binascii.unhexlify(s)  

def reformat_content(data):
  p = re.compile(r'\\x(\w{2})')
#  return p.sub(asciirepl, data)
  return data

hex_string = '\x70f=l\x26hl=en\x26geocode=\x26q\x3c \n \x1b[1m blablabl\x1b[0m'
ascii_string = reformat_content(hex_string)

print ascii_string
