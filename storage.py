import redis
import json
import pickle
from settings import *
from main import User

class RedisUserLocationStorage:
    redis = None
    hash_key = 'users'

    def __init__(self):
        self.redis = redis.from_url(REDIS_URL)

    def update_user_data(self, user):
        user_storage.redis.hset(self.hash_key, key = user.user_id, value = json.dumps(user.__dict__))

    def retrived_user_data(self, user_id):
        recieved_data = user_storage.redis.hget(self.hash_key, user_id)
        if recieved_data:
            return json.loads(recieved_data)

user_storage = RedisUserLocationStorage()

if __name__ == '__main__':
    print('here')
    user_id  = 123
    user_created = User(123)
    user_created.add_place_name('Пиццерия')
    user_created.add_place_address('Пиццерия', 'Лесная 9')
    user_storage.update_user_data(user_created)
    retrived_data = user_storage.retrived_user_data(user_id)
    user_retrived = User.user_creation(retrived_data)
    print(user_retrived.__dict__)

    print(user_storage.retrived_user_data(567))
