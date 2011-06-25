from PyQt4 import QtCore, QtGui, Qsci
from eric4.QScintilla.Lexers.LexerPython import LexerPython
#Qsci.QsciLexerSQL(self) #QsciLexerPython
foo = Qsci.QsciLexerSQL()
bazz = Qsci.QsciLexerPython()


##for i in dir(foo):
##    if i in dir(bazz):
##        try:
##            print i, ":", foo.__getattribute__(i), "::", bazz.__getattribute__(i)
##            print i, ":", foo.__getattribute__(i)(), "::", bazz.__getattribute__(i)()
##        except:
##            pass #print i