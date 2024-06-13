class FriendRepository:
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super().__new__(cls)
    
        return cls.instance

    def setConnPool(self, connPool):
        self.connPool = connPool

    def createRequest(self, sender, receiver):
        query = """
        INSERT INTO public.friendrequests (sender_id, receiver_id)
        VALUES (%s, %s)
        """
        validateResult = self.checkRequestValid(sender, receiver)
        if validateResult[0] == 200:
            print(validateResult)
            conn = self.connPool.getconn()
            try:
                with conn.cursor() as cursor:
                    cursor.execute(query, (sender, receiver))
            except Exception as e:
                print(e)
                return (500, e)
            finally:
                conn.commit()
                self.connPool.putconn(conn)
                return True
        else: return validateResult



    def createFriendship(self, requestId):
        query = """
        INSERT INTO friendships (user_id1, user_id2)
        SELECT sender_id, receiver_id
        FROM friendrequests
        WHERE request_id = %s;

        DELETE FROM friendrequests
        WHERE request_id = %s;
        """
        conn = self.connPool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, (requestId, requestId))
        except Exception as e:
            print(e)
            return (False, e)
        finally:
            conn.commit()
            self.connPool.putconn(conn)
            return True

    def getRequestByRid(self, rid):
        query = """
        SELECT sender_id, receiver_id
        FROM public.friendrequests
        WHERE request_id=%s
        """
        conn = self.connPool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, (int(rid), ))
                result = cursor.fetchall()
        except Exception as e:
            print(e)
        finally:
            self.connPool.putconn(conn)
            return result


    def getRequestByUid(self, uid):
        query = """
        SELECT sender_id, receiver_id, request_id
        FROM public.friendrequests
        WHERE receiver_id=%s
        """
        conn = self.connPool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, (int(uid), ))
                result = cursor.fetchall()
        except Exception as e:
            print(e)
        finally:
            self.connPool.putconn(conn)
            return result

    def checkRequestValid(self, sender, receiver):
        conn = self.connPool.getconn()
        # 이미 보낸 요청인지 확인하는 쿼리
        query1 = """
        SELECT 1 FROM public.friendrequests WHERE (sender_id=%s AND receiver_id=%s)
        """

        # 상대방이 요청을 먼저 보냈는지 확인하는 쿼리
        query2 = """
        SELECT 1 FROM public.friendrequests WHERE (receiver_id=%s AND sender_id=%s)
        """

        # 이미 친구인지 확인하는 쿼리
        query3 = """
        SELECT 1 FROM public.friendships
        WHERE (user_id1=%s AND user_id2=%s) OR (user_id1=%s AND user_id2=%s)
        """

        try:
            returnTuple = None
            with conn.cursor() as cursor:
                cursor.execute(query1, (sender, receiver))
                result1 = cursor.fetchall()
                if result1:
                    returnTuple = (400, "이미 보낸 요청입니다.")

                cursor.execute(query2, (sender, receiver))
                result2 = cursor.fetchall()
                if result2:
                    returnTuple = (401, "상대방이 송신한 요청입니다.")

                cursor.execute(query3, (sender, receiver, receiver, sender))
                result3 = cursor.fetchall()
                if result3:
                    returnTuple = (402, "이미 친구인 사용자입니다.")

                if not result1 and not result2 and not result3: returnTuple = (200, "친구 요청을 성공적으로 보냈습니다!")
        except Exception as e:
            print(e)
            return(500, f"[DB_ERROR] {e}")

        finally:
            self.connPool.putconn(conn)
            return returnTuple

    def getAllFriends(self, uid):
        query = """
        SELECT uid, user_name, user_image, user_status_msg, hash_tag
        FROM public.user u
        JOIN (
        SELECT
            CASE
                WHEN user_id1 = %s THEN user_id2
                ELSE user_id1
            END AS friend_id
        FROM friendships
        WHERE user_id1 = %s OR user_id2 = %s
        ) f ON u.uid = f.friend_id;
        """
        conn = self.connPool.getconn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, (int(uid), int(uid), int(uid)))
                result = cursor.fetchall()
                print(result)
        except Exception as e:
            print(e)
        finally:
            self.connPool.putconn(conn)
            return result