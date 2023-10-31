# monsterBuilder
Ideas for a Creature Autorig Tool

Here you can find some initial ideas for a Quadruped Autorig, for Autodesk Maya,  to create a spine/neck/tail setup, you will need to create an EP curve first with just two points your start and end, the input curve requires to be bezier so check the convert radial button.

```
import sys
sys.path.append('tool path here')
import MonsterBuilderUi
reload(MonsterBuilderUi)
mb = MonsterBuilderUi.MonsterBuilderUI()
mb.show(dockable=True, width=250, height=350)
```
