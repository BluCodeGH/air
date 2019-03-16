import uuid
import json

class World:
  packTypes = [{
      "controller": "world_resource_packs.json",
      "folder": "resource_packs",
      "shortFolder": "rp",
      "dataType": "resources"
    },
    {
      "controller": "world_behavior_packs.json",
      "folder": "behavior_packs",
      "shortFolder": "bp",
      "dataType": "data"
    }]
  def __init__(self, path, devPath):
    self.path = path
    self.name = (self.path / "levelname.txt").read_text()
    self.devPath = devPath / self.name
    if not self.devPath.exists():
      self.create()

  def create(self):
    self.devPath.mkdir(parents=True)
    self.createPack(self.name + " Resources", self.packTypes[0])
    self.createPack(self.name + " Behaviors", self.packTypes[1])

  def createPack(self, name, packType):
    manifest = {
      "format_version": 1,
      "header": {
        "name": name,
        "description": name,
        "uuid": str(uuid.uuid4()),
        "version": [0, 0, 1],
        "min_engine_version": [1, 9, 0]
      },
      "modules": [
        {
          "type": packType["dataType"],
          "uuid": str(uuid.uuid4()),
          "version": [0, 0, 1]
        }
      ]
    }
    (self.devPath / packType["shortFolder"]).mkdir()

    path = self.path / packType["folder"] / packType["shortFolder"]
    path.mkdir(parents=True)
    (path / "manifest.json").write_text(json.dumps(manifest, indent=2))

    controller = self.path / packType["controller"]
    packs = json.loads(controller.read_text()) or []
    packs.append({
      "pack_id": manifest["header"]["uuid"],
      "version": [0, 0, 1]
    })
    controller.write_text(json.dumps(packs, indent=2))

  def go(self, converters):
    for converter in converters:
      converter.go(self.devPath / "rp", self.path / "resource_packs" / "rp")
      converter.go(self.devPath / "bp", self.path / "behavior_packs" / "bp")
