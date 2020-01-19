import json
import re
from converter import Converter

def _infer(text):
  text = text.strip()
  if text[0] == '"' and text[-1] == '"':
    return text[1:-1]
  if text[0] == '[' and text[-1] == ']':
    res = []
    wip = ""
    iq = False
    for c in text[1:-1].strip():
      if c == '"':
        iq = not iq
      elif c == " " and not iq:
        res.append(_infer(wip.strip(" ,")))
        wip = ""
      else:
        wip += c
    if wip.strip() != "":
      res.append(_infer(wip.strip()))
    return res
  if text[0] == '{' and text[-1] == '}':
    res = {}
    wip = ""
    for c in text[1:-1]:
      if c == ",":
        k, v = wip.strip().split(" ", 1)
        res[k] = _infer(v)
        wip = ""
      else:
        wip += c
    if wip.strip() != "":
      k, v = wip.strip().split(" ", 1)
      res[k] = _infer(v)
    return res
  if text == "false":
    return False
  if text == "true":
    return True
  try:
    return int(text)
  except ValueError:
    pass
  try:
    return float(text)
  except ValueError:
    pass
  return text

def dump(text):
  res = {}
  wip = ""
  wipKey = None

  """
  wipKey  wip
  None    None: Start of a file
  *       None: empty tag {}
  None    *: in a list or random indent
  *       *: k, v
  """
  def finish(res, wipKey, wip):
    if wip == "":
      if wipKey is not None:
        res[wipKey] = {}
      return
    if wipKey is None:
      if None in res:
        if _infer(wip) != wip:
          res[None].append(_infer(wip))
        else:
          processed = dump(wip)
          if processed == {wip: {}}:
            res[None].append(_infer(wip))
          else:
            res[None].append(processed)
      else:
        raise SyntaxError("Cannot have indent without heading.")
    elif wipKey in res:
      raise SyntaxError("Duplicate keys {}".format(wipKey))
    else:
      res[wipKey] = dump(wip)
      if None in res[wipKey]:
        res[wipKey] = res[wipKey][None]

  for line in text.splitlines():
    if line.strip() == "" or line.strip()[0] == "#":
      continue
    if line.startswith("  "):
      if wip:
        wip += "\n"
      wip += line[2:]
    elif line.startswith("- "):
      finish(res, wipKey, wip)
      if res != {} and list(res.keys()) != [None]:
        raise SyntaxError("List must be indented from key in {}".format(text))
      wip = ""
      wipKey = None
      if None not in res:
        res[None] = []
      wip = line[2:]
    elif " " in line and not (line[0] == '"' and line[-1] == '"'):
      finish(res, wipKey, wip)
      wip = ""
      wipKey = None
      k, v = line.split(" ", 1)
      res[k] = _infer(v)
    else:
      finish(res, wipKey, wip)
      wipKey = line
      wip = ""

  finish(res, wipKey, wip)
  if res == {} and text:
    return _infer(text)
  if len(res.keys()) == 1 and None in res:
    return res[None]
  return res

simple = (int, float, str)
def load(obj):
  res = ""
  if isinstance(obj, dict):
    for k, v in obj.items():
      if isinstance(v, bool):
        res += "{} ".format(k)
        if v:
          res += "true\n"
        else:
          res += "false\n"
      elif isinstance(v, simple):
        if isinstance(v, str) and (" " in v or v.isdecimal() or len(v) == 0):
          res += "{} \"{}\"\n".format(k, v)
        else:
          res += "{} {}\n".format(k, v)
      else:
        if isinstance(v, list) and 1 < len(v) < 4:
          for item in v:
            if not isinstance(item, simple) or (isinstance(item, str) and (" " in item or len(item) > 10)):
              break
          else:
            res += "{} [{}]\n".format(k, " ".join([(str(item) if not isinstance(item, str) or not item.isdecimal() else "\"{}\"".format(item)) for item in v]))
            continue
        res += "{}\n".format(k)
        for line in load(v).splitlines():
          res += "  " + line + "\n"
  elif isinstance(obj, list):
    for item in obj:
      if isinstance(item, simple):
        if isinstance(item, str) and (" " in item or item.isdecimal() or len(item) == 0):
          res += "- \"{}\"\n".format(item)
        else:
          res += "- {}\n".format(item)
      else:
        res += "- " + load(item).replace("\n", "\n  ")[:-2]
  else:
    raise ValueError("Invalid type of json object {}".format(type(obj)))
  return res

comment = re.compile(r"//.*|/\*.+?\*/")
class MCJson(Converter):
  @property
  def priority(self):
    return 0

  def dump(self, file):
    if file.path.suffix != ".mcj":
      return file
    obj = dump(file.contents)
    file.contents = json.dumps(obj, indent=2).replace("\\u00a7", "§")
    file.path = file.path.with_suffix(".json")
    return file

  def load(self, file):
    if file.path.suffix != ".json":
      return file
    text = comment.sub("", file.contents)
    file.contents = load(json.loads(text))
    file.path = file.path.with_suffix(".mcj")
    return file

  def delete(self, path):
    if path.suffix != ".mcj":
      return path
    return path.with_suffix(".json")

MCJson()
