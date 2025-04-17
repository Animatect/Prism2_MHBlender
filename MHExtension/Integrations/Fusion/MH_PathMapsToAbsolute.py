import os
import sys
import re
FusionPluginPath = FUSIONROOT
ThirdPartyPath = os.path.join(FusionPluginPath, "Scripts", "thirdparty")
sys.path.append(ThirdPartyPath)

import pyperclip
class MapToPath():
	def __init__(self, fusion):
		self.fusion = fusion

	def getCurrentComp(self):
		return self.fusion.CurrentComp
	
	def CheckSubmittedPaths(self):
		comp = self.getCurrentComp()
		allpathdata = []

		# get Paths
		allpathdata += self.replacePathMapsIOtools(comp)
		# self.replacePathMapsABC(comp)
		# self.replacePathMapsFBX(comp)
		# self.replacePathMapsOCIOCS(comp)
		# self.replacePathMapsLUTFiles(comp)
		all_alembic  = comp.GetToolList(False, "SurfaceAlembicMesh").values()
		allpathdata += self.replacePathMapsbyPattern(
			comp, all_alembic, r'Filename = Input { Value = "(.*?)", },', "Filename"
			)
		
		all_fbx  = comp.GetToolList(False, "SurfaceFBXMesh").values()
		allpathdata += self.replacePathMapsbyPattern(
			comp, all_fbx, r'ImportFile = Input { Value = "(.*?)", },', "ImportFile"
			)
		
		all_OCIO_CS = comp.GetToolList(False, "OCIOColorSpace").values()
		allpathdata += self.replacePathMapsbyPattern(
			comp, all_OCIO_CS, r'OCIOConfig\s*=\s*Input\s*{\s*Value\s*=\s*"([^"]+)"', "OCIOConfig"
			)
		
		all_OCIO_FT = comp.GetToolList(False, "OCIOFileTransform").values()
		all_FileLUT = comp.GetToolList(False, "FileLUT").values()
		luttools = list(all_OCIO_FT) + list(all_FileLUT)
		allpathdata += self.replacePathMapsbyPattern(
			comp, luttools, r'LUTFile = Input { Value = "(.*?)"', "LUTFile"
			)
		
		for pathdata in allpathdata:
			if not pathdata["valid"]:
				print("path: ", pathdata["path"], " in ", pathdata["node"], "does not exists")
			if not pathdata["net"]:
				print("path: ", pathdata["path"], " in ", pathdata["node"], "Is not a NET Path")
			print("path: ", pathdata["path"], " in ", pathdata["node"], "was processed")




	def getReplacedPaths(self, comp, filepath):
		pathmaps = comp.GetCompPathMap(False, False)
		pathexists = False
		isnetworkpath = False
		for k in pathmaps.keys():
			if k in filepath:
				index = filepath.find(k)

				if index != -1:  # Check if substring exists
					# Replace "brown" with "red"
					new_path = filepath[:index] + pathmaps[k] + "/" + filepath[index + len(k):]
					formatted_path = os.path.normpath(new_path)
					# Check if the formatted path exists
					if os.path.exists(formatted_path):
						pathexists = True
					# Check if path is local
					# drive_letter, _  = os.path.splitdrive(formatted_path)
					# drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive_letter)
					# isnetworkpath = drive_type == 4 or formatted_path.startswith("\\\\")
					isnetworkpath = True

					return {"path":formatted_path, "valid":pathexists, "net":isnetworkpath}
		
		return {"path":None, "valid":pathexists, "net":isnetworkpath}


	def replacePathMapsLUTFiles(self, comp):
		oldcopy = pyperclip.paste()
		# Input text		
		all_OCIO_FT = comp.GetToolList(False, "OCIOFileTransform").values()
		all_FileLUT = comp.GetToolList(False, "FileLUT").values()
		luttools = list(all_OCIO_FT) + list(all_FileLUT)

		for tool in luttools:
			comp.Copy(tool)
			text = pyperclip.paste()
			# Define regular expression pattern to match the desired substring
			pattern = r'LUTFile = Input { Value = "(.*?)"'

			# Search for the pattern in the text
			match = re.search(pattern, text)

			# If a match is found, extract the substring after "Value ="
			if match:
				filepath = match.group(1)
				pathinfo = self.getReplacedPaths(comp, filepath)
				newpath = pathinfo["path"]
				if newpath:
					tool.LUTFile = newpath
			else:
				print("Pattern not found in the text.")
		pyperclip.copy(oldcopy)


	def replacePathMapsOCIOCS(self, comp):
		oldcopy = pyperclip.paste()
		# Input text
		all_OCIO_CS = comp.GetToolList(False, "OCIOColorSpace").values()

		for tool in all_OCIO_CS:
			comp.Copy(tool)
			text = pyperclip.paste()
			# Define regular expression pattern to match the desired substring
			pattern = r'OCIOConfig\s*=\s*Input\s*{\s*Value\s*=\s*"([^"]+)"'

			# Search for the pattern in the text
			match = re.search(pattern, text)

			# If a match is found, extract the substring after "Value ="
			if match:
				filepath = match.group(1)
				pathinfo = self.getReplacedPaths(comp, filepath)
				newpath = pathinfo["path"]
				if newpath:
					tool.OCIOConfig = newpath
			else:
				print("Pattern not found in the text.")
		pyperclip.copy(oldcopy)


	def replacePathMapsFBX(self, comp):
		oldcopy = pyperclip.paste()
		# Input text
		all_fbx  = comp.GetToolList(False, "SurfaceFBXMesh").values()

		for tool in all_fbx:
			comp.Copy(tool)
			text = pyperclip.paste()
			# Define regular expression pattern to match the desired substring
			pattern = r'ImportFile = Input { Value = "(.*?)", },'

			# Search for the pattern in the text
			match = re.search(pattern, text)

			# If a match is found, extract the substring after "Value ="
			if match:
				filepath = match.group(1)
				pathinfo = self.getReplacedPaths(comp, filepath)
				newpath = pathinfo["path"]
				tool.ImportFile = newpath
			else:
				print("Pattern not found in the text.")
		pyperclip.copy(oldcopy)


	def replacePathMapsABC(self, comp):
		pathdata = []
		oldcopy = pyperclip.paste()
		# Input text
		all_alembic  = comp.GetToolList(False, "SurfaceAlembicMesh").values()

		for tool in all_alembic:
			comp.Copy(tool)
			text = pyperclip.paste()
			# Define regular expression pattern to match the desired substring
			pattern = r'Filename = Input { Value = "(.*?)", },'

			# Search for the pattern in the text
			match = re.search(pattern, text)

			# If a match is found, extract the substring after "Value ="
			if match:
				filepath = match.group(1)
				pathinfo = self.getReplacedPaths(comp, filepath)
				newpath = pathinfo["path"]
				if newpath:
					tool.Filename = newpath
					pathdata.append({"node": tool.Name, "path":pathinfo["path"], "valid":pathinfo["valid"], "net":pathinfo["net"]})
			
		pyperclip.copy(oldcopy)
		return pathdata


	def replacePathMapsbyPattern(self, comp, tool_list, regexpattern, pathInput):
		pathdata = []
		oldcopy = pyperclip.paste()

		for tool in tool_list:
			comp.Copy(tool)
			text = pyperclip.paste()
			# Define regular expression pattern to match the desired substring
			pattern = regexpattern
			# Search for the pattern in the text
			match = re.search(pattern, text)

			# If a match is found, extract the substring after "Value ="
			if match:
				filepath = match.group(1)
				pathinfo = self.getReplacedPaths(comp, filepath)
				newpath = pathinfo["path"]
				if newpath:
					setattr(tool, pathInput, newpath)
					pathdata.append({"node": tool.Name, "path":pathinfo["path"], "valid":pathinfo["valid"], "net":pathinfo["net"]})
			
		pyperclip.copy(oldcopy)
		return pathdata

	def replacePathMapsIOtools(self, comp):
		pathdata = []
		print("comp: ", comp)
		all_loader = comp.GetToolList(False, "Loader").values()
		all_saver  = comp.GetToolList(False, "Saver").values()
		iotools = list(all_loader) + list(all_saver)
		for tool in iotools:
			filepath = tool.GetAttrs("TOOLST_Clip_Name")[1]
			pathinfo = self.getReplacedPaths(comp, filepath)
			newpath = pathinfo["path"]
			if newpath:
				tool.Clip = newpath			
				pathdata.append({"node": tool.Name, "path":pathinfo["path"], "valid":pathinfo["valid"], "net":pathinfo["net"]})

		return pathdata
	

if __name__ == "__main__":
	# print(fusion.CurrentComp)
	pathReplacer = MapToPath(fusion)
	pathReplacer.CheckSubmittedPaths()