import json
import uuid

class Pack:
  def __init__(self, path, controller):
    self.path = path
    self.controller = controller
    self.manifest = json.loads((path / "manifest.json").read_text())
    self.name = self.manifest["header"]["name"]
    self.uuid = self.manifest["header"]["uuid"]
    self.version = self.manifest["header"]["version"]

  def enable(self):
    packs = json.loads(self.controller.read_text())
    for pack in packs:
      if pack["uuid"] == self.uuid:
        pack["version"] = self.version
        break
    else:
      packs.append({
        "uuid": self.uuid,
        "version": self.version
      })
    self.controller.write_text(json.dumps(packs, indent=2))

  def disable(self):
    packs = json.loads(self.controller.read_text())
    packs = [pack for pack in path if pack["uuid"] != self.uuid]
    self.controller.write_text(json.dumps(packs, indent=2))

  def __repr__(self):
    return self.name

def generate(worldPath, name, description, packType):
  manifest = {
    "format_version": 1,
    "header": {
      "name": name,
      "description": description,
      "uuid": str(uuid.uuid4()),
      "version": [ 0, 0, 1 ]
    },
    "modules": [
      {
        "description": "_",
        "type": packType["dataType"],
        "uuid": str(uuid.uuid4()),
        "version": [ 0, 0, 1 ]
      }
    ]
  }
  path = worldPath / packType["folder"] / name
  path.mkdir()
  (path / "manifest.json").write_text(json.dumps(manifest, indent=2))
  return Pack(path, worldPath / packType["controller"])
