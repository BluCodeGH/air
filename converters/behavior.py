from collections import OrderedDict
import json
from converter import TextConverter

class Behavior(TextConverter):
  def priority(self):
    return 10

  def dump(self, text):
    data = json.loads(text)
    entity = {
      "description": {
        "identifier": data.pop("identifier"),
        "is_spawnable": bool(data.pop("spawn", True)),
        "is_summonable": True,
        "is_experimental": False
      }
    }

    if "component_groups" in data:
      entity["component_groups"] = {}
      for name, components in data.pop("component_groups").items():
        entity["component_groups"][name] = {"minecraft:" + k:v for k, v in components.items()}
    for key in ["animations", "scripts"]:
      if key in data:
        entity["description"][key] = data.pop(key)
    entity["components"] = {"minecraft:" + k:v for k, v in data.pop("components").items()}
    def events(d):
      if isinstance(d, dict):
        for k, v in d.items():
          if k in ["remove", "add"]:
            if isinstance(v, str):
              d[k] = {"component_groups": v.strip().split(" ")}
          elif isinstance(v, (dict, list)):
            events(v)
      else:
        for item in d:
          if isinstance(item, (dict, list)):
            events(item)
    if "events" in data:
      events(data["events"])

    entity.update(data)
    final = {"format_version":"1.13.0", "minecraft:entity": entity}

    return json.dumps(final, indent=2)

  def dump_path(self, path):
    return path.match("bp/entities/*.mcj")

  def load(self, text):
    data = json.loads(text)["minecraft:entity"]

    res = OrderedDict({
      "identifier": data["description"]["identifier"]
    })
    if not data["description"]["is_spawnable"]:
      res["spawn"] = False
    for key in ["animations", "scripts"]:
      if key in data["description"]:
        res[key] = data["description"][key]
    data.pop("description")

    if "component_groups" in data:
      res["component_groups"] = {}
      for name, components in data.pop("component_groups").items():
        res["component_groups"][name] = {k[10:]:v for k, v in components.items()}
    res["components"] = {k[10:]:v for k, v in data.pop("components").items()}
    def events(d):
      if isinstance(d, dict):
        for k, v in d.items():
          if k in ["remove", "add"]:
            if isinstance(v, dict) and "component_groups" in v:
              d[k] = " ".join(v["component_groups"])
          elif isinstance(v, (dict, list)):
            events(v)
      else:
        for item in d:
          if isinstance(item, (dict, list)):
            events(item)
    if "events" in data:
      events(data["events"])

    res.update(data)

    return json.dumps(res)

  def load_path(self, path):
    return path.match("bp/entities/*.json")

Behavior()
