from revChatGPT.revChatGPT import Chatbot
import json

with open("config.json", "r") as cfg:
    config = json.load(cfg)

bot = Chatbot(config)

message = bot.get_chat_response("Hello world")['message']

print(message)
