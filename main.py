import sys
import os
from flask import Flask, request
import random, json, requests
import numpy as np

# line用ライブラリ
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, StickerSendMessage,
)

from os import environ
from typing import Dict

from dotenv import load_dotenv
from app.gpt.client import ChatGPTClient
from app.gpt.constants import Model, Role
from app.gpt.message import Message

load_dotenv(".env", verbose=True)

chatgpt_instance_map: Dict[str, ChatGPTClient] = {}

app = Flask(__name__)

channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)

if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

# Flaskのルート設定
@app.route("/")
def hello_world():
    return "hello world!"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
        text_message: TextMessage = event.message
        source: Source = event.source
        type: str= event.source.type;

        if type == 'user':
            id: str= event.source.userId;
        elif type == 'group':
            id: str= event.source.groupId;
        elif type == 'room':
            id: str= event.source.roomId;

        if (gpt_client := chatgpt_instance_map.get(id)) is None:
            gpt_client = ChatGPTClient(model=Model.GPT4)
            gpt_client.add_system()

        gpt_client.add_message(
            message=Message(role=Role.USER, content=text_message.text)
        )

        res = gpt_client.create()
        if res["usage"]["total_tokens"] > 2800:
            gpt_client.delete()

        res_text: str = res["choices"][0]["message"]["content"]

        # line_bot_api.reply_message(
        #     event.reply_token, TextSendMessage(text=res_text.strip())
        # )
        line_bot_api.push_message(id,TextSendMessage(text=res_text.strip()))

        if res["usage"]["total_tokens"] > 2800:
            gpt_client.delete()
        chatgpt_instance_map[id] = gpt_client


#------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)