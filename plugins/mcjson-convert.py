import json
import pathlib
from plugin import command

simple = (int, float, bool, str)
def enc(obj):
  res = ""
  if isinstance(obj, dict):
    for k, v in obj.items():
      if isinstance(v, simple):
        res += "{} {}\n".format(k, v)
      else:
        res += "{}\n".format(k)
        for line in enc(v).splitlines():
          res += "  " + line + "\n"
  elif isinstance(obj, list):
    for item in obj:
      if isinstance(item, simple):
        res += "- {}\n".format(item)
      else:
        res += "- " + enc(item).replace("\n", "\n  ")[:-2]
  else:
    raise ValueError("Invalid type of json object {}".format(type(obj)))
  return res

@command
def mcj(world, path):
  if not pathlib.Path(path).expanduser().is_absolute():
    path = (world.devPath / path)
  if not path.exists():
    raise FileNotFoundError("Could not locate file {}".format(path))
  if path.is_dir():
    paths = path.glob("*.json")
  else:
    paths = [path]
  for file in paths:
    try:
      data = json.loads(file.read_text("utf-8"))
    except json.JSONDecodeError:
      raise ValueError("Invalid JSON in {}".format(file))
    file.write_text(enc(data), "utf-8")
    file.rename(file.with_suffix(".mcj"))
  return True
