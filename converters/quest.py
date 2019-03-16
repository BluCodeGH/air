initQuest = """function quests/{0}/1/enter
tag @s add quest_{0}_1
""" # name
questStage = """execute @s[tag=quest_{0}_{1}] ~ ~ ~ function quests/{0}/{1}/main
execute @s[tag=quest_{0}_{1},tag=quest_{0}_{2}] ~ ~ ~ function quests/{0}/{1}/exit
execute @s[tag=quest_{0}_{1},tag=quest_{0}_{2}] ~ ~ ~ function quests/{0}/{2}/enter
tag @s[tag=quest_{0}_{1},tag=quest_{0}_{2}] remove quest_{0}_{1}
""" # name, number, number + 1

questStageDialogueInit = """scoreboard players set @e[{0}] dialogueState 0
scoreboard players set @e[{0}] dialogueTime 1
""" # selector
questStageDialogueTick = """scoreboard players remove @e[{0},scores={{dialogueTime=0..}}] dialogueTime 1
scoreboard players add @e[{0},scores={{dialogueTime=0}}] dialogueState 1
""" # selector
questStageDialogueInteract = """execute @e[{0}] ~ ~ ~ execute @e[type=silverfish,r=1] ~ ~ ~ execute @e[tag=questState] ~ ~ ~ function quests/{1}/{2}/interact
""" # selector, name, number

dialogueStageCommand = """execute @s[scores={{dialogueState={0},dialogueTime=0}}] ~ ~ ~ {1}
""" # snumber, command
dialogueStageTiming = """scoreboard players set @s[scores={{dialogueState={0},dialogueTime=0}}] dialogueTime {1}
""" # number, duration
dialogueStageTellraw = """tellraw @a {{"rawtext":[{{"text":"{0}"}}]}}"""

dialogueMain = """execute @e[{0},scores={{dialogueState=..{1}}}] ~ ~ ~ function quests/{2}/{3}/dialogue
execute @e[{0},scores={{dialogueState={4}}}] ~ ~ ~ execute @e[tag=questState] ~ ~ ~ function quests/{2}/{3}/tick
""" # selector, number - 1, questname, queststage, number
noDialogueMain = """function quests/{0}/{1}/tick
"""

questReset = """scoreboard players reset @s *
"""
questStageReset = """tag @s remove quest_{}_{}
""" # name, number

def folderConvert(realRoot, root):
  i = 1
  name = root.name
  root = "functions" / root
  res = {root / "main.mcfunction": "",
    root / "init.mcfunction": initQuest.format(name),
    root / "reset.mcfunction": questReset}
  while True:
    path = root / str(i)
    realPath = realRoot / str(i)
    if not realPath.is_dir():
      break
    res[root / "main.mcfunction"] += questStage.format(name, i, i + 1)
    res[root / "reset.mcfunction"] += questStageReset.format(name, i)
    res[path / "enter.mcfunction"] = ""
    res[path / "tick.mcfunction"] = ""
    dialogue = realPath / "dialogue.txt"
    if dialogue.is_file():
      dialogue = dialogue.read_text()
      selector, dialogue = dialogue.split("\n", 1)
      res[path / "enter.mcfunction"] += questStageDialogueInit.format(selector)
      res[path / "dialogue.mcfunction"] = questStageDialogueTick.format(selector)
      lineNum = 1
      for line in dialogue.splitlines():
        if line.startswith("!"):
          res[path / "dialogue.mcfunction"] += dialogueStageCommand.format(lineNum, line[1:].strip())
        elif line.strip() != "":
          time, line = line.split(" ", 1)
          time = int(float(time) * 20)
          res[path / "dialogue.mcfunction"] += dialogueStageCommand.format(lineNum, dialogueStageTellraw.format(line))
          res[path / "dialogue.mcfunction"] += dialogueStageTiming.format(lineNum, time)
          lineNum += 1
      res[path / "main.mcfunction"] = dialogueMain.format(selector, lineNum - 1, name, i, lineNum)
      if (realPath / "interact.mcfunction").is_file():
        res[path / "tick.mcfunction"] = questStageDialogueInteract.format(selector, name, i)
        res[path / "interact.mcfunction"] = (realPath / "interact.mcfunction").read_text()
    else:
      res[path/ "main.mcfunction"] = noDialogueMain.format(name, i)
    if (realPath / "enter.mcfunction").is_file():
      res[path / "enter.mcfunction"] = (realPath / "enter.mcfunction").read_text() + "\n" + res[path / "enter.mcfunction"]
    if (realPath / "tick.mcfunction").is_file():
      res[path / "tick.mcfunction"] += (realPath / "tick.mcfunction").read_text()
    if (realPath / "exit.mcfunction").is_file():
      res[path / "exit.mcfunction"] = (realPath / "exit.mcfunction").read_text()
    i += 1
  return res


patterns = ["quests/*/"]
