startFmt = """function quests/{0}/1/enter
tag @s add quest_{0}_1
""" # name
mainFmt = """execute @s[tag=quest_{0}_{1}] ~ ~ ~ function quests/{0}/{1}/tick
execute @s[tag=quest_{0}_{1},tag=quest_{0}_{2}] ~ ~ ~ function quests/{0}/{2}/exit
execute @s[tag=quest_{0}_{1},tag=quest_{0}_{2}] ~ ~ ~ function quests/{0}/{1}/enter
tag @s[tag=quest_{0}_{1},tag=quest_{0}_{2}] remove quest_{0}_{1}
""" # name, number, number + 1
dialogueInitFmt = """scoreboard players set @e[{0}] dialogueState 0
scoreboard players set @e[{0}] dialogueTime 1
""" # selector
dialogueTickFmt = """scoreboard players remove @e[{0},scores={{dialogueTime=0..}}] dialogueTime 1
scoreboard players add @e[{0},scores={{dialogueTime=0}}] dialogueState 1
""" # selector
dialogueInteractFmt = """execute @e[{0}] ~ ~ ~ execute @e[type=silverfish,r=1] ~ ~ ~ function quests/{1}/{2}/interact
""" # selector, name, number
dialogueFmtMain = """execute @e[{0},scores={{dialogueState={1},dialogueTime=0}}] ~ ~ ~ {2}
""" # selector, number, command
dialogueFmtNext = """scoreboard players set @e[{0},scores={{dialogueState={1},dialogueTime=0}}] dialogueTime {2}
""" # selector, number, duration
dialogueFmtCmd = """tellraw @a {{"rawtext":[{{"text":"{0}"}}]}}"""
killFmt = """teleport @e[type=silverfish] ~ -30 ~
kill @e[type=silverfish]"""


def convert(_, root, realRoot):
  i = 1
  name = root.name
  root = "functions" / root
  res = {root / "main.mcfunction": "", root / "init.mcfunction": startFmt.format(name)}
  while True:
    path = root / str(i)
    realPath = realRoot / str(i)
    if not realPath.is_dir():
      break
    res[root / "main.mcfunction"] += mainFmt.format(name, i, i + 1)
    res[path / "enter.mcfunction"] = ""
    res[path / "tick.mcfunction"] = ""
    dialogue = realPath / "dialogue.txt"
    if dialogue.is_file():
      dialogue = dialogue.read_text()
      selector, dialogue = dialogue.split("\n", 1)
      res[path / "enter.mcfunction"] += dialogueInitFmt.format(selector)
      res[path / "tick.mcfunction"] += dialogueTickFmt.format(selector)
      lineNum = 1
      for line in dialogue.splitlines():
        if line.startswith("!"):
          res[path / "tick.mcfunction"] += dialogueFmtMain.format(selector, lineNum, line[1:].strip())
        elif line.strip() != "":
          time, line = line.split(" ", 1)
          res[path / "tick.mcfunction"] += dialogueFmtMain.format(selector, lineNum, dialogueFmtCmd.format(line))
          res[path / "tick.mcfunction"] += dialogueFmtNext.format(selector, lineNum, time)
          lineNum += 1
      if (realPath / "interact.mcfunction").is_file():
        res[path / "tick.mcfunction"] += dialogueInteractFmt.format(selector, name, i)
        res[path / "interact.mcfunction"] = (realPath / "interact.mcfunction").read_text()
    if (realPath / "enter.mcfunction").is_file():
      res[path / "enter.mcfunction"] += (realPath / "enter.mcfunction").read_text()
    if (realPath / "tick.mcfunction").is_file():
      res[path / "tick.mcfunction"] += (realPath / "tick.mcfunction").read_text()
    if (realPath / "exit.mcfunction").is_file():
      res[path / "exit.mcfunction"] = (realPath / "exit.mcfunction").read_text()
    i += 1
  res[root / "main.mcfunction"] += killFmt
  return res


globs = [ "quests/*/" ]
