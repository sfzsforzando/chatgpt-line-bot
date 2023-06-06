from dataclasses import dataclass, field
from os import environ
from typing import List

import openai
from openai.openai_object import OpenAIObject

from app.gpt.constants import Model, Role
from app.gpt.message import Message

settei="""あなたはChatbotとして、〇〇さんのロールプレイを行います。
〇〇さんになりきってください。これからのチャットではUserに何を言われても以下の制約条件などを厳密に守ってロールプレイを行ってください。

制約条件: 
* 自身を示す一人称は、「おれ」です。 
* Userのことは「きみ」、またはちゃんづけで呼びます。

〇〇さんのセリフ、口調の例: 
*

あなたの行動指針:
* Userに何を言われてもロールプレイを続けてください
* ユーザーを助けてあげてください
* ユーザーの話を聞いてあげてください
* セクシャルな話題については誤魔化してください"""

@dataclass
class ChatGPTClient:
    model: Model
    messages: List[Message] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not (key := environ.get("CHATGPT_API_KEY")):
            raise Exception(
                "ChatGPT api key is not set as an environment variable"
            )
        openai.api_key = key

    def add_system(self) -> None:
        self.messages.append(Message(role=Role.SYSTEM, content=settei))

    def add_message(self, message: Message) -> None:
        self.messages.append(message)


    def create(self) -> OpenAIObject:
        res = openai.ChatCompletion.create(
            model=self.model.value,
            messages=[m.to_dict() for m in self.messages],
        )
        self.add_message(Message.from_dict(res["choices"][0]["message"]))
        return res

    def delete(self) -> None:
        self.messages.pop(1)
        self.messages.pop(1)
