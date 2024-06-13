import random
import string

class UserRepository:
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super().__new__(cls)
        
        return cls.instance

    def setConnPool(self, connPool):
        self.connPool = connPool
    
    def createUser(self, userId, userPw, userName):
        query = """
        INSERT INTO public.user (user_id, user_pw, user_name, hash_tag)
        VALUES (%s, %s, %s, %s)
        """
        conn = self.connPool.getconn()
        try:
            with conn.cursor() as cursor:
                characters = string.ascii_uppercase + string.digits
                while True:
                    hashTag = ''.join(random.choice(characters) for _ in range(6))
                    if self.checkHash(hashTag, cursor):
                        break
                cursor.execute(query, (userId, userPw, userName, hashTag))
        except Exception as e:
            print(e)
        finally:
            conn.commit()
            self.connPool.putconn(conn)

    def checkHash(self, hashTag, cursor):
        query = """
        SELECT hash_tag
        FROM public.user
        WHERE hash_tag=%s
        """
        try:
            cursor.execute(query, (hashTag,))
            result = cursor.fetchone()
        except Exception as e:
            print(e)
        finally:
            return False if result else True

    def getUserInfo(self, userId):
        query = """
        SELECT user_id, user_name, user_status_msg, user_image, hash_tag, uid
        FROM public.user
        WHERE user_id=%s
        """
        conn = self.connPool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, (userId,))
                result = cursor.fetchone()
        except Exception as e:
            print(e)
        finally:
            self.connPool.putconn(conn)
            return result

    def getUserInfoByUid(self, uid):
        query = """
        SELECT user_id, user_name, user_status_msg, user_image, hash_tag, uid
        FROM public.user
        WHERE uid=%s
        """
        conn = self.connPool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, (uid,))
                result = cursor.fetchone()
        except Exception as e:
            print(e)
        finally:
            self.connPool.putconn(conn)
            return result if result else None

    def getUserInfoByHash(self, userHash):
        query = """
        SELECT user_id, user_name, user_status_msg, user_image, hash_tag, uid
        FROM public.user
        WHERE hash_tag=%s
        """
        conn = self.connPool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, (userHash,))
                result = cursor.fetchone()
        except Exception as e:
            print(e)
        finally:
            self.connPool.putconn(conn)
            return result if result else None


    def checkDuplicateId(self, userId):
        query = """
        SELECT user_id
        FROM public.user
        WHERE user_id=%s
        """
        conn = self.connPool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, (userId,))
                result = cursor.fetchone()

        except Exception as e:
            print(e)
        finally:
            self.connPool.putconn(conn)
            return True if result else False

    def checkIdAndPw(self, userId, userPw):
        query = """
        SELECT user_id
        FROM public.user
        WHERE user_id=%s AND user_pw=%s
        """
        conn = self.connPool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, (userId, userPw))
                result = cursor.fetchone()

        except Exception as e:
            print(e)
            
        finally:
            self.connPool.putconn(conn)
            return True if result else False