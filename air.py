import importlib
import pathlib
import cmd

from world import World
import converter

class Air(cmd.Cmd):
  def __init__(self, config):
    self.prompt = "> "
    self.config = config
    self.mcw = pathlib.Path(config["main"]["minecraftWorlds"][0]).expanduser().resolve()
    self.dev = pathlib.Path(config["main"]["dev"][0]).expanduser().resolve()
    self.world = None
    converter.load()
    super().__init__()


  def do_load(self, line):
    results = [d for d in self.mcw.iterdir() if d.is_dir() and (d / "levelname.txt").read_text() == line]
    if len(results) == 0:
      print("Error: Could not find a world called {}".format(line))
      return
    if len(results) == 1:
      self.world = World(results[0], self.dev / line)
    else:
      print("Warning: There are multiple worlds named {}".format(line))
      folder = input("Choose a folder out of {}: ".format(", ".join([r.name for r in results])))
      if folder in [r.name for r in results]:
        self.world = World([r for r in results if r.name == folder][0], self.dev / line)
      else:
        print("Error: Invalid folder entered: {}".format(folder))
        return
    self.prompt = self.world.name + "> "

  def complete_load(self, text, line, start, end):
    if not text:
      return [(d / "levelname.txt").read_text() for d in self.mcw.iterdir() if d.is_dir()]
    return [(d / "levelname.txt").read_text() for d in self.mcw.iterdir() if d.is_dir() and (d / "levelname.txt").read_text().startswith(text)]


  def do_pack(self, line):
    if line.startswith("new "):
      line = line[4:]
      if line.startswith("rp "):
        i = 0
      elif line.startswith("bp "):
        i = 1
      else:
        print("Error, unknown pack type.")
        return
      line = line[3:]
      name, desc = line.split(" ", 1)
      self.world.generate(name, desc, i)

  def emptyline(self):
    self.world.go(converter.converters)
    print("Done.")

  def do_EOF(self, line):
    print("Exiting")
    return True

def readConfig(file):
  with open(file) as iF:
    contents = iF.read()
  config = {}
  section = None
  for line in contents.splitlines():
    line = line.strip()
    if line == "" or line[0] in "#;":
      continue
    if line.startswith("["):
      section = line[1:-1]
      config[section] = {}
    else:
      k, v = line.split("=", 1)
      k, v = k.strip(), v.strip()
      if k in config[section]:
        config[section][k].append(v)
      else:
        config[section][k] = [v.strip()]
  return config

if __name__ == "__main__":
  config = readConfig("config.ini")

  Air(config).cmdloop()
