"""
auth_demo.py

Created by Kang Zhang 2009-08-14
"""

import keyring
import getpass

def main():
    """This scrip demos how to use keyring facilite the authorization. The
    username is stored in a config named 'auth_demo.cfg'
    """
    db = 'STG_PLM'
    user = 'informat'
    password = keyring.get_password(db, user)
    print password

##    if password == None or not auth(username, password):
##
##        while 1:
##            username = raw_input("Username:\n")
##            password = getpass.getpass("Password:\n")
##
##            if auth(username, password):
##                break
##            else:
##                print "Authorization failed."
##
##        # store the username
##        config.set('auth_demo_login', 'username', username)
##        config.write(open(config_file, 'w'))
##
##        # store the password
##        keyring.set_password('auth_demo_login', username, password)
##
##    # the stuff that needs authorization here
##    print "Authorization successful."

if __name__ == "__main__":
    main()