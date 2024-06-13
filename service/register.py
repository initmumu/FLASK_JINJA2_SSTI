def registerService(userRepository, userId, userPw, userName):
    try:
        userRepository.createUser(userId, userPw, userName)
        
    except Exception as e:
        return (1, e)

    finally:
        return 0

def checkDuplicateId(userRepository, userId):
    try:
        result = userRepository.checkDuplicateId(userId)
        
    except Exception as e:
        return (100, e)

    finally:
        return result

def checkIdAndPw(userRepository, userId, userPw):
    try:
        result = userRepository.checkIdAndPw(userId, userPw)
        
    except Exception as e:
        return (100, e)

    finally:
        return result