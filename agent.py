#!/usr/bin/env python3
import os
import openai
import sys
import ast 
import shlex
import time 
import json 
from action import Action 
from client import LLM  
from prompts import construct_prompt 

steps_so_far = []
goal = ""
discarded_tasks = list()

def strip(string):
	start_index = string.find('{')
	end_index = string.rfind('}')

	if start_index != -1 and end_index != -1:
		stripped_string = string[start_index:end_index+1].strip()
		return stripped_string
	return string 

def main(prefix="", reduce_context = False):
	
	while(True):

		final_prompt = construct_prompt(prefix, reduce_context, goal, discarded_tasks, steps_so_far)
		user_input = input("comments>")
		
		if len(user_input) > 2 and user_input[-1] == "?":
			user_input += "respond in the correct format using type 'info'" 
		res = LLM.getResponse(final_prompt + "\n" + user_input)

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
			print(str(e))
			print("Response not in correct format; requesting response again") 
			return main("Please don't add extra words in your response. \n Only write responses in the format requested. Your last response: %s"%(res))

def handleTask(task): 
	if task['type'] == "info":
		print("\n" + task['content'])
		return
		
	report = dict() 

	if task['type'] == 'run':
		report = Action.run(task['params']['command'])
	elif task['type'] == 'write':
		report = Action.write(task['params']['path'], task['params']['content']);
	elif task['type'] == 'read':
		report = Action.read(task['params']['path'])
	elif task['type'] == 'navigate':
		report = Action.navigate(task['params']['path'])	

	if report["success"] == False:
		prompt = '''Your last task failed. 
		task: %s, 
		error: %s

		Please fix this error as your next task
		Try to gather more information by running commands or reading files to 
		make sure you guess for the root cause is correct.
''' % (str(task), report["error"]) 

		print("Task failed, ", report) 
		steps_so_far.append({'task': task, 'task_execution_report': report}) 
		return main(prompt)

	print("Tasks completed successfully, report: ", report)
	steps_so_far.append({'task': task, 'task_execution_report': report}) 

if __name__ == '__main__':
	while(True):
		goal = input("New goal: ") 
		main()	
		print("Goal completed!") 
			
