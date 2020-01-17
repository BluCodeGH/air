import filecmp
import importlib
import os
from pathlib import Path

class Converter:
  _converters = {}
  def __init__(self):
    print("Loaded converter {}".format(self.__class__.__name__))
    p = self.priority()
    if p in self._converters:
      print("Err: Duplicate priority between {} and {}".format(self, self._converters[p]))
      return
    self._converters[p] = self

  # Lowest to greatest
  def priority(self):
    raise NotImplementedError

  # False -> skip
  # True -> process and continue
  # Path -> process and continue, eventually write to path
  def dump_path(self, path):
    raise NotImplementedError

  # convert output path to input path, return None if won't process
  def load_path(self, path):
    raise NotImplementedError

class TextConverter(Converter):
  # air -> world
  def dump(self, text):
    raise NotImplementedError

  # world -> air
  def load(self, text):
    raise NotImplementedError

  # get file relative to text when dumping/loading
  def _get(self, path):
    raise Exception("_get method not replaced.")

class FileConverter(Converter):
  # air -> world
  def dump(self, source, path, dest):
    raise NotImplementedError

  # world -> air
  def load(self, source, path, dest):
    raise NotImplementedError



class Symlink(FileConverter):
  def priority(self):
    return 100

  def dump(self, source, path, dest):
    if path.name.startswith("."):
      return
    if (dest / path).is_symlink():
      if (dest / path).resolve() != source / path:
        print(f"Warning: Couldn't dump path {path} as another symlink already exists.")
      return
    if (dest / path).exists():
      print(f"Warning: Couldn't dump path {path} as the destination already exists.")
      return
    (dest / path).parent.mkdir(parents=True, exist_ok=True)
    os.symlink(source / path, dest / path)

  def dump_path(self, path):
    for converter in self._converters.values():
      if converter != self and converter.dump_path(path):
        return False
    return True

  def load(self, source, path, dest):
    if (dest / path).is_symlink():
      if (dest / path).resolve() != source / path:
        print(f"Warning: Couldn't load path {path} as symlink points to wrong location.")
      return
    if (source / path).exists():
      if not filecmp.cmp(source / path, dest / path):
        print(f"Warning: Couldn't load path {path} as the source already exists.")
      else:
        (dest / path).unlink()
    else:
      (source / path).parent.mkdir(parents=True, exist_ok=True)
      os.rename(dest / path, source / path)
    os.symlink(source / path, dest / path)

  def load_path(self, path):
    for converter in self._converters.values():
      if converter != self and converter.load_path(path):
        return False
    return True

Symlink()

def init():
  for file in (Path(__file__).parent / "converters").glob("*.py"):
    #print("Loading converter {}".format(file.stem))
    importlib.import_module("converters.{}".format(file.stem))

# source / path = file, dest is equivalent to source
def changed(source, path, dest):
  def _get(file):
    if file.startswith("source/"):
      return (source / path).with_name(file[7:]).read_text()
    if file.startswith("dest/"):
      return (dest / path).with_name(file[5:]).read_text()
    return (source / path).with_name(file).read_text()
  data = None
  destPath = path
  for _, converter in sorted(Converter._converters.items(), key=lambda k: k[0]):
    try:
      if not (dump := converter.dump_path(path)):
        continue
    except ValueError:
      for path2 in (source / path).parent.glob("*"):
        if path2.is_dir() or path2 == source / path:
          continue
        path2 = path2.relative_to(source)
        changed(source, path2, dest)
      return
    if isinstance(converter, FileConverter):
      converter.dump(source, path, dest)
      return
    if data is None:
      data = (source / path).read_text()
    converter._get = _get
    data = converter.dump(data)
    converter._get = None
    if isinstance(dump, Path):
      destPath = dump
  (dest / destPath).parent.mkdir(parents=True, exist_ok=True)
  (dest / destPath).write_text(data)

def deleted(_, path, dest):
  destPath = path
  for _, converter in sorted(Converter._converters.items(), key=lambda k: k[0]):
    if (dump := converter.dump_path(path)) and isinstance(dump, Path):
      destPath = dump
  print("DELETE", dest / destPath)
  (dest / destPath).unlink()

def load(source, path, dest):
  def _get(file):
    if file.startswith("source/"):
      return (source / path).with_name(file[7:]).read_text()
    if file.startswith("dest/"):
      return (dest / path).with_name(file[5:]).read_text()
    return (dest / path).with_name(file).read_text()
  data = None
  srcPath = path
  for _, converter in sorted(Converter._converters.items(), key=lambda k: k[0], reverse=True):
    if not (dump := converter.load_path(path)):
      continue
    if isinstance(converter, FileConverter):
      converter.load(source, path, dest)
      return
    if data is None:
      data = (dest / path).read_text()
    converter._get = _get
    data = converter.load(data)
    converter._get = None
    if isinstance(dump, Path):
      srcPath = dump
  if (source / srcPath).exists():
    if (source / srcPath).read_text().strip() == data.strip():
      return
    print(data)
    choice = ""
    while choice == "" or choice not in "><s":
      choice = input("Warning: {} source and dest are different. air [><s] world: ".format(srcPath))
    if choice == "s":
      return
    if choice == ">":
      changed(source, srcPath, dest)
      return
  (source / srcPath).parent.mkdir(parents=True, exist_ok=True)
  (source / srcPath).write_text(data)

def loadAll(source, _, dest):
  for path in dest.rglob("*"):
    if path.is_dir():
      continue
    path = path.relative_to(dest)
    load(source, path, dest)
