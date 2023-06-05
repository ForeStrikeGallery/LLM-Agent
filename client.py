import json 
import time 
import openai 
import logging 

with open('secrets.json') as f:
	secrets = json.load(f)

openai.organization = "org-rpFAIRUIBdByWr2P89N0MRmO"
openai.api_key = secrets["apiKey"]

class LLM: 

	@staticmethod 
	def getResponse(prompt, system_msg = "you are a helpful AI agent"):
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
			
			logging.error("Error while fetching API response, waiting for 5 seconds: %s"%(str(e)))
			time.sleep(5)

			return getResponse(prompt)

		return response["choices"][0]["message"]["content"] 


