import importlib
import pathlib
import re

def match(pattern, path, is_dir):
  s = str(path)
  if is_dir:
    s += "/"
  pattern = pattern.replace("/*", "/[^/]+")
  return re.fullmatch(pattern, s)

class Converter:
  def __init__(self, patterns, process):
    self.patterns = patterns
    self.process = process

  def go(self, source, dest):
    for pattern in self.patterns:
      for path in source.glob("**/*"):
        if path.is_file() and match(pattern, path.relative_to(source), False):
          contents = None
          try:
            contents = path.read_text()
          except UnicodeDecodeError:
            contents = path.read_bytes()
          res = self.process(contents, path.relative_to(source))
          if isinstance(res, str) or isinstance(res, bytes):
            destPath = dest / path.relative_to(source)
            destPath.parent.mkdir(parents=True, exist_ok=True)
            destPath.touch()
            if isinstance(res, str):
              destPath.write_text(res)
            else:
              destPath.write_bytes(res)
          elif isinstance(res, dict):
            for destPath, text in res.items():
              destPath = dest / destPath
              destPath.parent.mkdir(parents=True, exist_ok=True)
              destPath.touch()
              destPath.write_text(text)

class FolderConverter(Converter):
  def go(self, source, dest):
    matched = []
    for pattern in self.patterns:
      for path in source.glob("**/*"):
        if match(pattern, path.relative_to(source), path.is_dir()):
          alreadyMatched = False
          for item in matched:
            try:
              path.relative_to(item)
              alreadyMatched = True
              break
            except ValueError:
              pass
          if alreadyMatched:
            break
          matched.append(path)
          res = self.process(path, path.relative_to(source))
          for destPath, text in res.items():
            destPath = dest / destPath
            destPath.parent.mkdir(parents=True, exist_ok=True)
            destPath.touch()
            destPath.write_text(text)

def fallback(file, path):
  for pattern in patterns:
    if match(pattern, path, False) or any([match(pattern, p, True) for p in path.parents]):
      return
  print("Falling back on", path)
  return file

converters = [Converter([".*"], fallback)]
patterns = []
def load():
  for file in pathlib.Path("converters").glob("*.py"):
    print("Loading converter {}".format(file.stem))
    c = importlib.import_module("converters.{}".format(file.stem))
    patterns.extend(c.patterns)
    if hasattr(c, "convert"):
      converters.append(Converter(c.patterns, c.convert))
    else:
      converters.append(FolderConverter(c.patterns, c.folderConvert))
