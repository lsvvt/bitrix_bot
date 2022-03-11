from flask import Flask, request, abort
import telebot
import requests
import datetime
import os

my_token = os.environ['my_token']
chat_ids = [int(os.environ['chat_ids'])]
app_token = os.environ['app_token']
api_token = os.environ['api_token']

app = Flask(__name__)

@app.route('/')
def hello():
    print("LOL HELLO")
    return 'ЗАКРЫТО'

bot = telebot.TeleBot(my_token)


def form_html(text, arg):
    return f'<{arg}>' + text + f'</{arg}>'



def send(msg):
    """
    Send a message to a telegram user or group specified on chatId
    chat_id must be a number!
    """
    for chat_id in chat_ids:
        bot.send_message(chat_id, msg, parse_mode='HTML')

def get_users(user_info):
    return user_info["name"]


def gen_message_from_tasks(tasks):
    responsible_users = []
    for task in tasks:
        responsible_users.append(get_users(task["responsible"]))

    responsible_users = " ".join(responsible_users)

    task = tasks[0]
    
    title = form_html(task["title"], "i")
    message += f"{form_html('Новая задача', 'b')} (№{task_id}) для {responsible_users}: {title}"

    if len(task["group"]) > 0:
        group = form_html(form_html(task["group"]["name"], "b"), "i")
        message += f",  в рамках проекта {group}"
    message += "."

    if not task["deadline"] is None:
        deadline = task["deadline"]
        deadline = datetime.datetime.strptime(deadline[:-6], '%Y-%m-%dT%H:%M:%S')

        delta = str(deadline - datetime.datetime.now())[:-7].replace("days", "дней")
        message += f" Крайний срок: {form_html(deadline.strftime('%d.%m.%Y'), 'b')}, через {form_html(delta, 'b')}"


@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        print("POST")
        if request.form['auth[application_token]'] == app_token:
            print(request.form)
            data = request.form
            message = "Ничего не произошло"
            if data["event"] == "ONTASKCOMMENTADD":
                message = "Новый комментарий"
            if data["event"] == "ONTASKADD":
                message = ""
                task_id = data["data[FIELDS_AFTER][ID]"]
                response = requests.get(f"https://qmioc.bitrix24.ru/rest/16/{api_token}/tasks.task.get?taskId={task_id}")
                if response.status_code == 200:
                    rjson = response.json()
                    title = rjson["result"]["task"]["title"]
                    print(rjson)
                    if rjson["result"]["task"]["parentId"] is None:
                        response = requests.get(f"https://qmioc.bitrix24.ru/rest/16/{api_token}/tasks.task.list?filter[title]={title}")
                        rjson = response.json()
                        #print("list = ", rjson)
                        message = gen_message_from_tasks(rjson["result"]["tasks"])
                else:
                    message = "ERROR:2"

            send(message)
        else:
            print("ERROR:ILLEGAL ACCESS")
        return "Webhook received!"

if __name__ == '__main__':
    app.run()

