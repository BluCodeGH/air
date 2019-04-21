import pathlib
import readline
from colorama import init, Fore, Style
from world import World
import converter
import plugin
init(autoreset=True)
converter.load()
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
mcw = pathlib.Path(configData["minecraftWorlds"][0]).expanduser().resolve()
dev = pathlib.Path(configData["dev"][0]).expanduser().resolve()

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
world.go(converter.converters)
try:
  while True:
    cmd = input("Ready: ")
    if cmd == "":
      world.go(converter.converters)
    else:
      #try:
        plugin.parse(world, cmd)
      #except Exception as e:
      #  print(Fore.RED + "! " + Style.RESET_ALL + str(e))
except KeyboardInterrupt:
  print(Fore.BLUE + "\nExiting.")
except EOFError:
  print(Fore.BLUE + "\nExiting.")
