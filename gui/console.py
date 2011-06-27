import sys, os
import traceback
from PyQt4 import QtCore, QtGui, Qsci
import re
import syntax

##class Console2(QtGui.QPlainTextEdit):
##    def __init__(self, prompt='>>> ', startup_message='', parent=None):
##        QtGui.QPlainTextEdit.__init__(self, parent)
##        self.prompt = prompt
##        self.history = []
##        self.namespace = {}
##        self.construct = []
##
##        self.setGeometry(50, 75, 600, 400)
##        self.setWordWrapMode(QtGui.QTextOption.WrapAnywhere)
##        self.setUndoRedoEnabled(False)
##        self.document().setDefaultFont(QtGui.QFont("monospace", 14, QtGui.QFont.Normal))
##        self.showMessage(startup_message)
##
##    def updateNamespace(self, namespace):
##        self.namespace.update(namespace)
##
##    def showMessage(self, message):
##        self.append(message)
##        self.newPrompt()
##
##    def newPrompt(self):
##        if self.construct:
##            prompt = '.' * len(self.prompt)
##            if len(self.construct[-1]) > 0:
##                if self.construct[-1][-1]  == ":":
##                    c = self.construct[-1]
##                    depth = (len(c) - len(c.lstrip(" "))) / 4
##                    prompt += "        " * (depth + 1)
##        else:
##            prompt = self.prompt
##        self.append(prompt)
##        #self.append("____")
##        self.moveCursor(QtGui.QTextCursor.End)
##
##    def getCommand(self):
##        doc = self.document()
##        curr_line = unicode(doc.findBlockByLineNumber(doc.lineCount() - 1).text())
##        curr_line = curr_line.rstrip()
##        curr_line = curr_line[len(self.prompt):]
##        return curr_line
##
##    def setCommand(self, command):
##        if self.getCommand() == command:
##            return
##        self.moveCursor(QtGui.QTextCursor.End)
##        self.moveCursor(QtGui.QTextCursor.StartOfLine, QtGui.QTextCursor.KeepAnchor)
##        for i in range(len(self.prompt)):
##            self.moveCursor(QtGui.QTextCursor.Right, QtGui.QTextCursor.KeepAnchor)
##        self.textCursor().removeSelectedText()
##        self.textCursor().insertText(command)
##        self.moveCursor(QtGui.QTextCursor.End)
##
##    def getConstruct(self, command):
##        if self.construct:
##            prev_command = self.construct[-1]
##            self.construct.append(command)
##            if not prev_command and not command:
##                ret_val = '\n'.join(self.construct)
##                self.construct = []
##                return ret_val
##            else:
##                return ''
##        else:
##            if command and command[-1] == (':'):
##                self.construct.append(command)
##                #print "."
##                #self.moveCursor(QtGui.QTextCursor.Right, QtGui.QTextCursor.KeepAnchor)
##                #self.append("____")
##                return ''
##            else:
##                return command
##
##    def getHistory(self):
##        return self.history
##
##    def setHisory(self, history):
##        self.history = history
##
##    def addToHistory(self, command):
##        if command and (not self.history or self.history[-1] != command):
##            self.history.append(command)
##        self.history_index = len(self.history)
##
##    def getPrevHistoryEntry(self):
##        if self.history:
##            self.history_index = max(0, self.history_index - 1)
##            return self.history[self.history_index]
##        return ''
##
##    def getNextHistoryEntry(self):
##        if self.history:
##            hist_len = len(self.history)
##            self.history_index = min(hist_len, self.history_index + 1)
##            if self.history_index < hist_len:
##                return self.history[self.history_index]
##        return ''
##
##    def getCursorPosition(self):
##        return self.textCursor().columnNumber() - len(self.prompt)
##
##    def setCursorPosition(self, position):
##        self.moveCursor(QtGui.QTextCursor.StartOfLine)
##        for i in range(len(self.prompt) + position):
##            self.moveCursor(QtGui.QTextCursor.Right)
##
##    def runCommand(self):
##        self.append("\n")
##        command = self.getCommand()
##        self.addToHistory(command)
##
##        command = self.getConstruct(command)
##
##        if command:
##            tmp_stdout = sys.stdout
##
##            class stdoutProxy():
##                def __init__(self, write_func):
##                    self.write_func = write_func
##                    self.skip = False
##
##                def write(self, text):
##                    if not self.skip:
##                        stripped_text = text.rstrip('\n')
##                        self.write_func(stripped_text)
##                        QtCore.QCoreApplication.processEvents()
##                    self.skip = not self.skip
##
##            sys.stdout = stdoutProxy(self.append)
##            try:
##                try:
##                    result = eval(command, self.namespace, self.namespace)
##                    if result != None:
##                        self.append(repr(result))
##                except SyntaxError:
##                    exec command in self.namespace
##            except SystemExit:
##                self.close()
##            except:
##                traceback_lines = traceback.format_exc().split('\n')
##                # Remove traceback mentioning this file, and a linebreak
##                for i in (3,2,1,-1):
##                    traceback_lines.pop(i)
##                self.append('\n'.join(traceback_lines))
##            sys.stdout = tmp_stdout
##        self.newPrompt()
##
##    def keyPressEvent(self, event):
##        if event.key() in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
##            self.runCommand()
##            return
##        if event.key() == QtCore.Qt.Key_Home:
##            self.setCursorPosition(0)
##            return
##        if event.key() == QtCore.Qt.Key_PageUp:
##            return
##        elif event.key() in (QtCore.Qt.Key_Left, QtCore.Qt.Key_Backspace):
##            if self.getCursorPosition() == 0:
##                return
##        elif event.key() == QtCore.Qt.Key_Up:
##            self.setCommand(self.getPrevHistoryEntry())
##            return
##        elif event.key() == QtCore.Qt.Key_Down:
##            self.setCommand(self.getNextHistoryEntry())
##            return
##        elif event.key() == QtCore.Qt.Key_D and event.modifiers() == QtCore.Qt.ControlModifier:
##            self.close()
##        super(Console, self).keyPressEvent(event)


