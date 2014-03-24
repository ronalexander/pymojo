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
      resp = self.__call("/scripts/" + name)
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
