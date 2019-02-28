import converters.mcjson as mcjson
import json

def convert(text, path):
  dest = path.with_suffix(".json")
  data = mcjson.process(text)
  final = {"format_version":"1.8.0",
    "minecraft:entity": {
      "description": {
        "identifier": data.pop("identifier"),
        "is_spawnable": "false",
        "is_summonable": "true",
        "is_experimental": "false"
      }
    }}
  final["minecraft:entity"]["components"] = {"minecraft:" + k:v for k, v in data.pop("components").items()}
  final["minecraft:entity"].update(data)
  return {dest: json.dumps(final, indent=2)}

patterns = [ "entities/*.mcj" ]