class Console(Qsci.QsciScintilla):
    def __init__(self, prompt='>>> ', startup_message='', parent=None):
        super(Qsci.QsciScintilla, self).__init__(parent)

        self.prompt = prompt
        self.history = []
        self.namespace = {}
        self.construct = []

        #self.setGeometry(50, 75, 600, 400)
        self.setEditor()
        self.setautocomplete()
        #self.setWordWrapMode(QtGui.QTextOption.WrapAnywhere)
        #self.setUndoRedoEnabled(False)
        #self.document().setDefaultFont(QtGui.QFont("monospace", 14, QtGui.QFont.Normal))
        self.showMessage(startup_message)

    def setEditor(self):
        self.setInputMethodHints(QtCore.Qt.ImhUppercaseOnly)
        self.setUtf8(True)
        self.setWrapMode(Qsci.QsciScintilla.WrapWord)
        ## Editing line color
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QtGui.QColor("#B2EC5D"))

        ## Indentation
        self.setAutoIndent(True)
        self.setIndentationWidth(4)
        self.setIndentationGuides(1)
        self.setIndentationsUseTabs(0)

    def updateNamespace(self, namespace):
        self.namespace.update(namespace)

    def append_new(self, message):
        self.append(message)
        self.append("\n")

    def showMessage(self, message):
        self.append_new(message)
        #self.append("\n")
        self.newPrompt()

    def newPrompt(self):
        if self.construct:
            prompt = "... " # % '.' * (len(self.prompt) - 1)
            if len(self.construct[-1]) > 0:
                if self.construct[-1][-1]  == ":":
                    c = self.construct[-1]
                    depth = (len(c) - len(c.lstrip(" "))) / 4
                    prompt += "    " * (depth + 2)
        else:
            prompt = self.prompt
        self.append("\n" + prompt)
        self.setCursorPosition(self.lines() + 2, 1000)

    def getselection(self, linefrom, indexfrom, lineto, indexto):
        cursorPosition = self.getCursorPosition()

        self.setSelection(linefrom, indexfrom, lineto, indexto)
        text = unicode(self.selectedText())

        self.setCursorPosition(*cursorPosition)

        return text


    def setautocomplete(self):
        self.sqlLexer = Qsci.QsciLexerSQL(self) #QsciLexerPython #TestQsciLexerPython #$TestQsciLexerPython
        self.api = Qsci.QsciAPIs(self.sqlLexer)

        self.api.prepare()
        self.sqlLexer.setAPIs(self.api)
        self.setLexer(self.sqlLexer)

        self.setAutoCompletionThreshold(2)
        self.setAutoCompletionSource(Qsci.QsciScintilla.AcsAll)
        self.setAutoCompletionCaseSensitivity(False)
        self.setAutoCompletionReplaceWord(True)
        self.setAutoCompletionFillupsEnabled(False)
        self.setAutoCompletionShowSingle(False)

    def getCommand(self):
        #print "sdf"
        #self.text(-1)
        #doc = self.document()
        curr_line = self.getselection(self.lines() - 1, 4, self.lines() - 1, 1000) #unicode(doc.findBlockByLineNumber(doc.lineCount() - 1).text())
        curr_line = curr_line.rstrip()
        #curr_line = curr_line[len(self.prompt):]
        return curr_line

    def setCommand(self, command):
        if self.getCommand() == command:
            return
        self.moveCursor(QtGui.QTextCursor.End)
        self.moveCursor(QtGui.QTextCursor.StartOfLine, QtGui.QTextCursor.KeepAnchor)
        for i in range(len(self.prompt)):
            self.moveCursor(QtGui.QTextCursor.Right, QtGui.QTextCursor.KeepAnchor)
        self.textCursor().removeSelectedText()
        self.textCursor().insertText(command)
        self.moveCursor(QtGui.QTextCursor.End)

    def getConstruct(self, command):
        if self.construct:
            prev_command = self.construct[-1]
            self.construct.append(command)
            if not prev_command and not command:
                ret_val = '\n'.join(self.construct)
                self.construct = []
                return ret_val
            else:
                return ''
        else:
            if command and command[-1] == (':'):
                self.construct.append(command)
                return ''
            else:
                return command

    def getHistory(self):
        return self.history

    def setHisory(self, history):
        self.history = history

    def addToHistory(self, command):
        if command and (not self.history or self.history[-1] != command):
            self.history.append(command)
        self.history_index = len(self.history)

    def getPrevHistoryEntry(self):
        if self.history:
            self.history_index = max(0, self.history_index - 1)
            return self.history[self.history_index]
        return ''

    def getNextHistoryEntry(self):
        if self.history:
            hist_len = len(self.history)
            self.history_index = min(hist_len, self.history_index + 1)
            if self.history_index < hist_len:
                return self.history[self.history_index]
        return ''

    def runCommand(self):

        command = self.getCommand()
        self.addToHistory(command)

        command = self.getConstruct(command)

        if command:
            tmp_stdout = sys.stdout

            class stdoutProxy():
                def __init__(self, write_func):
                    self.write_func = write_func
                    self.skip = False

                def write(self, text):
                    if not self.skip:
                        stripped_text = text.rstrip('\n')
                        self.write_func(stripped_text)
                        QtCore.QCoreApplication.processEvents()
                    self.skip = not self.skip

            sys.stdout = stdoutProxy(self.append_new)
            try:
                try:
                    self.append("\n")
                    result = eval(command, self.namespace, self.namespace)
                    if result != None:
                        self.append_new(repr(result))
                except SyntaxError:
                    exec command in self.namespace
            except SystemExit:
                self.close()
            except:
                traceback_lines = traceback.format_exc().split('\n')
                # Remove traceback mentioning this file, and a linebreak
                for i in (3,2,1,-1):
                    traceback_lines.pop(i)
                self.append_new('\n'.join(traceback_lines))
            sys.stdout = tmp_stdout
        self.newPrompt()

    def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
            self.runCommand()
            return
        if event.key() == QtCore.Qt.Key_Home:
            self.setCursorPosition(0)
            return
        if event.key() == QtCore.Qt.Key_PageUp:
            return
        elif event.key() in (QtCore.Qt.Key_Left, QtCore.Qt.Key_Backspace):
            if self.getCursorPosition() == 0:
                return
        elif event.key() == QtCore.Qt.Key_Up:
            self.setCommand(self.getPrevHistoryEntry())
            return
        elif event.key() == QtCore.Qt.Key_Down:
            self.setCommand(self.getNextHistoryEntry())
            return
        elif event.key() == QtCore.Qt.Key_D and event.modifiers() == QtCore.Qt.ControlModifier:
            self.close()
        super(Console, self).keyPressEvent(event)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    console = Console(startup_message="this is python")
    console.updateNamespace({'myVar1' : app, 'myVar2' : 1234})
    console.show();
    #syntax.PythonHighlighter(console.document())


    sys.exit(app.exec_())