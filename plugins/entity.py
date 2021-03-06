from plugin import command
from .mcjson_convert import enc

@command
def entity(world, name):
  if ":" not in name:
    raise ValueError("Entity name must include namespace.")
  namespace, name = name.split(":", 1)
  rp_entity = {
    "format_version": "1.10.0",
    "minecraft:client_entity": {
      "description": {
        "identifier": "{}:{}".format(namespace, name),
        "materials": {"default": "entity"},
        "textures": {
          "default": "textures/entity/" + name
        },
        "geometry": {
          "default": "geometry." + name
        },
        "spawn_egg": {
          "base_color": "#ffffff",
          "overlay_color": "#000000"
        },
        "render_controllers": [
          "controller.render.generic"
        ]
      }
    }
  }
  (world.devPath / "rp" / "entity").mkdir(exist_ok=True)
  (world.devPath / "rp" / "entity" / "{}.mcj".format(name)).write_text(enc(rp_entity))
  (world.devPath / "rp" / "textures" / "entity").mkdir(exist_ok=True, parents=True)
  (world.devPath / "rp" / "models" / "entity").mkdir(exist_ok=True, parents=True)
  bp_entity = {
    "identifier": "{}:{}".format(namespace, name),
    "components": {
      "collision_box": {
        "width": 1,
        "height": 1
      },
      "health": {
        "value": 1,
        "max": 1
      },
      "pushable": {
        "is_pushable": False,
        "is_pushable_by_piston": False
      },
      "damage_sensor": {
        "triggers": [
          {
            "deals_damage": False
          }
        ]
      },
      "physics": {}
    }
  }
  (world.devPath / "bp" / "entities").mkdir(exist_ok=True)
  (world.devPath / "bp" / "entities" / "{}.mcj".format(name)).write_text(enc(bp_entity))
