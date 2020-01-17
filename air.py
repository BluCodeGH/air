from pathlib import Path
import readline
from colorama import init, Fore, Style
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
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
for pack in world.devPath.glob("*"):
  world.go(Path(pack.parts[-1]), converter.loadAll)
for path in world.devPath.rglob("*"):
  if path.is_dir():
    continue
  path = path.relative_to(world.devPath)
  world.go(path, converter.changed)

class UpdateHandler(FileSystemEventHandler):
  @staticmethod
  def on_modified(event):
    if event.is_directory:
      return
    UpdateHandler._handle(event.src_path, converter.changed)

  @staticmethod
  def on_deleted(event):
    if event.is_directory:
      return
    UpdateHandler._handle(event.src_path, converter.deleted)

  @staticmethod
  def on_moved(event):
    if event.is_directory:
      return
    UpdateHandler._handle(event.src_path, converter.deleted)
    UpdateHandler._handle(event.dest_path, converter.changed)

  @staticmethod
  def _handle(path, fn):
    path = Path(path).relative_to(world.devPath)
    world.go(path, fn)

observer = Observer()
observer.schedule(UpdateHandler(), str(world.devPath), recursive=True)
observer.start()

try:
  while True:
    cmd = input("Ready: ")
    if cmd.strip() == "":
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
