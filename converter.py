from typing import Union, List
import filecmp
import importlib
import os
from pathlib import Path

def write(path, contents):
  path.parent.mkdir(parents=True, exist_ok=True)
  if isinstance(contents, str):
    path.write_text(contents)
  else:
    path.write_bytes(contents)

def read(path):
  try:
    contents = path.read_text()
  except UnicodeDecodeError:
    contents = path.read_bytes()
  return contents

# Files always go source -> dest, so when loading they are reversed
class File:
  def __init__(self, source, path, dest):
    self._source = source
    self.path = path
    self._dest = dest
    self._contents = None
    self.dirty = False

  @property
  def contents(self):
    if not self.dirty:
      self.dirty = True
      self._contents = read(self.source)
    return self._contents

  @contents.setter
  def contents(self, contents):
    self.dirty = True
    self._contents = contents

  @property
  def source(self):
    return self._source / self.path

  @property
  def dest(self):
    return self._dest / self.path

  def reverse(self):
    return File(self._dest, self.path, self._source)

class Converter:
  _converters = {}
  def __init__(self):
    print("Loaded converter {}".format(self.__class__.__name__))
    if self.priority in self._converters:
      print(f"Err: Duplicate priority between {self} and {self._converters[self.priority]}")
      return
    self._converters[self.priority] = self

  def __lt__(self, other):
    if isinstance(other, Converter):
      return self.priority < other.priority
    return self.priority < other

  # Lowest to greatest
  @property
  def priority(self) -> int:
    raise NotImplementedError

  def dump(self, file: File) -> Union[None, File, List[File]]:
    return file

  def load(self, file: File) -> Union[None, File]:
    return file

  def delete(self, path: Path) -> Union[None, Path, List[Path]]:
    return path

class SymlinkDump(Converter):
  @property
  def priority(self):
    return 100

  def dump(self, file):
    if file.dirty:
      return file
    if file.path.name.startswith("."):
      return None
    if file.dest.is_symlink():
      if file.dest.resolve() != file.source:
        print(f"Warning: Couldn't dump path {file.path} as another symlink already exists.")
      return None
    if file.dest.exists():
      print(f"Warning: Couldn't dump path {file.path} as the destination already exists.")
      return None
    file.dest.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(file.source, file.dest)
    return None
SymlinkDump()

class SymlinkLoad(Converter):
  @property
  def priority(self):
    return -100

  def load(self, file):
    if file.dirty:
      return file
    if file.path.name.startswith("."):
      return None
    if file.source.is_symlink():
      if file.source.resolve() != file.dest:
        print(f"Warning: Couldn't symlink path {file.path} as symlink points to wrong location.")
      return None
    if file.dest.exists():
      if not filecmp.cmp(file.dest, file.source):
        print(f"Warning: Couldn't symlink path {file.path} as the source already exists.")
        return None
      file.source.unlink()
    else:
      file.dest.parent.mkdir(parents=True, exist_ok=True)
      os.rename(file.source, file.dest)
    os.symlink(file.dest, file.source)
    return None
SymlinkLoad()

def init():
  for file in (Path(__file__).parent / "converters").glob("*.py"):
    #print("Loading converter {}".format(file.stem))
    importlib.import_module("converters.{}".format(file.stem))

def _apply(items, fn, *, reverse=False):
  for converter in sorted(Converter._converters.values(), reverse=reverse):
    oldItems = items
    items = []
    for item in oldItems:
      if res := getattr(converter, fn)(item):
        if not isinstance(res, list):
          res = [res]
        items += res
  return items

def dump(files: List[File]):
  files = _apply(files, "dump")
  for file in files:
    if not file.dirty:
      print(f"Warning: Didn't catch file {file.path}.")
    write(file.dest, file.contents)

def load(files: List[File]):
  files = _apply(files, "load", reverse=True)
  for file in files:
    if not file.dirty:
      print(f"Warning: Didn't catch file {file.path}.")
    write(file.dest, file.contents)

def delete(paths: List[Path], dest):
  path = _apply(paths, "delete")
  for path in paths:
    path = dest / path
    if not path.exists():
      print(f"Warning: Can't delete file {path} as it does not exist.")
      continue
    print(f"Deleting {path}")
    #path.unlink()

def _iterate(path):
  for p in path.rglob("*"):
    if p.is_dir():
      continue
    yield p.relative_to(path)

def unison(sourceDir, destDir):
  for path in _iterate(sourceDir):
    files = _apply([File(sourceDir, path, destDir)], "dump")
    for file in files:
      if not file.dest.exists():
        write(file.dest, file.contents)
        continue
      dest = read(file.dest)
      if dest.strip() == file.contents.strip():
        continue
      sources = _apply([file.reverse()], "load", reverse=True)
      for source in sources:
        print(f"{source.path}\n{source.contents}")
      response = ""
      while not response or response not in "<>s":
        response = input(f"Files {file._source.name}/{file.path} differ. air [<>s] world: ")
      if response == ">":
        write(file.dest, file.contents)
      if response == "<":
        for source in sources:
          write(source.dest, source.contents)

  for path in _iterate(destDir):
    files = _apply([File(destDir, path, sourceDir)], "load", reverse=True)
    for file in files:
      if not file.dest.exists():
        write(file.dest, file.contents)
        continue
