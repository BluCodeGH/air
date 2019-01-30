import json

import pack

class World:
  packTypes = [{
      "controller": "world_resource_packs.json",
      "folder": "resource_packs",
      "dataType": "resources"
    },
    {
      "controller": "world_behavior_packs.json",
      "folder": "behavior_packs",
      "dataType": "behaviors"
    }]
  def __init__(self, path, devPath):
    self.path = path
    self.devPath = devPath
    self.name = (self.path / "levelname.txt").read_text()
    print("Loading {}".format(self.name))
    self.get_packs()
    print("Packs:", str(self.packs)[1:-1])
    print("Loaded")

  def get_packs(self):
    self.packs = []
    for packType in self.packTypes:
      packs = json.loads((self.path / packType["controller"]).read_text())
      for packPath in (self.path / packType["folder"]).iterdir():
        newPack = pack.Pack(packPath, packType["controller"])
        self.packs.append(newPack)

  def generate(self, name, description, packType):
    packType = self.packTypes[packType]
    newPack = pack.generate(self.path, name, description, packType)
    newPack.enable()
    self.packs.append(newPack)
