import json
from converter import Converter

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

  # def dump(self, text):
  #   data = json.loads(text)
  #   try:
  #     template = mcjson.dump(self._get("source/TEMPLATE.mcj"))
  #   except FileNotFoundError:
  #     #print("Not found.", text[:15])
  #     return text
  #   update(template, data)
  #   return json.dumps(template, indent=2)

  # def dump_path(self, path):
  #   if path.name == "TEMPLATE.mcj":
  #     raise ValueError
  #   return path.suffixes[-2:] == [".template", ".mcj"]

  # def load(self, text):
  #   final = json.loads(text)
  #   try:
  #     template = mcjson.dump(self._get("source/TEMPLATE.mcj"))
  #   except FileNotFoundError:
  #     return text
  #   original = difference(final, template)
  #   return json.dumps(original)

  # def load_path(self, path):
  #   return path.suffixes[-2:] == [".template", ".json"]

Template()
