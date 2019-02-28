import json

def _infer(text):
  text = text.strip()
  if text[0] == '"' and text[-1] == '"':
    return text[1:-1]
  if text[0] == '[' and text[-1] == ']':
    res = []
    wip = ""
    for c in text[1:-1]:
      if c == ",":
        res.append(_infer(wip.strip()))
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
      else:
        wip += c
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

  def next(res, wipKey, wip):
    if wip == "":
      if wipKey is not None:
        res[wipKey] = {}
      return
    if wipKey is None:
      raise SyntaxError("Cannot have indent without heading.")
    if wipKey in res and isinstance(res[wipKey], list):
      res[wipKey].append(process(wip))
    elif wipKey in res:
      raise SyntaxError("Must start list with -")
    else:
      res[wipKey] = process(wip)

  for line in text.splitlines():
    if line.strip() == "" or line.strip()[0] == "#":
      continue
    if line.startswith("  "):
      if wip:
        wip += "\n"
      wip += line[2:]
    elif line.startswith("- "):
      next(res, wipKey, wip)
      wip = ""
      if wipKey not in res:
        res[wipKey] = []
      wip = line[2:]
    elif " " in line:
      next(res, wipKey, wip)
      wip = ""
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

patterns = [ "loot_tables/*.mcj" ]
