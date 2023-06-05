
response_format_prompt = '''
	Respond only in the format given below, don't add any extra text. If any extra text is present in your response,
	the answer won't be parsable by the user, so always respond only in the format. This is crucial.  

	The format is a python dictionary, like this: 
	{'type': 'write', 'params': {'path': 'path/to/file', 'content': 'content'}, 'reason': '<reason for the task>'}
	
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
	NOTE: DO NOT use "&&" in your command. If multiple commands have to be run, do them in subsequent tasks.
	 Don't use '&&' to combine commands

	In addition to all the above mentioned field, every task should have a "reason" field at the top level, which
	describes in not more than 3 sentences, why this task was chosen as the current task. 
	
	output only ONE such task, one of type write, read, or run. And this task is the NEXT task that to be performed. 
	the purpose of the task is to get enough information for the next task, so this might require reading files or 
	running some commands to look at outputs. 

	NOTE: Before coming up next tasks, check the previous tasks that are finished If no other tasks are remaining for 
	the goal, just return {'type': 'finished'} WITHOUT any other text preceding or succeeding it. I REPEAT, CHECK THE 
	LIST OF FINISHED TASK TO SEE IF ANYTHING MORE HAS TO BE DONE BEFORE SUGGESTING THE NEXT TASK

	You shall NOT use pdb to debug. 
	You shall NOT install any new packages or tools 

    NOTE: Before coming up with the next task, confirm that the next task is not already executed. If it's executed, 
	DO NOT repeat it. If repeating is necessary for some reason, CLEARLY explain why in the "reason" field. 

	If the last line of this prompt is a question (that ends with "?") then, respond in the following format
	{'type': 'info', 'content': '<your response>'}. This is not considered as a task. 

	DO NOT write your response as free text. Only send response in the requested format.
'''	

def construct_prompt(prefix, reduce_context, goal, discarded_tasks, steps_so_far): 
	completed_tasks = [str(s) for s in steps_so_far]

	if len(completed_tasks) > 5:
		completed_tasks = completed_tasks[-5:]

	if reduce_context:
		completed_tasks = completed_tasks[1:]

	completed_tasks = "\n\n".join(completed_tasks)
	last_discareded_tasks = "\n\n".join(discarded_tasks[-3:] if len(discarded_tasks) > 3 else discarded_tasks)	

	task_data_prompt  = '''
		Here is the goal you have to carry out, for which you need to keep 
		finding the next task until the goal is accomplished 

		goal: %s	
		Here are the last 5 task you've done: %s
		Here are the last 3 discarded tasks which were never executed, along with the user comments %s

		''' % (completed_tasks, goal, last_discareded_tasks) 
	last_task = ""

	if (len(steps_so_far) > 0):	
	
		if steps_so_far[-1]['task_execution_report']['success']:
			last_task = steps_so_far[-1]['task_execution_report']['output']   
		else:
			last_task = steps_so_far[-1]['task_execution_report']['error']
 
	return prefix + task_data_prompt + response_format_prompt + last_task
