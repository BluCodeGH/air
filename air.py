import os
from pathlib import Path
import readline
import time
from colorama import init, Fore, Style
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from world import World
import converter
import plugin
init(autoreset=True)
converter.init()
plugin.load()

def readConfig(file):
  with open(file) as iF:
    contents = iF.read()
  config = {}
  for line in contents.splitlines():
    line = line.strip()
    if line == "" or line[0] in "#;":
      continue
    k, v = line.split("=", 1)
    k, v = k.strip(), v.strip()
    if k in config:
      config[k].append(v)
    else:
      config[k] = [v]
  return config

configData = readConfig("config.txt")
mcw = Path(configData["minecraftWorlds"][0]).expanduser().resolve()
dev = Path(configData["dev"][0]).expanduser().resolve()

worlds = [((d / "levelname.txt").read_text(), d) for d in mcw.iterdir() if d.is_dir()]
print(Fore.GREEN + "Found worlds: " + Style.RESET_ALL + ", ".join([w for w, _ in worlds]))

readline.parse_and_bind("tab: complete")

world = None
while world is None:
  readline.set_completer(lambda text, i: [world for world, _ in worlds if world.startswith(text)][i])
  name = input(Fore.GREEN + "?" + Style.RESET_ALL + " Enter world to load: ")
  results = [(world, d) for world, d in worlds if world == name]
  if not results:
    results = [(world, d) for world, d in worlds if d.name == name]
    if not results:
      print(Fore.RED + "  Invalid world name entered.")
    else:
      world = results[0]
      print(Fore.BLUE + "  Matched folder, loading " + world[0])
  elif len(results) == 1:
    print(Fore.BLUE + "  Loading " + results[0][0])
    world = results[0]
  else:
    print(Fore.RED + "  Multiple worlds called " + name)
    print(Fore.GREEN + "  Folder names: " + Style.RESET_ALL + ", ".join([d.name for _, d in results]))
    readline.set_completer(lambda text, i: [d.name for _, d in results if d.name.startswith(text)][i])
    name = input(Fore.GREEN + "  ?" + Style.RESET_ALL + " Enter folder name: ")
    if name in [d.name for _, d in results]:
      world = results[0][0], [d for _, d in results if d.name == name][0]
      print(Fore.BLUE + "    Loading " + world[0])
    else:
      print(Fore.RED + "    Invalid folder name entered.")


world = World(world[1], dev)
packs = set()
for pack in world.devPath.glob("*"):
  packs.add(pack.name)
  converter.unison(pack, world.file(pack)[2])
for packType in ["resource", "behavior"]:
  for pack in world.path.joinpath(f"{packType}_packs").glob("*"):
    if pack.name not in packs:
      converter.unison(world.file(pack)[2], pack)

DELAY = 1
class SourceHandler(PatternMatchingEventHandler):
  busy = 0
  def __init__(self):
    super().__init__(ignore_directories=True)

  def dispatch(self, event):
    if time.time() - DestHandler.busy < DELAY:
      return
    SourceHandler.busy = time.time()
    super().dispatch(event)

  @staticmethod
  def on_created(event):
    if os.path.getsize(event.src_path) == 0:
      return
    SourceHandler.on_modified(event)

  @staticmethod
  def on_modified(event):
    source, path, dest = world.file(event.src_path)
    converter.dump([converter.File(source, path, dest)])

  @staticmethod
  def on_deleted(event):
    _, path, dest = world.file(event.src_path)
    converter.delete([path], dest)

  @staticmethod
  def on_moved(event):
    SourceHandler.on_deleted(event)
    event._src_path = event._dest_path
    SourceHandler.on_modified(event)

class DestHandler(PatternMatchingEventHandler):
  busy = 0
  def __init__(self):
    super().__init__(patterns=["*_packs/*"], ignore_directories=True)

  def dispatch(self, event):
    if time.time() - SourceHandler.busy < DELAY:
      return
    DestHandler.busy = time.time()
    super().dispatch(event)

  @staticmethod
  def on_created(event):
    if os.path.getsize(event.src_path) == 0:
      return
    DestHandler.on_modified(event)

  @staticmethod
  def on_modified(event):
    source, path, dest = world.file(event.src_path)
    converter.load([converter.File(source, path, dest)])

  @staticmethod
  def on_deleted(event):
    _, path, _ = world.file(event.src_path)
    print(f"Remember to delete the equivalent of {path}")

  @staticmethod
  def on_moved(event):
    DestHandler.on_deleted(event)
    event._src_path = event._dest_path
    DestHandler.on_modified(event)

observer = Observer()
observer.schedule(SourceHandler(), str(world.devPath), recursive=True)
observer.schedule(DestHandler(), str(world.path), recursive=True)
observer.start()

try:
  while True:
    cmd = input("Ready: ")
    if cmd.strip() == "":
      continue
    if cmd.strip() == "u":
      for pack in world.devPath.glob("*"):
        converter.unison(pack, world.file(pack)[2])
      continue
    try:
      plugin.parse(world, cmd)
    except Exception as e:
      print(Fore.RED + "! " + Style.RESET_ALL + str(e))
except KeyboardInterrupt:
  print(Fore.BLUE + "\nExiting.")
except EOFError:
  print(Fore.BLUE + "\nExiting.")
observer.stop()
observer.join()
