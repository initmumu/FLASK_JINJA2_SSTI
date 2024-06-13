class ChatRepository:
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super().__new__(cls)
    
        return cls.instance

    def setConnPool(self, connPool):
        self.connPool = connPool


    def createNewMessage(self, senderHash, receiverHash, message):
        query = """
        INSERT INTO public.chat (sender_hash, receiver_hash, message)
        VALUEs (%s, %s, %s)
        """
        conn = self.connPool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, (senderHash, receiverHash, message))
        except Exception as e:
            print(e)
            return False
        finally:
            conn.commit()
            self.connPool.putconn(conn)
            return True

    def getMessages(self, myHash, yourHash):
        query = """
        SELECT chat_id, sender_hash, receiver_hash, message, publish_time
        FROM public.chat
        WHERE (receiver_hash=%s AND sender_hash=%s) OR (receiver_hash=%s AND sender_hash=%s)
        """
        conn = self.connPool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, (myHash, yourHash, yourHash, myHash))
                result = cursor.fetchall()
        except Exception as e:
            print(e)
            return False
        finally:
            conn.commit()
            self.connPool.putconn(conn)
            return result