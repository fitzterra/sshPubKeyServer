#!/usr/bin/env python
"""
A very simplistic SSH public key server.

The features this server should have:
 * Very simple, but still secure
 * The main purpose is to retrieve public SSH keys by user and/or host, or a
 combination of the user@host
 * Each user at each host may have different types of keys.
 * Only priviledged users can store public keys via HTTP [1]??

[1] Can any user store their public keys? How to authenticate or assign
responsibility? Using an email addy as user key?

"""
import os
import re
import magic
import cherrypy
from keyServer import version, getConfFiles, appConf


class Root(object):
    """
    Site root handler
    """

    @cherrypy.expose
    def index(self):
        """
        Main index page
        """
        return "SSH keys server - v{0}\nTry the /key path.".format(version)

    @cherrypy.expose
    def default(self):
        """
        Default page handler
        """
        self.index()


@cherrypy.expose
class Keys(object):
    """
    Keys requests handlers
    """
    # validation regexes for host, user and key type
    host_re = re.compile(r"^([a-zA-Z0-9](?:(?:[a-zA-Z0-9-]*|(?<!-)\.(?![-.]))*[a-zA-Z0-9]+)?)$")
    user_re = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{2,}$")
    keyT_re = re.compile(r"(rsa|dsa) public key", re.I)


    def __init__(self):
        """
        Class initializer
        """
        self.keysList = self.loadKeys()


    def loadKeys(self, basePath=appConf['keyDir']):
        """
        Reads the full keys structure from disk into a dict as:

        {
            'server1': {
                'user1': {
                    'rsa': "rsa key"
                    'dsa': "dsa key"
                },
                'user2': {
                    'rsa': "rsa key"
                    'dsa': "dsa key"
                },
                ...
            },
            'server2': {
                'user1': {
                    'rsa': "rsa key"
                    'dsa': "dsa key"
                },
                'user2': {
                    'rsa': "rsa key"
                    'dsa': "dsa key"
                },
                ...
            },
            ...
        }
        """
        keys = {}
        fileParts = re.compile(r"^id_([^.]+).pub$")

        # Make sure basePath ends in a dir seperator
        if basePath[-1] != os.path.sep:
            basePath += os.path.sep
        # Run through the keys structure on disk
        for root, dirs, files in os.walk(basePath):
            # We only act when we get to the keys level, which should be 2 levels
            # deep
            levels = root.replace(basePath, "", 1).split(os.path.sep)
            if len(levels) == 2:
                # Find valid files
                for f in files:
                    info = fileParts.search(f)
                    if not info:
                        continue
                    # We now have everything we need to add the key
                    if levels[0] not in keys:
                        keys[levels[0]] = {}
                    if levels[1] not in keys[levels[0]]:
                        keys[levels[0]][levels[1]] = {}
                    with open(os.path.join(root, f), 'r') as k:
                        keys[levels[0]][levels[1]][info.group(1)] = k.read()
        return keys

    def detectKey(self, key):
        """
        Detects the type of public key and returns a string as indicator.
        """
        # Try to identify the key type - magic expects a normal string, but the
        # key may be unicode, so we encode it
        keyType = magic.from_buffer(key.encode('utf-8'))
        # See if magic identified it as a pub key and also the type of key
        keyID = self.keyT_re.search(keyType.lower())
        if keyID:
            return (keyID.group(1), keyType)
        else:
            return (None, keyType)

    def GET(self, host=None, user=None, keyType=None, *otherPath, **dat):
        """
        Get info about stored resources or get keys
        """
        # List the avialable hosts if we do not have a specific host
        if not host:
            hosts = self.keysList.keys()
            hosts.sort()
            return "Available hosts:\n{}".format('\n'.join(hosts))
        elif host not in self.keysList:
            raise cherrypy.HTTPError(400, "Host [{}] not found.".format(host))

        # List the users on host if we do not have a specific user
        if not user:
            users = self.keysList[host].keys()
            users.sort()
            return "Available users:\n{}".format('\n'.join(users))
        elif user not in self.keysList[host]:
            raise cherrypy.HTTPError(
                        400,
                        "User [{}] not found on host [{}]."\
                        .format(user, host))

        # List the user's keys if we do not have a specific key type
        if not keyType:
            keyTypes = self.keysList[host][user].keys()
            keyTypes.sort()
            return "Available key types:\n{}".format('\n'.join(keyTypes))
        elif keyType not in self.keysList[host][user]:
            raise cherrypy.HTTPError(
                        400,
                        "No key type of [{}] exists for user [{}] on host [{}]."\
                        .format(keyType, user, host))
        # return the key
        return self.keysList[host][user][keyType]

    def POST(self, host=None, user=None, *otherPath, **dat):
        """
        Allows adding a new public key
        """

        # We need a host, a user and a key to continue
        if not (host and user and 'key' in dat):
            raise cherrypy.HTTPError(400, "Missing host, user and/or key.")
        # Validate host
        if not self.host_re.search(host):
            raise cherrypy.HTTPError(400, "Invalid host name.")
        # Validate user
        if not self.user_re.search(user):
            raise cherrypy.HTTPError(400, "Invalid user name.")
        # Validate the key type
        keyInfo = self.detectKey(dat['key'])
        if not keyInfo[0]:
            raise cherrypy.HTTPError(400, "Invalid key type. Identified as: {}.".format(keyInfo[1]))

        # Generate the dir path for the new key
        keyPath = os.path.join(appConf['keyDir'], host, user)
        keyName = "id_{}.pub".format(keyInfo[0])
        # Check that it does not already exist
        if os.access(os.path.join(keyPath, keyName), os.F_OK):
            raise cherrypy.HTTPError(409, "This key already exists. Use PUT to replace.")

        # Create the dir tree if it does not already exist
        if not os.access(keyPath, os.F_OK):
            os.makedirs(keyPath)
        # Write the key
        with open(os.path.join(keyPath, keyName), 'w') as f:
            f.write(dat['key'].encode('utf-8'))

        # Update the keys list
        self.keysList = self.loadKeys()

        cherrypy.response.status = "201 Key Created."
        return

    def PUT(self, host=None, user=None, *otherPath, **dat):
        """
        Allows deleting an existing key.
        """
        # We need a host, a user and a key to continue
        if not (host and user and 'key' in dat):
            raise cherrypy.HTTPError(400, "Missing host, user and/or key.")
        # Identify the key type
        keyInfo = self.detectKey(dat['key'])
        if not keyInfo[0]:
            raise cherrypy.HTTPError(400, "Invalid key type. Identified as: {}.".format(keyInfo[1]))
        # Generate the dir path for the key
        keyPath = os.path.join(appConf['keyDir'], host, user,
                               "id_{}.pub".format(keyInfo[0]))
        # Does it exist?
        if not os.access(keyPath, os.F_OK):
            raise cherrypy.HTTPError(400, "Specified key for this host/user not found.")
        # Overwrite it
        with open(keyPath, 'w') as f:
            f.write(dat['key'].encode('utf-8'))
        return

    def DELETE(self, host=None, user=None, keyType=None, *otherPath, **dat):
        """
        Allows deleting an existing key.
        """
        # We need a host, a user and a key type to continue
        if not (host and user and keyType in ['rsa', 'dsa']):
            raise cherrypy.HTTPError(400, "Missing host, user and/or valid key type.")
        # Generate the dir path for the key
        keyPath = os.path.join(appConf['keyDir'], host, user, "id_{}.pub".format(keyType))
        # Does it exist?
        if not os.access(keyPath, os.F_OK):
            raise cherrypy.HTTPError(400, "Specified key for this host/user not found.")
        # Remove it
        os.unlink(keyPath)
        # Can we remove the user dir?
        userDir = os.path.dirname(keyPath)
        if not os.listdir(userDir):
            os.rmdir(userDir)
            # Can we remove the host dir?
            hostDir = os.path.dirname(userDir)
            if not os.listdir(hostDir):
                os.rmdir(hostDir)
        # Update the keys list
        self.keysList = self.loadKeys()

def keysDirIsValid():
    """
    Validates that the keys directory exists and is writable
    """
    assert os.path.isdir(appConf['keyDir']), \
           "Keys dir is not available: {}".format(appConf['keyDir'])
    assert os.access(appConf['keyDir'], os.R_OK|os.W_OK), \
           "Keys dir not writable or readable: {}".format(appConf['keyDir'])

def startServer():
    """
    Starts the server
    """
    keysDirIsValid()
    confFiles = getConfFiles()
    rootApp = Root()
    rootApp.key = Keys()
    rootApp = cherrypy.tree.mount(rootApp, "/", confFiles[0])
    if len(confFiles) > 1:
        rootApp.merge(confFiles[1])

    cherrypy.engine.start()
    cherrypy.engine.block()

if __name__ == '__main__':
    startServer()
