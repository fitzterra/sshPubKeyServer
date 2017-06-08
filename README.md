SSH Public Key Server
=====================

The purpose of this project is to make it easy to store and retrieve SSH public
keys in a central and easy to access system. 

If you have multiple clients/users that needs SSH access to multiple
servers/systems, and you use key based authentication for SSH, then this may be
something you can use.

The initial requirements for this project was:
* A central server to store SSH public keys
* It should be easy to add new keys
* It should be easy to retrieve specific keys from any location
* The keys stored on the server should be in a very simple open structure like a
  file system, and not in a database. This is so that it is easy to also
  manage, backup, etc. the keys outside of the running system. Managing the keys
  outside the system should not impact on system integrity.
* Only support for RSA and DSA key types for now
* Auto identify the type of key as it is submitted and disallow obvious invalid
  key types
* The server should be small and easy to deploy - handling large numbers of
  requests per second is not an initial requirement
* A simple REST style API to manage and retrieve keys



Authentication - or the lack thereof!
-------------------------------------
The initial idea is that the service is run without needing any authentication
for adding, deleting or modifying keys. Obviously this implies an environment in
which all users of the service is trusted. 

It would be great to have some form of authentication to allow any user to store
their keys, but only that user manage may mange their own keys. Not too much
thought has gone into how to achieve this yet, without detracting from ease of use
though.

Installation
------------
Still need to be written. Some initial outlines:
* python virtual environment
* cherrypy, python-magic
* pip requirements
* system startup - systemd?
* keys storage folder setup and structure

Make sure `virtualenv` is installed. Then do:
`git clone https://github.com/fitzterra/sshPubKeyServer.git`
`cd sshPubKeyServer`
`virtualenv venv`
`source venv/bin/activate`
`pip install -r requirements.txt`
`mkdir keys`

Now you either go on to the Configuration or, start the server with:
`./runServer.py`
and then access it on port `4321`.

Configuration
-------------
Still to be done. Initial outlines:
* Listining socket address and port
* default and site local config
* debugging and logging?

REST API
--------
The rest API is accessible on the `/key` path on the server. If the host is for
example `server.host[:port]`, then the base API URI (**baseURI**) is:

`http://server.host[:port]/key`

The higherarcical structure of keys are:
> `hostname/username/keyType`

and the URL follows the same structure:
`http://server.host[:port]/key/hostname/username/keyType`


### Getting information or a key
The API allows getting a list of hostnames that we have known users and keys
for, getting a list of users within hostname, getting the types of keys
available for a specific user, and finally, getting a specific key.

#### Getting a list of known hostnames
| For  | Use/Receive        |
| ---- | ------------------ |
| **Request method** | GET |
| **URI** | `http://server.host[:port]/key` |
| **Result** | Status 200 and a list of host names |

#### Getting a list of users within a hostname
| For  | Use/Receive        |
| ---- | ------------------ |
| **Request method** | GET |
| **URI** | `http://server.host[:port]/key/{hostname}` |
| **Result** | Status 200 and a list of users |
| **Error** | A 4xx status code and a description of the error. |

#### Getting the keys available for a user
| For  | Use/Receive        |
| ---- | ------------------ |
| **Request method** | GET |
| **URI** | `http://server.host[:port]/key/{hostname}/{user}` |
| **Result** | Status 200 and the avialable key types |
| **Error** | A 4xx status code and a description of the error. |

#### Getting the key for a user
| For  | Use/Receive        |
| ---- | ------------------ |
| **Request method** | GET |
| **URI** | `http://server.host[:port]/key/{hostname}/{user}/{keyType}` |
| **Result** | Status 200 and public key as a string |
| **Error** | A 4xx status code and a description of the error. |


### Storing a key
Keys are uploaded to the URI identifying the **hostname**, and **user** the key
is for, using an HTTP **POST**. The server will automatically identify the key
type and store it under that type.

The **POST** is a standard `application/x-www-form-urlencoded` type request with
the body having the key/value pair as:

`key=urlencoded-ssh-public-key`

The key must be URL encoded since it contains characters that may cause problems
if not encoded.

The hostname and user names are both validated to make sure they are made
up of only valid characters.

| For  | Use/Receive        |
| ---- | ------------------ |
| **Request method** | POST |
| **URI** | `http://server.host[:port]/key/{hostname}/{user}` |
| **Result** | Status 201 to indicate the key was stored. |
| **Error** | A 4xx status code and a description of the error. |

For an RSA key generated for user `joe`, on the host `joe.laptop`, and stored in
the standard openSSH directory, this `curl` request will store the key:

`curl --data-urlencode key@/home/joe/.ssh/id_rsa.pub http://server/key/joe.laptop/joe`

### Updating/Replacing a key
If a public key for a user on the same host has changed, it can be updated using
a HTTP **PUT** request. Since a **POST** can only be used to store a new key, it
will fail when trying to replace an existing key, and therefore a **PUT** is
needed.

| For  | Use/Receive        |
| ---- | ------------------ |
| **Request method** | PUT |
| **URI** | `http://server.host[:port]/key/{hostname}/{user}` |
| **Result** | Status 200 to indicate the key was replaced. |
| **Error** | A 4xx status code and a description of the error. |

For an updated RSA key for user `joe`, on the host `joe.laptop`, and stored in
the standard openSSH directory, this `curl` request will update the existing key:

`curl -X PUT --data-urlencode key@/home/joe/.ssh/id_rsa.pub http://server/key/joe.laptop/joe`

### Deleting a key
A key can be deleted using the HTTP **DELETE** method. There are **no** warnings
or confirmations to delete a key, and once it's deleted, it can not be
undeleted!

| For  | Use/Receive        |
| ---- | ------------------ |
| **Request method** | DELETE |
| **URI** | `http://server.host[:port]/key/{hostname}/{user}` |
| **Result** | Status 200 to indicate the key was deleted. |
| **Error** | A 4xx status code and a description of the error. |


ToDo
----
**Lots!**

In no particular order
* Logging
* Web interface
* Management client wrapper - could be bash around curl
* Content type handling: JSON, plain text, yaml, plain with extra info, plain
  but machine readable, etc.


