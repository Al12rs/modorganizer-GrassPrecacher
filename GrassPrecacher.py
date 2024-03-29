import mobase
import os

from typing import List
from pathlib import Path

try:
    from PyQt5.QtCore import QDir
    from PyQt5.QtGui import QIcon
    #from PyQt5 import QMainWindow, QWidget, QMessageBox
    from PyQt5 import QtWidgets
except:
    from PyQt6.QtCore import QDir
    from PyQt6.QtGui import QIcon
    from PyQt6 import QtWidgets

class GrassPrecacher(mobase.IPluginTool):

    _organizer: mobase.IOrganizer
    _mainWindow: QtWidgets.QMainWindow
    _parentWidget: QtWidgets.QWidget

    def __init__(self):
        super().__init__()

    def init(self, organizer: mobase.IOrganizer):
        self._organizer = organizer
        return True

    def name(self) -> str:
        return "GrassPrecacher"

    def author(self) -> str:
        return "AL"

    def description(self) -> str:
        return "Automatically restarts the game if it crashed on close (only works for meh321 PrecacheGrass mod)"

    def version(self) -> mobase.VersionInfo:
        return mobase.VersionInfo(1, 1, 0, mobase.ReleaseType.FINAL)

    def isActive(self) -> bool:
        return self._organizer.pluginSetting(self.name(), "enabled") is True

    def settings(self) -> List[mobase.PluginSetting]:
        return [
            mobase.PluginSetting("enabled", "enable this plugin", True)
        ]
    
    def displayName(self):
        return "Precache Grass "
    
    def tooltip(self):
        return "Runs the game in a loop while PrecacheGrass.txt exists in the game folder."
    
    def icon(self):
        return QIcon()

    def setParentWidget(self, widget:QtWidgets.QWidget):
        self._parentWidget = widget
    
    def _isGrassPluginPresent(self) -> bool:
        grassPluginPath = "NetScriptFramework/Plugins/"
        grassPlugin = "*GrassControl.dll"
        result = self._organizer.findFiles(grassPluginPath, grassPlugin)
        if result:
            return True
        else:
            return False

    def display(self):
        # When you press the option in the tools menu:
        if not self._isGrassPluginPresent():
            QtWidgets.QMessageBox.critical(self._parentWidget,"GrassControl plugin is missing", "\"No Grass In Object\" mod not found. Please install the mod and refresh MO2.")
            return
        if QtWidgets.QMessageBox.warning(self._parentWidget,"Start Grass Precaching?", 
"""This operation can take a long time (1hour+).
 
The game is expected to crash multiple times during the operation, MO2 will restart it automatically until it's complete.""",
                 QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.Abort) == QtWidgets.QMessageBox.StandardButton.Yes.value :
            gameFolder : QDir = self._organizer.managedGame().gameDirectory()
            cacheFile = gameFolder.absoluteFilePath("PrecacheGrass.txt")
            # Create PrecacheGrass.txt in game folder
            Path(cacheFile).touch()
            self._startGame_and_wait()

    
    def _startGame_and_wait(self):
        gameFolder : QDir = self._organizer.managedGame().gameDirectory()
        sksePath = gameFolder.absoluteFilePath("skse64_loader.exe")

        appHandle = self._organizer.startApplication(sksePath, ["-forcesteamloader"])

        if  appHandle == 0:
            QtWidgets.QMessageBox.critical(self._parentWidget,"Grass Precaching Error", "MO2 failed to restart the game, aborting Grass Precaching")
            cacheFile = gameFolder.absoluteFilePath("PrecacheGrass.txt")
            os.remove(cacheFile)
        else :
            #Application started successfully, wait until completion
            self._organizer.waitForApplication(appHandle)
            # Application was closed or crashed
            self._tryRestart() 


    def _tryRestart(self):
        gameFolder : QDir = self._organizer.managedGame().gameDirectory()
        cacheFile = gameFolder.absoluteFilePath("PrecacheGrass.txt")

        # check for PrecacheGrass.txt
        if os.path.exists(cacheFile) :
            # PrecacheGrass.txt exists so we restart if user doesn't abort in 8 seconds.

            timedBox = QtWidgets.QMessageBox(self._parentWidget)
            timedBox.setWindowTitle("Restarting Game...") 
            timedBox.setText("""Grass Precacheing isn't finished yet, Mo2 will try restart the game automatically in 8 seconds... 
(The game is expected to crash multiple times during this operation, so this is normal).""")
            timedBox.addButton(QtWidgets.QMessageBox.StandardButton.Ok)
            timedBox.addButton(QtWidgets.QMessageBox.StandardButton.Abort)
            okButton = timedBox.button(QtWidgets.QMessageBox.StandardButton.Ok)
            timedBox.button(QtWidgets.QMessageBox.StandardButton.Ok).animateClick(8000)
            timedBox.exec()

            if timedBox.clickedButton() == okButton :
                #continue loop
                self._startGame_and_wait()
            else:
                #stop loop
                os.remove(cacheFile)
                QtWidgets.QMessageBox.warning(self._parentWidget,"Grass Precaching Aborted", "The grass precaching operation was terminated before being completed.")
        else:
            # The game terminated and the file is missing, assume operation completed successfully
            QtWidgets.QMessageBox.information(self._parentWidget, "Grass precaching completed.",
                """ The grass caching operation was completed successfully.""", QtWidgets.QMessageBox.StandardButton.Ok)
