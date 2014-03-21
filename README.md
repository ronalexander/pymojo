PyMoJo
======

A client library for Pyjojo, which lives [here](https://github.com/atarola/pyjojo). Together, they are [Mojojojo](http://i.imgur.com/TW2EiMb.gif)!

## Usage

To interact with a Jojo server running on `localhost:9090`, which uses a self-
signed SSL certificate and HTTP Basic Authentication...

    from pymojo.mojo import Mojo

    mojo = Mojo(endpoint=localhost, port=9090, use_ssl=True, verify=False,
                user="username", password="A good password")
    
    script = mojo.get_script("my_script")
    # script is now a JSON object detailing 

    resp = mojo.run("my_script", params={some_key="some value"})
    # resp is a requests response object from which you can gather a
    # resp.status_code and get the JSON body with resp.json()

    mojo.reload()
    # The Jojo server just reloaded its configuration

## More Details
Jojo is built to present system scripts in the form of a REST API. It has
essentially four functions:

 * Get details about all scripts
 * Get details about one script
 * Reload the configuration
 * Run a script

Mojo is a client library for this, which boils these things down to a
constructor and four functions:

 * `reload()`
 * `run(name, params={})`
 * `get_script(name, use_cache=True)`
 * `__get_scripts()`

The constructor accepts the following arguments:

 * `endpoint` - The network path to the server. This should be an IP or domain.
 * `port` - The port Jojo listens on (default: 3000)
 * `use_ssl` - Whether or not to use HTTPS (default: False)
 * `verify` - Whether to bother verifying Jojo's SSL certificate (default: True)
 * `user` - The username for HTTP Basic Auth (default: None)
 * `password` - The password for HTTP Basic Auth (default: None)

When you run the constructor, Mojo connects to Jojo, downloads the script index,
and caches that data. If you run `get_script`, the data will be returned from
this cache without consulting the server. Pass `use_cache=False` to force a
connection to the server. When you call `reload()`, this cache is refreshed.

You can run `__get_scripts()` manually if you like. Doing so will get you a
dictionary of scripts, but it will not update the cache.

When you call `get_script` with `use_cache=False`, a successful script retrieval
will cause the Mojo's cache to be updated with that data.
