import base64
import json
import requests

class Mojo:
  def __init__(self, **kwargs):
    """Constructs a Mojo by connecting to a Jojo and caching its scripts"""
    self.endpoint = "http"
    if kwargs.get("use_ssl", False):
      self.endpoint += "s"
    self.endpoint += "://" + kwargs.get("endpoint", "localhost") + ":" \
                  + str(kwargs.get("port", 3000))

    self.verify = kwargs.get("verify", True)
    self.user = kwargs.get("user", None)
    self.password = kwargs.get("password", None)

    if (self.user is not None) & (self.password is not None):
      self.auth = True
    else:
      self.auth = False

    scripts = self.__get_scripts()
    if isinstance(scripts, dict):
      self.scripts = scripts
    else:
      self.scripts = {}

  def __call(self, path, method="GET", data=""):
    """Makes a call to a Jojo"""
    s = requests.Session()
    headers = {
      "Content-Type" : "application/json"
    }

    if self.auth:
      headers["Authorization"] = "Basic " + base64.b64encode(self.user + ":" + self.password)

    req = requests.Request(method,
      self.endpoint + path,
      data=data,
      headers=headers
    ).prepare()

    resp = s.send(req, verify=self.verify)

    return resp


  def __get_scripts(self):
      """Gets a collection of scripts that live on the Jojo"""
      resp = self.__call("/scripts", method="GET")
      if resp.status_code == 200:
        return resp.json()['scripts']
      return None

  def reload(self):
    """Reloads the Jojo's script cache, then stashes that data in the Mojo"""
    r = self.__call("/reload", method="POST")
    self.scripts = self.__get_scripts()

  def get_script(self, name, use_cache=True):
    """Gets data about a script in the Jojo, from the cache or from the Jojo"""
    if use_cache:
      if self.scripts[name] is not None:
        return self.scripts[name]
      else:
        return None
    else:
      resp = self.__call("/scripts/" + name, method="GET")
      if resp.status_code == 200:
        self.scripts[name] = resp.json()['script']
        return self.scripts[name]
      else:
        return None

  def run(self, name, params={}):
    data = None
    if len(params) > 0:
      data = json.dumps(params)

    return self.__call("/scripts/" + name, method="POST", data=data)



def cli(args):
  opts = {}
  opts["endpoint"] = args.endpoint
  opts["port"] = args.port
  opts["user"] = args.user
  opts["password"] = args.password
  opts["use_ssl"] = args.use_ssl
  opts["verify"] = args.verify


  if args.action == "list":
    ls(opts)
  elif args.action == "show":
    show(opts, args)
  elif args.action == "run":
    run(opts, args)

def ls(opts):
  m = Mojo(**opts)
  for s in m.scripts:
    print s

def show(opts, args):
  m = Mojo(**opts)
  script = m.get_script(args.script)
  
  print "Name:", script["name"]
  print "Lock:", script["lock"]
  print "Filename:", script["filename"]
  print "Description:", script["description"]
  print "Parameters:"
  for p in script["params"]:
    print " ", p["name"], ":", p["description"]

def run(opts, args):
  m = Mojo(**opts)

  params = {}
  for p in args.params:
    broken = p.split("=")
    params[broken[0]] = broken[1]

  resp = m.run(args.script, params)
  
  print "Status Code: ", resp.status_code

  print "Headers:"
  for h in resp.headers:
    print " ", h, ":", resp.headers[h]

  j = resp.json()
  print "Script return code:", j["retcode"]
  print "Stderr:", j["stderr"]
  print "Stdout:", j["stdout"]


if __name__ == "__main__":
  import argparse
  parser = argparse.ArgumentParser(description="Mojo command line client")
  parser.add_argument("-e", "--endpoint", dest="endpoint", default="localhost",
                      help="The host to connect to a Jojo instance on")
  parser.add_argument("-p", "--port", dest="port", default=3000,
                      help="The port Jojo is listening on")
  parser.add_argument("-s", "--ssl", action="store_true", dest="use_ssl",
                      default=False, help="Use SSL")
  parser.add_argument("-i", "--ignore-warnings", action="store_false", dest="verify",
                      default=False, help="Ignore SSL certificate security warnings")
  parser.add_argument("-u", "--user", dest="user", default=None,
                      help="The user to authenticate with")
  parser.add_argument("-w", "--password", dest="password", default=None,
                      help="The password to authenticate with")
  parser.add_argument("action", choices=[ "list", "show", "run" ],
                      help="The action you want to take")
  parser.add_argument("script", nargs="?", default=None,
                      help="For 'show' and 'run' commands, this is the relevant script")
  parser.add_argument("params", nargs=argparse.REMAINDER,
                      help="Parameters to pass through the 'run' command in 'key1=value key2=value' format")
  cli(parser.parse_args())
