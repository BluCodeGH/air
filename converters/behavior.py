import json
import converters.mcjson as mcjson

def convert(text, path):
  dest = path.with_suffix(".json")
  data = mcjson.process(text)
  entity = {
    "description": {
      "identifier": data.pop("identifier"),
      "is_spawnable": True,
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

  final = {"format_version":"1.8.0", "minecraft:entity": entity}
  return {dest: json.dumps(final, indent=2)}

patterns = ["entities/*.mcj"]
