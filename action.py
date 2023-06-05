import subprocess
import os 
import shlex

def parse(command, prefix = ""):
	command = prefix + " " + command
	return shlex.split(command)
	
class Action:

	@staticmethod 	
	def run(command):
		report = dict()
		try:
			print("Running command.. ", command)
			parsed_command = parse(command)
			output = None
			if ">" in command or "|" in command:
				subprocess.run(command, shell=True)
				report["success"] = True
				report["output"] = "shell command ran successfully" 
				return report 
			else:
				output = subprocess.run(parsed_command, capture_output=True, text=True)
			
			if output.stderr != "":
				raise Exception("Task failed with error : %s"%(output.stderr))
			report["success"] = True
			report["output"] = output.stdout
		except Exception as e:
			report["success"] = False
			report["error"] = str(e)
		return report 
	
	@staticmethod 	
	def read(path):
		report = dict()
		print("Reading from file at..", path)
		try:
			with open(path, 'r') as file:
				output = file.read()
				report["output"] = output
				report["success"] = True
		except Exception as e:
			report["success"] = False
			report["error"] = str(e)

		return report 

	@staticmethod
	def write(path, content):
		report = dict()
		print("Writing to file at..", path)
		try:
			with open(path, 'w') as file:
				file.write(content)
			report["output"] = "written successfully"
			report["success"] = True
		except Exception as e:
			report["success"] = False
			report["error"] = str(e)
		return report 

	@staticmethod
	def navigate(path):
		report = dict()
		print("Navigating to...", path)
		try:
			os.chdir(path)	
			report["output"] = "navigated successfully"
			report["success"] = True
		except Exception as e:
			report["success"] = False
			report["error"] = str(e)
		return report 


