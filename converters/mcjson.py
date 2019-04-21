import json

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
        res.append(_infer(wip.strip()))
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
    return float(text)
  except ValueError:
    pass
  return text

def process(text):
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
  def next(res, wipKey, wip):
    if wip == "":
      if wipKey is not None:
        res[wipKey] = {}
      return
    if wipKey is None:
      if None in res:
        processed = process(wip)
        if processed == {wip: {}}:
          res[None].append(_infer(wip))
        else:
          res[None].append(processed)
      else:
        raise SyntaxError("Cannot have indent without heading.")
    elif wipKey in res:
      raise SyntaxError("Duplicate keys {}".format(wipKey))
    else:
      res[wipKey] = process(wip)
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
      next(res, wipKey, wip)
      if res != {} and list(res.keys()) != [None]:
        raise SyntaxError("List must be indented from key in {}".format(text))
      wip = ""
      wipKey = None
      if None not in res:
        res[None] = []
      wip = line[2:]
    elif " " in line and not (line[0] == '"' and line[-1] == '"'):
      next(res, wipKey, wip)
      wip = ""
      wipKey = None
      k, v = line.split(" ", 1)
      res[k] = _infer(v)
    else:
      next(res, wipKey, wip)
      wipKey = line
      wip = ""

  next(res, wipKey, wip)
  if res == {} and text:
    return _infer(text)
  return res

def convert(text, path):
  dest = path.with_suffix(".json")
  data = json.dumps(process(text), indent=2)
  return {dest: data}

patterns = ["loot_tables/*.mcj", "animations/*.mcj", "animation_controllers/*.mcj", "entity/*.mcj", "render_controllers/*.mcj"]
