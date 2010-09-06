
# ======================================================== #
# File automagically generated by GUI2Exe version 0.5.0
# Copyright: (c) 2007-2009 Andrea Gavana
# ======================================================== #

# Let's start with some default (for me) imports...

from distutils.core import setup
from py2exe.build_exe import py2exe

import glob
import os
import zlib
import shutil

# Remove the build folder
shutil.rmtree("build", ignore_errors=True)

# Version
version = int(open("files/setup/setup-version.txt").readline()) + 1
open("files/setup/setup-version.txt", "w").write(str(version))



class Target(object):
    """ A simple class that holds information on our executable file. """
    def __init__(self, **kw):
        """ Default class constructor. Update as you need. """
        self.__dict__.update(kw)


# Ok, let's explain why I am doing that.
# Often, data_files, excludes and dll_excludes (but also resources)
# can be very long list of things, and this will clutter too much
# the setup call at the end of this file. So, I put all the big lists
# here and I wrap them using the textwrap module.

data_files = [('files', ['files/settings.yaml.example']),
              ('files/cache', ['files/cache/counter.txt']),
              ('files/icons', ['files/icons/AddedIcon.ico',
                               'files/icons/sdbe.ico']),
              ('files/sql', ['files/sql/counter.txt']),
              ('files/testDB', ['files/testDB/db_news.sqlite']),
              ('files/setup', ['files/setup/setup-version.txt',
                                'files/setup/changelog.txt']),
              ('sqldrivers', ['files/dll/sqldrivers/qsqlpsql4.dll',
                             'files/dll/sqldrivers/qsqlodbc4.dll',
                             'files/dll/sqldrivers/qsqlmysql4.dll',
                             'files/dll/sqldrivers/qsqlite4.dll']),
              ('imageformats', ['files/dll/imageformats/qico4.dll']),
			  ('.', ['files/dll/qscintilla2.dll'])]



includes = ['sip']
excludes = ['_gtkagg', '_tkagg', 'bsddb', 'curses', 'email', 'pywin.debugger',
            'pywin.debugger.dbgcon', 'pywin.dialogs', 'tcl',
            'Tkconstants', 'Tkinter']
packages = []
dll_excludes = ['libgdk-win32-2.0-0.dll', 'libgobject-2.0-0.dll', 'tcl84.dll',
                'tk84.dll']
icon_resources = [(1, 'files/icons/sdbe.ico')]
bitmap_resources = []
other_resources = []


# This is a place where the user custom code may go. You can do almost
# whatever you want, even modify the data_files, includes and friends
# here as long as they have the same variable name that the setup call
# below is expecting.

# No custom code added


# Ok, now we are going to build our target class.
# I chose this building strategy as it works perfectly for me :-D

GUI2Exe_Target_1 = Target(
    # what to build
    script = "sdbe.pyw",
    icon_resources = icon_resources,
    bitmap_resources = bitmap_resources,
    other_resources = other_resources,
    dest_base = "sdbe",
    version = "0.%s" % version,
    company_name = "No Company",
    copyright = "No Copyrights",
    name = "Py2Exe Sample File",

    )

# No custom class for UPX compression or Inno Setup script

# That's serious now: we have all (or almost all) the options py2exe
# supports. I put them all even if some of them are usually defaulted
# and not used. Some of them I didn't even know about.

setup(

    # No UPX or Inno Setup

    data_files = data_files,

    options = {"py2exe": {"compressed": 0,
                          "optimize": 0,
                          "includes": includes,
                          "excludes": excludes,
                          "packages": packages,
                          "dll_excludes": dll_excludes,
                          "bundle_files": 3,
                          "dist_dir": "files/exe/sdbe-build-%s" % version,
                          "xref": False,
                          "skip_archive": False,
                          "ascii": False,
                          "custom_boot_script": '',
                         }
              },

    zipfile = None,
    console = [],
    windows = [GUI2Exe_Target_1],
    service = [],
    com_server = [],
    ctypes_com_server = []
    )

# This is a place where any post-compile code may go.
# You can add as much code as you want, which can be used, for example,
# to clean up your folders or to do some particular post-compilation
# actions.

# No post-compilation code added

#os.popen('rar a exe\DemoCollector-build-%s.rar exe\DemoCollector-build-%s' % (version, version))

# And we are done. That's a setup script :-D

