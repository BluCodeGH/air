import collections
import importlib
import inspect
import pathlib

def command(fn):
  sig = inspect.signature(fn)
  parameters = collections.OrderedDict(sig.parameters)
  if parameters.popitem(False)[0] not in ["world", "_"]:
    raise ValueError("Command {} does not take 'world' as first parameter.".format(fn.__name__))

  def handle(world, args):
    i = 0
    n = 0
    params = {k: None for k in parameters.keys()}
    while i < len(args):
      arg = args[i]
      if not arg.startswith("-"):
        name = list(parameters.keys())[n]
        if n == -1:
          raise ValueError("Unnamed arguments must go before named ones.")
        param = parameters[name]
        if param.kind != inspect.Parameter.VAR_POSITIONAL:
          params[name] = arg
          n += 1
        elif params[name] is None:
          params[name] = [arg]
        else:
          params[name].append(arg)
      elif arg.strip("-") in parameters.keys():
        n = -1
        name = arg.strip("-")
        if params[name] is not None:
          raise KeyError("Argument {} already specified.".format(name))
        if args[i + 1].startswith("-"):
          params[name] = True
        else:
          params[name] = args[i + 1]
          i += 1
      else:
        raise KeyError("Unknown named argument {}".format(arg.strip("-")))
      i += 1
    for name in list(params):
      val = params[name]
      if val is None and parameters[name].default == inspect.Parameter.empty:
        raise KeyError("Argument {} must be specified.".format(name))
      if val is None:
        params.pop(name)
    return fn(world, **params)

  if fn.__name__ in commands:
    raise ValueError("Duplucate command name {}".format(fn.__name__))
  commands[fn.__name__] = handle
  return fn

commands = {}
def load():
  for file in pathlib.Path("plugins").glob("*.py"):
    print("Loading plugin {}".format(file.stem))
    importlib.import_module("plugins.{}".format(file.stem))

def parse(world, cmd):
  cmd, *args = [t.strip() for t in cmd.split()]
  if cmd in commands:
    return commands[cmd](world, args)
  raise KeyError("Command {} not found.".format(cmd))
