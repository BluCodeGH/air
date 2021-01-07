import json
from converter import Converter
from converters import mcjson

def update(d1, d2):
  for k in d2.keys():
    if k in d1 and isinstance(d1[k], dict) and isinstance(d2[k], dict):
      update(d1[k], d2[k])
    else:
      d1[k] = d2[k]

def difference(d1, d2):
  res = {}
  for k in d1:
    if k in d2:
      if isinstance(d1[k], dict) and isinstance(d2[k], dict):
        if d := difference(d1[k], d2[k]):
          res[k] = d
      elif d1[k] != d2[k]:
        res[k] = d1[k]
    else:
      res[k] = d1[k]
  return res

class Template(Converter):
  @property
  def priority(self):
    return 5

  def dump(self, file):
    if file.path.name == "TEMPLATE.json":
      return None
    if file.path.suffixes[-2:] != [".template", ".json"]:
      return file
    data = json.loads(file.contents)
    #variables = data.pop("variables", {})
    try:
      template = mcjson.dump(file.source.with_name("TEMPLATE.mcj").read_text())
    except FileNotFoundError:
      print("Not found template for", file.source)
      return file
    update(template, data)
    # template = updateVars(template, variables)
    file.contents = json.dumps(template, indent=2)
    return file

  def load(self, file):
    if file.path.suffixes[-2:] != [".template", ".json"]:
      return file
    final = json.loads(file.contents)
    try:
      template = mcjson.dump(file.dest.with_name("TEMPLATE.mcj").read_text())
    except FileNotFoundError:
      print("Not found template for", file.dest)
      return file
    original = difference(final, template)
    file.contents = json.dumps(original, indent=2)
    return file

Template()
