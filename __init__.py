import mobase

from .GrassPrecacher import GrassPrecacher

def createPlugin() -> mobase.IPlugin:
    return GrassPrecacher()