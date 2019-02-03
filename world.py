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
      "dataType": "client_data"
    }]
  def __init__(self, path, devPath):
    self.path = path
    self.devPath = devPath
    self.name = (self.path / "levelname.txt").read_text()
    print("Loading {}".format(self.name))
    self.get_packs()
    print("Packs: ", str(self.packs)[1:-1])
    print("Loaded")

  def get_packs(self):
    self.packs = []
    for packType in self.packTypes:
      for packPath in (self.path / packType["folder"]).iterdir():
        newPack = pack.Pack(packPath, self.devPath, packType["controller"])
        self.packs.append(newPack)

  def generate(self, name, description, packType):
    packType = self.packTypes[packType]
    newPack = pack.generate(self.path, self.devPath, name, description, packType)
    newPack.enable()
    self.packs.append(newPack)

  def go(self, converters):
    for pack in self.packs:
      pack.go(converters)
