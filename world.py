import json
from pathlib import Path
import uuid

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
    self.knownPacks = {}
    if not self.devPath.exists():
      self.create()

  def create(self):
    print("Setting up " + self.name)
    self.devPath.mkdir(parents=True)
    self.createPack(self.name + " Resources", self.packTypes[0])
    self.createPack(self.name + " Behaviors", self.packTypes[1])

  def createPack(self, name, packType):
    self.knownPacks[packType["shortFolder"]] = packType["folder"]

    manifest = {
      "format_version": 2,
      "header": {
        "name": name,
        "description": name,
        "uuid": str(uuid.uuid4()),
        "version": [0, 0, 1],
        "min_engine_version": [1, 14, 0]
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
    if controller.exists():
      packs = json.loads(controller.read_text())
    else:
      packs = []
    packs.append({
      "pack_id": manifest["header"]["uuid"],
      "version": [0, 0, 1]
    })
    controller.write_text(json.dumps(packs, indent=2))

  def getPack(self, pack):
    if pack not in self.knownPacks:
      manifest = (self.devPath / pack / "manifest.mcj").read_text()
      if "type resources" in manifest:
        self.knownPacks[pack] = "resource_packs"
      elif "type data" in manifest:
        self.knownPacks[pack] = "behavior_packs"
      else:
        print(f"Unknown pack type for pack {pack}")
        return None
    return self.knownPacks[pack]

  def file(self, path):
    if not isinstance(path, Path):
      path = Path(path)
    try:
      path = path.relative_to(self.devPath)
      pack = path.parts[0]
      source = self.devPath / pack
      path = path.relative_to(pack)
      dest = self.path / self.getPack(pack) / pack
    except ValueError:
      try:
        path = path.relative_to(self.path)
        packType = path.parts[0]
        pack = path.parts[1]
        source = self.path / packType / pack
        path = path.relative_to(packType, pack)
        dest = self.devPath / pack
      except ValueError:
        print(f"Error: Can't create file for unknown path {path}")
        return None
    return source, path, dest
