# -*- coding: utf-8 -*-
from flask import Flask, request, abort
import requests
import json
from linebot import (
    LineBotApi, WebhookHandler
)
import time
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage ,SourceUser
)
from linebot.models import *
import pandas as pd
import configparser
import datetime
import json
import requests
from bs4 import BeautifulSoup
from chatgpt import ChatGPT
chatgpt = ChatGPT()

#爬玩股網
def wantgoo(sid):
    target_url = 'https://www.wantgoo.com/stock/'+sid
    rs = requests.session()
    res = rs.get(target_url)#verify=False
    soup = BeautifulSoup(res.text, 'html.parser')
    content = ''
    if len(soup.select('.cn div'))!=0:
        for titleURL in soup.select('.cn div'):
            title = titleURL.text.replace(' ','').replace('\n','').replace('\r','')
            data = '{}\n'.format(title)
            content += data
    else:
        content += '沒有搜尋到匹配的股票'
    return '{}\n{}'.format(sid,content)

app = Flask(__name__,static_url_path = "/images" , static_folder = "./images/" )

#Line的一些使用者金鑰設定
line_bot_api = LineBotApi('5kICaBiVxMwVBoP2EB4ZomImaet1xvwiXMrKHER3SDJUVOaeuPZyrHGWXXXCIrF9JkjBynrWTRh93wYcjTNwCUS6FgUWSTSvwryyzfQx7q/uxct6LlHs5gs1QjcNwfUm6NqcmTLh923ezTaa3GLRAQdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('0e5e4c91217b0abae408c37512bd8352')
host_id="Uc13726ca34cc65314694bad1cb6b7394"

#定義路由器
@app.route("/", methods=['POST'])
def index():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


#定義接收到文字訊息要如何處理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.message.text == 'profile':
        if isinstance(event.source, SourceUser):
            profile = line_bot_api.get_profile(event.source.user_id)
            line_bot_api.reply_message(
                event.reply_token, [
                    TextSendMessage(text='Display name: ' + profile.display_name),
                    TextSendMessage(text='Status message: ' + profile.status_message)
                ]
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="Bot can't use profile API without user ID"))
    
#當別人密我時回報他的group_id/user_id位置
    if event.source.user_id!=host_id:
        if event.source.type=='group':
            group_id=event.source.group_id
            group_text=event.message.text+'\n'+'from'+'\n'+group_id
            line_bot_api.push_message(host_id,TextSendMessage(text=group_text))
        else:
            guest_id=event.source.user_id
            guest_text=event.message.text+'\n'+'from'+'\n'+guest_id
            line_bot_api.push_message(host_id,TextSendMessage(text=guest_text))
#傳訊
    if (event.source.user_id==host_id) and (event.message.text.split(':')[0]=='@傳訊'):
        host_text=event.message.text
        To_userid=host_text.split(':')[1]
        My_message=host_text.split(':')[2:]
        content=""
        for i in My_message:
            content+=i
        line_bot_api.push_message(To_userid,TextSendMessage(text=content))
#取得個資
    if (event.source.user_id==host_id) and (event.message.text.split(':')[0]=='@取得個資'):
        user_id=event.message.text.split(':')[1]
        profile = line_bot_api.get_profile(user_id)
        line_bot_api.reply_message(event.reply_token,[
            TextSendMessage(text='Display name: ' + str(profile.display_name)),
            TextSendMessage(text='Status message: ' + str(profile.status_message)),
            TextSendMessage(text='Photo url: ' + str(profile.picture_url))])
#玩股網診股
    elif (event.message.text.split(' ')[0]=="技術健診") and (len(event.message.text.split(' '))==2):
        sid=event.message.text.split(' ')[1]
        content=wantgoo(sid)
        line_bot_api.reply_message(event.reply_token,TextSendMessage(content))
#chatgpt
    elif(event.message.text != "個股健診")&(event.message.text != "選股")&(event.message.text != "走勢預測"):
        chatgpt.add_msg(f"Human:{event.message.text}?\n")
        reply_msg = chatgpt.get_response().replace("AI:", "", 1)
        chatgpt.add_msg(f"AI:{reply_msg}\n")
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text=reply_msg))
#run
if __name__ == "__main__":
    app.run(host='127.0.0.1', port=2336, debug=True)
