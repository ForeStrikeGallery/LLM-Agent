#!/usr/bin/env python3
import os
import openai
import sys
import ast 
import shlex
import time 
import subprocess

openai.organization = "org-rpFAIRUIBdByWr2P89N0MRmO"
openai.api_key = "<your api key>"

def getResponse(prompt, system_msg = "you are a helpful assistant"):
	
	messages = [
			{"role": "system", "content": system_msg},	
			{"role": "user", "content": prompt}
		]
	
	try:  
		response = openai.ChatCompletion.create(
			model= 'gpt-3.5-turbo-0301',
			messages = messages
		)
	except Exception as e:
		if "This model's maximum context length is 4097 tokens" in str(e):
			return "Max context length reached" 
		print("Error while fetching API response, waiting for 5 seconds: %s"%(str(e)))
		time.sleep(5)
		return getResponse(prompt)

	result = response["choices"][0]["message"]["content"] 
	return  result

response_format_prompt = '''Respond only in the format given below, don't add any extra text. If any extra text is present in your response,
	the answer won't be parsable by the user, so always respond only in the format. This is crucial.  

	The format is a python dictionary, like this: {'type': 'write', 'params': {'path': 'path/to/file', 'content': 'content'}, 'reason': '<reason for the task>'}
	The dictionary represents a task 
	There are six different values for `type`. It can be 'write', 'read', 'run', 'finished', 'info', or 'navigate'
	
	for 'write', there should be two fields in the 'params' dictionary, which are 'path', that file to which you have to write
	and 'content', the text content that has to be written

	for 'read', there should be one field in the 'params' dictionary, which is 'path', the file that has to be read
	for e.g. {'type': 'read', 'params': {'path': 'path/to/file'}}

	if you want to navigate to a particular directory, the format is 
	{'type': 'navigate', 'params': {'path':'path/to/directory'}}

	for 'run', there should be one field in the 'params' dictionary, which is 'command', which is the shell command that has 
	to be run, for e.g. 	
	{'type': 'run', 'params': {'command': 'git log'}
	NOTE: DO NOT use "&&" in your command. If multiple commands have to be run, do them in subsequent tasks. Don't use '&&' to combine commands

	In addition to all the above mentioned field, every task should have a "reason" field at the top level, which
	describes in not more than 3 sentences, why this task was chosen as the current task. 
	
	output only ONE such task, one of type write, read, or run. And this task is the NEXT task that to be performed. 
	the purpose of the task is to get enough information for the next task, so this might require reading files or 
	running some commands to look at outputs. 

	NOTE: Before coming up next tasks, check the previous tasks that are finished If no other tasks are remaining for the goal, just return {'type': 'finished'} WITHOUT any other text preceding or succeeding it. I REPEAT, CHECK THE LIST OF FINISHED TASK TO SEE IF ANYTHING MORE HAS TO BE DONE BEFORE SUGGESTING THE NEXT TASK

	You shall NOT use pdb to debug. 
	You shall NOT install any new packages or tools 

     NOTE: Before coming up with the next task, confirm that the next task is not already executed. If it's executed, DO NOT repeat it. If repeating is necessary for some reason, CLEARLY explain why in the "reason" field. 

	If the last line of this prompt is a question (that ends with "?") then, respond in the following format
	{'type': 'info', 'content': '<your response>'}. This is not considered as a task. 

	DO NOT write your response as free text. Only send response in the requested format.
'''	

steps_so_far = []
goal = ""

