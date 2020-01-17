import json
import pathlib
import re
from plugin import command

class Options(list):
  def __repr__(self):
    return "O" + super().__repr__()

def types(obj):
  if isinstance(obj, dict):
    d = {}
    for k, v in obj.items():
      d[k] = types(v)
    return d
  if isinstance(obj, list):
    l = Options([])
    for i in obj:
      l = merge(l, types(i))
    if l:
      return [l]
    return "list"
  if isinstance(obj, bool):
    return "bool"
  if isinstance(obj, (float, int)):
    return "num"
  return "string"

def _merge(a, b):
  if isinstance(a, list):
    for item in b:
      if isinstance(item, Options):
        item = item[0]
      a[0] = merge(a[0], item)
  elif isinstance(a, dict):
    for k, v in  b.items():
      if k in a:
        a[k] = merge(a[k], v)
      else:
        a[k] = v
  else:
    raise TypeError("Invalid data to merge:", a)
  return a

def merge(l, t):
  if not isinstance(l, Options):
    if l == t:
      return l
    if not isinstance(l, str) and isinstance(t, type(l)):
      return _merge(l, t)
    l = Options([l])
  elif t in l:
    return l
  if not isinstance(t, str):
    for i, item in enumerate(l):
      if isinstance(t, type(item)):
        l[i] = _merge(item, t)
        return l
  if isinstance(t, Options):
    for item in t:
      if item not in l:
        l.append(item)
    return l
  l.append(t)
  return l

def mergeable(data):
  t = None
  for k, v in data.items():
    if t is None:
      t = type(v)
    elif not isinstance(v, t) or isinstance(v, Options):
      return False
  if t in (bool, str, int, float):
    return True
  if t == list:
    value = None
    for v in data.values():
      if value is None:
        value = v
      elif v != value:
        return False
    return True
  yes = 0
  no = 0
  known = []
  for v in data.values():
    for k in v.keys():
      if k in known:
        yes += 1
      else:
        known.append(k)
        no += 1
  return yes > no

def clean(data):
  if isinstance(data, Options):
    if len(data) == 1:
      return clean(data[0])
    return Options(clean(i) for i in data)
  if isinstance(data, dict):
    for k, v in data.items():
      data[k] = clean(v)
    if len(data) > 15 and mergeable(data):
      for k in data.copy().keys():
        if k != "*":
          if "*" in data:
            data["*"] = merge(data["*"], data.pop(k))
          else:
            data["*"] = data.pop(k)
      data["*"] = clean(data["*"])
  if isinstance(data, list):
    return [clean(i) for i in data]
  return data

def pprint(data, ind=0):
  inds = "  " * ind
  res = ""
  if isinstance(data, Options):
    res += "(\n"
    for item in data:
      res += inds + "  " + pprint(item, ind + 1) + ",\n"
    res = res[:-2] + "\n{})".format(inds)
  elif isinstance(data, list):
    res += "[ " + pprint(data[0], ind + 1) + " ]"
  elif isinstance(data, dict):
    res += "{\n"
    for k, v in data.items():
      res += "{}  {}: {},\n".format(inds, k, pprint(v, ind + 1))
    if data:
      res = res[:-2] + "\n"
    res += inds + "}"
  else:
    res += str(data)
  return res

def analyze(path, selectors=None):
  res = Options()
  for f in path.glob("**/*"):
    if f.is_dir():
      continue
    data = json.loads(re.sub(r"\s*//.*\n", "", f.read_text()))
    for s in (selectors or []):
      data2 = data
      try:
        for ss in s:
          if ss != "*":
            data2 = data2[ss]
          else:
            for v in data2.values():
              res = merge(res, types(v))
            break
        else:
          res = merge(res, types(data2))
      except KeyError:
        pass
  return pprint(clean(res))

def analyzeFile(path, selectors=None):
  data = json.loads(re.sub(r"\s*//.*\n|\s*/\*[\S\s]*?\*/\s*\n", "", path.read_text()))
  for s in (selectors or []):
    data = data[s]
  if "format_version" in data:
    data.pop("format_version")
  return pprint(clean(types(data)))

@command
def bpschema(_, path):
  path = pathlib.Path(path).expanduser()
  if not path.exists() or not path.is_dir():
    raise FileNotFoundError("Invalid path {}".format(path))
  (path / "schema").mkdir(exist_ok=True)
  (path / "schema/components.txt").write_text(analyze(path / "entities", [["minecraft:entity", "components"], ["minecraft:entity", "component_groups", "*"]]))
  (path / "schema/loot_tables.txt").write_text(analyze(path / "loot_tables"))
  (path / "schema/spawn_rules.txt").write_text(analyze(path / "spawn_rules"))
  (path / "schema/trades.txt").write_text(analyze(path / "trading"))
  (path / "schema/items.txt").write_text(analyze(path / "items"))

@command
def rpschema(_, path):
  path = pathlib.Path(path).expanduser()
  if not path.exists() or not path.is_dir():
    raise FileNotFoundError("Invalid path {}".format(path))
  (path / "schema").mkdir(exist_ok=True)
  (path / "schema/animation_controllers.txt").write_text(analyze(path / "animation_controllers"))
  (path / "schema/animations.txt").write_text(analyze(path / "animations"))
  (path / "schema/entity.txt").write_text(analyze(path / "entity"))
  (path / "schema/particles.txt").write_text(analyze(path / "particles"))
  (path / "schema/render_controllers.txt").write_text(analyze(path / "render_controllers"))
  (path / "schema/biomes.txt").write_text(analyzeFile(path / "biomes_client.json"))
  (path / "schema/blocks.txt").write_text(analyzeFile(path / "blocks.json"))
  (path / "schema/items.txt").write_text(analyze(path / "items"))
  (path / "schema/items_offsets.txt").write_text(analyzeFile(path / "items_offsets_client.json"))
  (path / "schema/sounds.txt").write_text(analyzeFile(path / "sounds.json"))
