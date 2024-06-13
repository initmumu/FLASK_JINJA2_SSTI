from flask import Blueprint, request, current_app, jsonify, session, redirect
from service.register import registerService, checkDuplicateId, checkIdAndPw
import hashlib

bp = Blueprint('user', __name__, url_prefix='/user')

@bp.route('/<hash>')
def getUser(hash):
    result = current_app.userRepository.getUserInfoByHash(hash)
        # userInfo[0]: user id
        # userInfo[1]: user name
        # userInfo[2]: user status message
        # userInfo[3]: user image 
        # userInfo[4]: hash_tag
    if result:
        return jsonify({
            "msg": "유저를 찾았습니다.",
            "user_id": result[0],
            "user_name": result[1],
            "user_status_msg": result[2],
            "user_img": result[3],
            "hash_tag": result[4],
            "uid": result[5]
        })

    else:
        return jsonify({
            "msg": "입력한 유저가 존재하지 않습니다."
        })

@bp.route('/uid/<uid>')
def getUserByUid(uid):
    result = current_app.userRepository.getUserInfoByUid(uid)
        # userInfo[0]: user id
        # userInfo[1]: user name
        # userInfo[2]: user status message
        # userInfo[3]: user image 
        # userInfo[4]: hash_tag
    if result:
        return jsonify({
            "msg": "유저를 찾았습니다.",
            "user_id": result[0],
            "user_name": result[1],
            "user_status_msg": result[2],
            "user_img": result[3],
            "hash_tag": result[4],
            "uid": result[5]
        })

    else:
        return jsonify({
            "msg": "입력한 유저가 존재하지 않습니다."
        })

@bp.route('/login', methods=['POST'])
def login():
    params = request.get_json()
    userId, userPw = params['userId'], hashlib.sha256(params['userPw'].encode()).hexdigest()
    signinResult = checkIdAndPw(current_app.userRepository, userId, userPw)
    if signinResult:
        session['id'] = userId
        return jsonify({
            "msg": "로그인 성공",
        })
    else:
        return jsonify({
            "msg": "로그인 실패"
        })

@bp.route('/logout')
def logout():
    session.pop('id', None)
    return redirect('/page/login')

@bp.route('/register', methods=['POST'])
def registerUser():
        params = request.get_json()
        userId, userPw, userName = params['userId'], hashlib.sha256(params['userPw'].encode()).hexdigest(), params['userName']
        checkResult = checkDuplicateId(current_app.userRepository, userId)

        if not checkResult:
            serviceResult = registerService(current_app.userRepository, userId, userPw, userName)
            
            if serviceResult == 0:
                return jsonify({
                    'msg': 'success'
                })

            else:
                return jsonify({
                    'msg': result[1]
                })

        else:
            return jsonify({
                    'msg': 'Inputed ID is Duplicated'
                })
            