# not in use 
def verify(res):

	completed_tasks = "\n".join([str(s) for s in steps_so_far])
	prompt = '''check if this current task is the correct next step for the goal, given all the tasks done so far.

		current task: %s,
		goal: %s,
		previous tasks: %s

		Carefully check previous tasks to make sure the current task neither (1) done previously nor (2) is an incorrect next step; for e.g. there might be some task to be done before the current task 

		If it's the correct next step, respond with 'Yes, the given task is correct <the reason>' else say 'No, the given task is incorrect <the reason>'

		If the next step is NOT correct, suggest what *should be* the next step 

		Repond exactly in the above format. DO NOT add preceding or succeeding extra words. 
	
		''' % (res, goal, str(completed_tasks))

	result = getResponse(prompt)

	if result[:2] == "No":
		verifier_suggestion = ''' 
			task: %s,
			checker response: %s

			Based on this feedback, please repond with the correct next task
		'''% (res, result)
		task = ast.literal_eval(res)
		steps_so_far.append({'task': task, 'task_execution_report': {'success':False, 'error': 'verifier stopped task from executing. Reason: %s'%(result)}})
		main(verifier_suggestion)
		return 

# not in use 
def checkIfDone():
		
	prompt = '''check if the goal is accomplished given the list of tasks done so far.

			goal: %s,
			tasks done so far: %s

			if it's finished, respond with "yes", else, respond with "no"
		'''	% (goal, str(steps_so_far))

	result = getResponse(prompt)
	return result


def parse(command, prefix = ""):
	command = prefix + " " + command
	return shlex.split(command)	

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



def lastTaskRepeating(res):
	res = ast.literal_eval(res)
	
	if len(steps_so_far) > 0: 	
		print("lastTaskRepeatingCheck", res["params"], steps_so_far[-1]['task']["params"])

	return len(steps_so_far) > 0 and res["params"] == steps_so_far[-1]['task']["params"]
	

def strip(string):
	start_index = string.find('{')
	end_index = string.rfind('}')

	if start_index != -1 and end_index != -1:
		stripped_string = string[start_index:end_index+1].strip()
		return stripped_string
	return string 

discarded_tasks = list()

def construct_prompt(prefix, reduce_context): 
	completed_tasks = [str(s) for s in steps_so_far]
	if len(completed_tasks) > 5:
		completed_tasks = completed_tasks[-5:]

	if reduce_context:
		completed_tasks = completed_tasks[1:]

	completed_tasks = "\n\n".join(completed_tasks)
	last_discareded_tasks = "\n\n".join(discarded_tasks[-3:] if len(discarded_tasks) > 3 else discarded_tasks)	

	main_prompt = '''
		you are an AI agent, your goal is to break down goals and execute them. You can do one of four things
		you can either read a file, write to a file, or run a command on linux, or navigate to a directory. 
		You can do each of them as many times 
		as you want. Your job is to convert any given goal into a series of steps of the given three type. 

		You have to do these tasks one at a time. For the goal that's presented below, find the immediate next step
		
		Here are the last 5 task you've done: %s
		If some previous steps are missing, and you're unsure whether they're done, 
		you can assume it was completed. DO NOT do those tasks again.  

		you are performing your goal as part of larger goal, which is: %s	
		It was broken down into a series of goals, like this: \n%s

		NOTE: Here is current goal you're pursuing: %s
		your current goal is one among the series of goals mentioned above 
		once the current goal is finished, respond with {"type":"finished"}
		if you think the current goal is already accomplished, directly respond with {"type":"finished"}

		here is a summary of the things you've accomplished so far: %s

		Here are the last 3 discarded tasks which were never executed, along with the user comments %s

''' % (str(completed_tasks), mega_goal, all_goals, goal[2:], context, last_discareded_tasks) 
	last_task = ""

	if (len(steps_so_far) > 0):	
		result = steps_so_far[-1]['task_execution_report']['output'] if steps_so_far[-1]['task_execution_report']['success'] else steps_so_far[-1]['task_execution_report']['error']
		last_task = "Last task results: \ntask: %s,\noutput/error: %s,\nsuccess: %s" % (steps_so_far[-1]['task'], result,  steps_so_far[-1]['task_execution_report']['success'])

	return prefix + main_prompt + response_format_prompt + last_task + "\n If you think the 'current goal' you're pursuing is already accomplished, respond directly with {'task': 'finished'}\n"
	

