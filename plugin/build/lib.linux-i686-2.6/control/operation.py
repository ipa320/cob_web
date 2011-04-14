# @package control
# -*- coding: utf8 -*-
#  Module operation
#  
#  @author: Regina Klauser
#  @license: BSD License
#


# 
#  Class encapsulates operation information 
#
class Operation(object):
   
    def __init__( self, cmd, attr, comp_title ):
        self.cmd = cmd
        self.attr = attr
        self.result = ''
        self.err = ''
        self.comp_title = comp_title

        
    def set_result(self, data):
        self.result += data
        
    def set_err(self, data):
        self.err += data
        
    def get_cmd(self):
        return self.cmd  

    def __str__(self):
        return "Operation [cmd='%s', attr='%s', result='%s', err='%s', comp_title='%s']" % (str(self.cmd), str(self.attr), str(self.result), str(self.err), str(self.comp_title))

    def __unicode__(self):
        return u"Operation [cmd='%s', attr='%s', result='%s', err='%s', comp_title='%s']" % (unicode(self.cmd, "utf_8", errors="replace"), unicode(self.attr, "utf_8", errors="replace"), unicode(self.result, "utf_8", errors="replace"), unicode(self.err, "utf_8", errors="replace"), unicode(self.comp_title, "utf_8", errors="replace"))
