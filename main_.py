# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press ⌘F8 to toggle the breakpoint.




# -*- coding: utf-8 -*-

import os
import re
import ssl
import time
import uuid
import socket
import threading

from queue import Queue
from slackclient import SlackClient
from slackclient.server import SlackConnectionError

# Constants
HOST = '127.0.0.1'
PORT = 9999
LISTEN = 5

RTM_READ_DELAY = 1
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"

CLIENT_SIG_ADD = "Add new client socket"

TOKEN = "xoxb-3264352708-2861930170147-xHlYJhCE57HtlVDZcXGNGnul"
CHANNEL_ID = "C02RE6TB6TE"  # qa_bot_world
BOT_UID = "U02RBTC504B"
# channel_id = "C02RE6TB6TE"  # qa_bot_world
# {
#     "ok": true,
#     "url": "https://stockplus.slack.com/",
#     "team": "두나무",
#     "user": "qa-bot1",
#     "team_id": "T037SACLU",
#     "user_id": "U02RBTC504B",
#     "bot_id": "B02QX86RVT9",
#     "is_enterprise_install": false
# }

device_dict = {  # ID : SERIAL
    "nano11130@kakao.com": "R3CRA0BT8CD",  # 갤럭시 폴드3
    "01076439939": "R3CRA0B8T3L",  # 갤럭시z 플립3
    "tothemoon1004@kakao.com": "R3CR70KJTBN",  # 갤럭시s21 울트라
}

chat_list = {
    "안녕": "꺼져",
    "-_-": "퉤 =3",
    "제레미": "바보",
    "내일봐": "충성충성",
    "내일 보자:": "충성충성",
    "내일보자": "충성충성",
    "야": "머 임마?",
    "고생": "고맙쯤미다 흑흑 ㅠㅠ",
    "자나": "피곤해요 /_\\",
    "자니": "피곤해요 /_\\",
    "수고했어": "네 고마워요",
    "수고했다": "오냐 ㅋㅋ",
}

client_socket_dict = {}  # { client uuid : client socket object }
SEND_QUEUE = Queue()

# SSL
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


def get_slack_client():
    print("get_slack_client - try to connect SLACK API")
    return SlackClient(token=TOKEN, ssl=ssl_context)


def connect_rtm():
    slack = get_slack_client()
    try:
        print("connect_rtm - try to connect rtm socket")
        if slack.rtm_connect(with_team_state=False):
            print(f"Bot connected! Bot UID is:{slack.api_call('auth.test')['user_id']}")
            return slack
        else:
            raise Exception()
    except:
        print("Connection failed. Exception traceback printed above.")
        return False


def reconnect_rtm():
    print("reconnect_rtm")
    return connect_rtm()


def get_id(command):
    uid = command.split()[0]

    # nano11130@kakao.com	갤럭시 폴드3		@easton
    # 01076439939	갤럭시z 플립3		@jeremy
    # tothemoon1004	갤럭시s21 울트라		@bale
    # 01076037792	아이폰13		@euny

    # 이메일 Hyperlink 제거, <mailto:nano11130@kakao.com|nano11130@kakao.com>
    if "<mailto:" in uid:
        uid = uid.split("|")[0]
        uid = uid.replace("<mailto:", "")

    return uid


def command_device_ready(command, channel):
    # check UID and Serial in device list
    uid = get_id(command)
    print(f"UID id Command: {uid}")

    if uid not in device_dict:
        # no device in device_list Dict
        return False
    else:
        # SERIAL in device_list Dict
        device_name = device_dict[uid]

        # query to All client socket to find device
        SEND_QUEUE.put([device_name, uid, channel])
        return True


def result_device_ready(device_name, uid, channel):
    msg = f"{uid}({device_name}) 기기 준비되었어요. 카톡 인증 요청을 하면 응답해드릴게요 :smile:"
    send_message(channel, msg)


def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If it's not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == BOT_UID:
                return message, event["channel"]
    return None, None


def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)


def handle_command(command, channel):
    # Default response is help text for the user
    default_response = "@빈둥이 '계정' 인증 부탁해 라고 입력해보세요. ex) @빈둥이 nano11130@kakao.com 인증 부탁해"

    # Command response
    response = None

    # execute high priority command

    # 인증
    # get account string and remove email hyperlink decoration
    # find connected adb devices
    # and try to wakeup, type PIN and ready
    if "인증" in command:
        if command_device_ready(command, channel) == True:
            response = "계정에 연결된 기기를 찾는 중 입니다."

            # uid = get_id(command)
        # print(f"UID id Command: {uid}")
        #
        # if wakeup_device(uid):
        #     response = "준비되었어요. 카톡 인증 요청을 하면 응답해드릴게요 :smile:"
        # else:
        #     # 기기 준비 실패
        #     response = "기기 준비 실패해쪄염 뿌우 :zany_face:"

    # very useful bot chat
    if response is None:
        for i in chat_list:
            if i in command:
                response = chat_list[i]

    # Sends the response back to the channel
    if response is None:
        send_message(channel, default_response)
    else:
        send_message(channel, response)