def main(prefix="", reduce_context = False):
	
	while(True):

		final_prompt = construct_prompt(prefix, reduce_context)
		user_input = input("comments>")
		
		if len(user_input) > 2 and user_input[-1] == "?":
			user_input += "respond in the correct format using type 'info'" 
		res = getResponse(final_prompt + "\n" + user_input)

		if res == "Max context length reached":
			print("Max context length reached, retrying with a lower number of completed tasks in prompt")
			return main(user_input, True)
 
		print("------------------------------------------\nNext Task (from GPT): ", res) 
		
		if "{'type': 'finished'}" in res: 
				print("Goal accomplished successfully: %s, \nMoving onto next one..." % (goal))
				return 

		res = strip(res)
		user_comment = input("User Comment (leave blank if approved)")

		if user_comment == "skip":
			continue 	

		if user_comment != "":
			discarded_tasks.append(res + "\n user comment: %s" % (user_comment))			
			return main("The last task was declined by user with this commment %s" % (user_comment))			

		try: 	
			task = ast.literal_eval(res)
			handleTask(task)
		except Exception as e:
			print("Response not in correct format; requesting response again") 
			return main("Please don't add extra words in your response. Only write responses in the format requested. Your last response: %s"%(res))

def handleTask(task): 
	if task['type'] == "info":
		print("\n" + task['content'])
		return main() 
		
	report = dict() 

	if task['type'] == 'run':
		report = run(task['params']['command'])
	elif task['type'] == 'write':
		report = write(task['params']['path'], task['params']['content']);
	elif task['type'] == 'read':
		report = read(task['params']['path'])
	elif task['type'] == 'navigate':
		report = navigate(task['params']['path'])	

	if report["success"] == False:
		prompt = '''Your last task failed. 
		task: %s, 
		error: %s

		Please fix this error as your next task
		Try to gather more information by running commands or reading files to 
		make sure you guess for the root cause is correct.

		''' % (res, report["error"]) 

		print("Task failed, ", report) 
		steps_so_far.append({'task': task, 'task_execution_report': report}) 
		return main(prompt)

	print("Tasks completed successfully, report: ", report)
	steps_so_far.append({'task': task, 'task_execution_report': report}) 


prev_goals = list()
all_goals = ""
context = ""
mega_goal = "" 

def getContext(steps_so_far):

	if len(steps_so_far) == 0:
		return "No tasks were previously done" 

	result = getResponse("Based on these steps for the previous goal, and the summary of all the work done until then, give a short summary of all that was done, but DO NOT leave out important details like filenames or pathnames, they might be necessary to know for future tasks\n steps for previous goal %s\n summary until now %s" + str(steps_so_far))
	if result  == "Max context length reached":
		print("Too many tasks done, and the context length is exeeding. Removing a task to fit in context length for summary calculation")
		return getContext(steps_so_far[1:])
	return result  

if __name__ == '__main__':
	while(True):
		prev_goals.append(goal)	
		goal = input("new goal> ")
		mega_goal = goal 
		goal_split_prompt = '''
		Break this goal down into a short (max 3) list of numbered instructions for an AI Bot

		The bot can do only one of 4 things. It can READ a file, it can NAVIGATE
		to a directory, it can WRITE anything to a file, or it can RUN a command. 

		Every instructions must have ATLEAST one of these four: READ, WRITE, NAVIGATE, or RUN. Do not lose any important information from the goal.

		IMPORTANT: If the instruction has a READ in it, it *must* also WRITE in the same instruction. 	
		
		For e.g.: "READ from file" is a wrong instruction. It should always be "READ from file at /path/to/file and WRITE result to /path/to/other/file"
		IMPORTANT: Do NOT mention anything other than the numbered list of goals
		here's the goal to break down %s

		Keep each instruction in a SINGLE line.
''' % (goal)
		all_goals = getResponse(goal_split_prompt) 	
		print(all_goals)
		
		for cur_goal in all_goals.strip().split("\n"):
			context = getContext(steps_so_far)
			discarded_tasks = list()
			goal = cur_goal
			print("\n Now pursuing: %s\n" % (goal))
			main(cur_goal, context)

		print("All goals completed!") 
			
