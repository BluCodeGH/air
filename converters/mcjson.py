import json

def _infer(self, text):
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
  try: 
    return float(text)
  except ValueError:
    pass
  return text

def process(self, text):
  res = {}
  wip = ""
  wipKey = None

  def next(res, wipKey, wip):
    if wip == "":
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
  
  if wip != "":
    next(res, wipKey, wip)
  if res == {} and text:
    return _infer(text)
  return res

def convert(text, path, _):
  dest = path.with_suffix(".json")
  data = json.dumps(process(text))
  return {dest: data}

globs = ["entities/*.mcj", "loot_tables/*.mcj"]