def send_message(channel, msg):
    try:
        print("send_message - get New slack socket and send message to the channel")
        slack = get_slack_client()

        slack.api_call(
            "chat.postMessage",
            channel=channel,
            as_user=True,
            text=msg
        )
    except:
        print("send_message - fail")
        pass


def send(client_socket_dict, send_queue):
    print("Thread start - send")
    while True:
        try:
            recv = send_queue.get()
            print("recv data =", recv)

            if recv == CLIENT_SIG_ADD:
                print("Thread stop - send : ", recv)
                break

            for client_uuid in client_socket_dict.keys():
                client_socket = client_socket_dict[client_uuid]

                # SEND_QUEUE.put([device_name, uid, channel])
                msg = f"{recv[0]} {recv[1]} {recv[2]}"

                try:
                    client_socket.send((msg.encode("utf-8")))
                    print("Send To - ", client_uuid, msg)
                except:
                    del client_socket_dict[client_uuid]
                    pass
        except:
            print("got some error")
            pass


def recv(client_socket, client_uuid):
    print("Thread start - recv", client_uuid)
    while True:
        try:
            data = client_socket.recv(1024).decode("utf-8")
            if data == "":
                print("Thread stop - recv thread broken :", client_uuid)
                break
            else:
                print("Client Message - ", client_uuid, data)

                # function call
                # SEND_QUEUE.put([device_name, uid, channel])
                data = data.split()
                device_name = data[0]
                uid = data[1]
                channel = data[2]
                result_device_ready(device_name, uid, channel)

        except ConnectionResetError:
            pass


def run_socket_service():

    try:
        # 해당 PORT 사용하는 프로세스 모두 KILL => 서버 & 연결된 클라 연결까지
        # => 클라이언트까지 Kill 되는 문제가 있어서 사용 보류
        # os.system(f'kill -KILL `lsof -i:{PORT} -t`')
        # time.sleep(3)

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        server_socket.bind((HOST, PORT))
        server_socket.listen(LISTEN)
    except OSError:
        print("asdfadsf")
        pass

    while True:
        print("Wait for client connect request...", time.strftime('%H:%M:%S'))

        # wait for client connect
        client_socket, addr = server_socket.accept()

        # if connected
        # generate new uuid for client socket
        client_uuid = str(uuid.uuid1())

        # add client uuid and socket to Dict
        client_socket_dict[client_uuid] = client_socket

        print("Connected - ", client_uuid, addr)
        print(len(client_socket_dict.keys()), client_socket_dict)

        if len(client_socket_dict.keys()) > 1:
            # if count > 1:
            SEND_QUEUE.put(CLIENT_SIG_ADD)
            thread_1 = threading.Thread(target=send, args=(client_socket_dict, SEND_QUEUE,))
            thread_1.start()
            # pass
        else:
            thread_1 = threading.Thread(target=send, args=(client_socket_dict, SEND_QUEUE,))
            thread_1.start()

        thread_2 = threading.Thread(target=recv, args=(client_socket, client_uuid,))
        thread_2.start()


def main():
    slack = connect_rtm()
    start = time.time()

    # Test code
    # slack = False

    while True:
        try:
            if slack == False:
                raise SlackConnectionError

            # Read slack message from RTM socket
            msg = slack.rtm_read()
            print("slack.rtm_read() - ", msg)

            # find bot mentioned message
            command, channel = parse_bot_commands(msg)

            # handel command
            if command:
                print("Bot caught some command - ", command)
                handle_command(command, channel)

            # 1-second delay for while loop
            time.sleep(RTM_READ_DELAY)
            print("wait...", time.strftime('%H:%M:%S'), command)

            # Reconnect slack every 5 minute
            end = time.time()
            if (end - start) > 5 * 60:
                slack = reconnect_rtm()
                start = time.time()
                print("reconnect slack every 5 min")

        # except (WebSocketConnectionClosedException, SlackConnectionError):
        except:
            print("꽥 x_X")
            slack = reconnect_rtm()
            if slack == False:
                time.sleep(5)
            else:
                print("으허허헉 살아났다!")


# def main():
    # 내일 할 거
    # main
    #   run_socket_service
    #   run_slackbot_service


if __name__ == "__main__":

    socket_main_thread = threading.Thread(target=run_socket_service, args=())
    socket_main_thread.start()

    time.sleep(1)
    print(socket_main_thread.is_alive())

    if socket_main_thread.is_alive():
        main()
        pass

