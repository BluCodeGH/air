import importlib
import pathlib

class Converter:
  def __init__(self, globs, process):
    self.globs = globs
    self.process = process

  def go(self, source, dest):
    for glob in self.globs:
      for path in source.glob(glob):
        if path.is_file():
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

def fallback(file, path):
  for glob in globs:
    if path.match(glob):
      return
  return file

converters = [Converter(["**/*"], fallback)]
globs = []
def load():
  for file in pathlib.Path("converters").glob("*.py"):
    print("Loading converter {}".format(file.stem))
    c = importlib.import_module("converters.{}".format(file.stem))
    globs.extend(c.globs)
    converters.append(Converter(c.globs, c.convert))
