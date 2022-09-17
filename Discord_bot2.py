import os
import json
import requests

# the Discord Python API
import discord

# Queue code
from collections import deque
  
# Initializing a queue
maxsize = 3
past_input = deque(maxlen = maxsize)
generated_responses = deque(maxlen = maxsize)

# this is my Hugging Face profile link
API_URL = 'https://api-inference.huggingface.co/models/Nakul24/'

class User():
    def __init__(self, id: str):
        self.id = id
        maxsize = 3
        self.past_input = deque(maxlen = maxsize)
        self.generated_responses = deque(maxlen = maxsize)
    
    def update(self, past_input: deque,generated_responses :deque):
        self.past_input = past_input
        self.generated_responses = generated_responses
      
    def getpast(self):
      return (self.past_input)

    def getresponse(self):
      return (self.generated_responses)
      

users = {}


class MyClient(discord.Client):
    def __init__(self, model_name):
        super().__init__()
        self.api_endpoint = API_URL + model_name
        # retrieve the secret API token from the system environment
        huggingface_token = os.environ['Huggingface_token']
        # format the header in our request to Hugging Face
        self.request_headers = {
            'Authorization': 'Bearer {}'.format(huggingface_token)
        }

    def query(self, payload):
        """
        make request to the Hugging Face model API
        """
        data = json.dumps(payload)
        response = requests.request('POST',
                                    self.api_endpoint,
                                    headers=self.request_headers,
                                    data=data)
        ret = json.loads(response.content.decode('utf-8'))
        return ret

    async def on_ready(self):
        # print out information when the bot wakes up
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')
      
        # send a request to the model without caring about the response
        # just so that the model wakes up and starts loading
        self.query({'inputs': {'text': 'Yo!'}})

    async def on_message(self, message):
        """
        this function is called whenever the bot sees a message in a channel
        """
        
        # ignore the message if it comes from the bot itself
        if message.author.id == self.user.id:
            return
        global users  
    
        if message.author.id not in users:
          users[message.author.id] = User(message.author.id)

        past_input = users[message.author.id].getpast()
        generated_responses =users[message.author.id].getresponse()

        # Reset chat on reset command
        if message.content == 'Reset':
          past_input = deque(maxlen = maxsize)
          generated_responses = deque(maxlen = maxsize)
          users[message.author.id].update(past_input,generated_responses)
          await message.channel.send("Reset Complete")
          return
        else:

          
        # form query payload with the content of the message
          payload = {'inputs': {
            'text': message.content,
            "past_user_inputs": list(users[message.author.id].getpast()),
            "generated_responses": list(users[message.author.id].getresponse()),         
            },
              "parameters": {
                'min_length': 4,
                'max_length': 120,
                'top_k':450,
                'top_p':0.88,
                'temperature' : 0.70,
                'repetition_penalty': 1.5,
                
              }     }
          past_input.append(message.content)
          
  
          # while the bot is waiting on a response from the model
          # set the its status as typing for user-friendliness
          async with message.channel.typing():
            response = self.query(payload)
          bot_response = response.get('generated_text', None)
          generated_responses.append(bot_response)
          users[message.author.id].update(past_input,generated_responses)
          #print(bot_response + f"\n @{message.author.name}")
          #print(generated_responses)
          
          # we may get ill-formed response if the model hasn't fully loaded
          # or has timed out
          
          if not bot_response:
              if 'error' in response:
                  past_input = deque(maxlen = maxsize)
                  generated_responses = deque(maxlen = maxsize)
                  users[message.author.id].update(past_input,generated_responses)
                  bot_response = '`Error: {}` \n Reset Complete'.format(response['error'])
                  
              else:
                  bot_response = 'Hmm... something is not right. Please message Reset'
  
          # send the model's response to the Discord channel
          await message.channel.send(bot_response + "\n<@{}>".format(message.author.id))

def main():
    # DialoGPT-medium-joshua is my model name
    client = MyClient('YC_Bot')
    client.run(os.environ['Discord_token'])

if __name__ == '__main__':
  main()
