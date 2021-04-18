import redis
import json
from settings import *
#from main import User

class RedisUserLocationStorage:
    """
    Class will create/store/update users locations data
    """
    redis = None
    hash_key = 'users'

    def __init__(self):
        self.redis = redis.from_url(REDIS_URL)

    def update_user_data(self, user):
        self.redis.hset(self.hash_key, key = user.user_id, value = json.dumps(user.__dict__))

    def retrived_user_data(self, user_id):
        recieved_data = self.redis.hget(self.hash_key, user_id)
        if recieved_data:
            return json.loads(recieved_data)

if __name__ == '__main__':
    user_storage = RedisUserLocationStorage()
    user_id  = 123
    user_created = User(123)
    user_created.add_place_name('Пиццерия')
    user_created.add_place_address('Пиццерия', 'Лесная 9')
    user_storage.update_user_data(user_created)
    retrived_data = user_storage.retrived_user_data(user_id)
    user_retrived = User.user_creation(retrived_data)
