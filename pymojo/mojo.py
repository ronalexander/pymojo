import base64
import json
import requests

class Mojo:
  def __init__(self, endpoint, port=3000, use_ssl=False,
               verify=True, user=None, password=None):
    self.endpoint = "http"
    if use_ssl:
      self.endpoint += "s"
    self.endpoint += "://" + endpoint + ":" + str(port)

    self.verify = verify
    self.user = user
    self.password = password

    if (len(user) > 0) & (len(password) > 0):
      self.auth = True
    else:
      self.auth = False

    self.scripts = self.__get_scripts()

  def __call(self, path, method="GET", data=""):
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
      resp = self.__call("/scripts", method="GET")
      return resp.json()['scripts']

  def reload(self):
    r = self.__call("/reload", method="POST")
    self.scripts = self.__get_scripts()

  def get_script(self, name, use_cache=True):
    if use_cache:
      return self.scripts[name]
    else:
      return self.__call("/scripts/" + name).json()['script']

  def run(self, name, params={}):
    if len(params) > 0:
      data = json.dumps(params)
      return self.__call("/scripts/" + name, method="POST", data=data)
    return self.__call("/scripts/" + name, method="POST")
