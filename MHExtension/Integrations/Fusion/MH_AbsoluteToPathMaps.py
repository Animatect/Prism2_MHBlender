import os
import sys

def getPrismRoot():
	prismRoot = os.getenv("PRISM_ROOT")
	if not prismRoot:
		prismRoot = "C:/Program Files/Prism2"
	return prismRoot
prismRoot = getPrismRoot()
scriptDir = os.path.join(prismRoot, "Scripts")
pysideDir = os.path.join(prismRoot, "PythonLibs", "Python3", "PySide")
sys.path.append(pysideDir)

if scriptDir not in sys.path:
	sys.path.append(scriptDir)

if pysideDir not in sys.path:
	sys.path.append(pysideDir)


import PrismCore

def prismInit():
	pcore = PrismCore.create(app="Standalone", prismArgs=["noUI", "loadProject"])

	return pcore

core = prismInit()

print(core.getUserPrefConfigPath())