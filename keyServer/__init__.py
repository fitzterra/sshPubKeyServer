"""
Module setup.
"""
import os
import cherrypy

version = "0.0.1"
myDir = os.path.abspath(os.path.dirname(__file__))
confDir = myDir

# The global application config dict. It gets populated by entries of the form:
    #   appConf.key: value
# in the [global] section of the config file
appConf = {}

def appConf_namespace(k, v):
    """
    CherryPy namespace handler for the appConf name space.
    It will be called whenever 'appConf.key: value' entries are found in the
    config files.

    See: http://docs.cherrypy.org/en/latest/config.html#namespaces

    This is also where we can manipulate values such as the keyDir option which
    gets an absolute path relative to the myDir if it is not an absolute path
    already.

    @param k: the key parf after the appConf. from the config file
    @param v: the value of the config entry
    """
    # We simply add it to the appConf dict
    appConf[k] = v
    # If it's the keyDir value, and it's not an absolute path, make it absolute
    # based on myDir
    if k=='keyDir' and not v.startswith('/'):
        appConf[k] = os.path.abspath(os.path.join(myDir, v))

def getConfFiles(base='app'):
    """
    Function to search for and return a list of absolute full paths to all config
    files for the given base.

    It will search for config files located in confDir, starting with the base
    name, followed by .conf and also .local.conf - if found, the full names to
    the conf files will be returned as a list.

    For example:
        confDir/
           +-- base.conf
           `-- base.local.conf

    will return:
        ['/full/path/to/confDir/base.conf',
         '/full/path/to/confDir/base.local.conf']

    Note that the main .conf file will always be first to allow this as the
    default config, and if the .local. version is present, it will be 2nd which
    should be local overrides for the defaults.
    """
    cfList = []
    for c in ['conf', 'local.conf']:
        cf = os.path.abspath(os.path.join(confDir, "{}.{}".format(base, c)))
        if os.access(cf, os.F_OK|os.R_OK):
            cfList.append(cf)
    return cfList

# Add the appConf namespace to cherrypy
cherrypy.config.namespaces['appConf'] = appConf_namespace

# Import app.conf and then override with optional app.local.conf
for c in getConfFiles():
    cherrypy.config.update(c)
