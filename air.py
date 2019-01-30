import configparser
import pathlib
import cmd

from world import World


class Air(cmd.Cmd):
  def __init__(self, config):
    self.prompt = "> "
    self.config = config
    self.mcw = pathlib.Path(config["main"]["minecraftWorlds"]).expanduser().resolve()
    self.dev = pathlib.Path(config["main"]["dev"]).expanduser().resolve()
    self.world = None
    super().__init__()


  def do_load(self, line):
    results = [d for d in self.mcw.iterdir() if d.is_dir() and (d / "levelname.txt").read_text() == line]
    if len(results) == 0:
      print("Error: Could not find a world called {}".format(line))
      return
    if len(results) == 1:
      self.world = World(results[0], self.dev)
    else:
      print("Warning: There are multiple worlds named {}".format(line))
      folder = input("Choose a folder out of {}: ".format(", ".join([r.name for r in results])))
      if folder in [r.name for r in results]:
        self.world = World([r for r in results if r.name == folder][0], self.dev)
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

  def do_EOF(self, line):
    print("Exiting")
    return True


if __name__ == "__main__":
  config = configparser.ConfigParser()
  config.read("config.ini")

  Air(config).cmdloop()
