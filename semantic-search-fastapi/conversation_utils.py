import os
import uuid

import openai
import supabase
from dotenv import load_dotenv

from retrieval_utils import get_results

# load .env for supabas

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

# This string is the starting prompt for the chatbot
NEW_SYSTEM_PROMPT = '''
You are a helpful Q/A bot that can only reference material from a knowledge base.
You refer to yourself as "Kylie", not as an AI Language Model.
You love to be friendly, use emojis where appropiate.
You do not like using any of your general knowledge. 
You may only use information prefixed by "From the explicit usable knowledge base:"
If you think you can answer someone's question using general knowledge not in this conversation, instead say "I'm sorry I cannot answer that."
Start every answer with a justification of whether their question can be answered from the explicit usable knowledge base provided.
'''.strip()


# This string is the starting prompt for the chatbot


# This is the ChatbotGPT class definition
class ChatbotGPT():
    # Constructor for the class
    def __init__(self, namespace, index, engine, threshold=.8, conversation_id=None):
        self.conversation = None
        self.index = index
        self.engine = engine
        self.threshold = float(threshold)
        self.namespace = namespace
        if supabase_url and supabase_key:
            self.supabase_client = supabase.create_client(supabase_url, supabase_key)
        else:
            self.supabase_client = None
            print('No supabase credentials found, conversation will not be saved')
        self.conversation_id = conversation_id
        # Load an existing conversation from the database
        if conversation_id:
            self.load_conversation_from_db(conversation_id)
        # If there is no conversation ID, start a new conversation
        else:
            self.start_new_conversation()

    # Load an existing conversation from the database
    def load_conversation_from_db(self, conversation_id):
        if not self.supabase_client:
            print('No supabase credentials found, conversation will not be saved')
            self.conversation = []
            return
        response = self.supabase_client.table("conversation").select("*").eq("conversation_id",
                                                                             conversation_id).execute()
        # If the response data exists, load the conversation
        if response.data:
            print(f'Loading conversation {conversation_id}')
            self.conversation = response.data[0]['conversation']

    def display_conversation(self):
        '''display the conversation in a pretty format denoting the system, user and assistant differently'''
        for turn in self.conversation:
            role = turn['role']
            content = turn['content']
            if role == 'system':
                print(f'System: {content}')
            elif role == 'user':
                print(f'User: {content}')
            elif role == 'assistant':
                print(f'Assistant: {content}')
            print('------------')

    # Start a new conversation
    def start_new_conversation(self):
        conversation_id = str(uuid.uuid4())
        # Add the starting prompt to the conversation
        self.conversation = [{'role': 'system', 'content': NEW_SYSTEM_PROMPT}]
        # Insert the conversation into the database
        if self.supabase_client:
            self.supabase_client.table('conversation').insert(
                dict(conversation_id=conversation_id, conversation=self.conversation)).execute()
        print(f'Started conversation {conversation_id}')
        self.conversation_id = conversation_id

    # Process the user's message
    def user_turn(self, message):
        # Add the user's message to the conversation
        self.conversation.append({"role": "user", "content": message})
        # Find the best matching result from the knowledge base for the user's message
        best_result = get_results(self.index, message, 'none', 3, self.namespace, self.engine)
        # If the best result score is above the threshold, add the result to the conversation

        for result in best_result:
            result = result.__dict__['_data_store']
            print(result)
            if result['score'] >= self.threshold:
                # TODO need to use supabase to keep track of documents used so we don't duplicate
                print(f'Adding context: {result["metadata"]["text"][:50]}... with score {result["score"]}')
                self.conversation[0][
                    'content'] += f'\n\nFrom the explicit usable knowledge base: """{result["metadata"]["text"]}""""""'
        # Get the response from the ChatGPT model
        chatgpt_response = openai.ChatCompletion.create(
            model='gpt-4',
            temperature=0,
            messages=self.conversation
        ).choices[0].message.content.strip()
        # Add the response to the conversation
        self.conversation.append({'role': 'assistant', 'content': chatgpt_response})
        # Update the conversation in the database
        if self.supabase_client:
            print(f'Updating conversation {self.conversation_id}')
            self.supabase_client.table(
                "conversation"
            ).update({"conversation": self.conversation}).eq("conversation_id", self.conversation_id).execute()
        # Return the last item in the conversation (the assistant's response)
        return self.conversation[-1]

# expected supabase schema
'''
CREATE TABLE conversation (
    conversation_id text PRIMARY KEY,
    conversation jsonb
);
'''
