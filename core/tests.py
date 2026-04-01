from django.test import SimpleTestCase, TransactionTestCase
from redis.connection import Connection as RedisConnection, ConnectionError
from django.db import connection as db_connection , OperationalError

# Create your tests here.
class DataBaseConnectionTestCase(TransactionTestCase):
    """This test case is for testing the health of the database (postgres) and it will use the main database that we use in the settings"""

    def test_database_connection(self):
        try:
            connection = db_connection.ensure_connection()
            with db_connection.cursor() as conn:
                conn.execute("SELECT 1")
        except OperationalError:
            self.fail(msg="Database connection failed. check the Database")
        except Exception as e:
            self.fail(f"An unexpected error occurred during database connection test: {e}")
        

class CacheConnectionTestCase(SimpleTestCase):

    def test_cache_connection(self):
        try:
            connection = RedisConnection().connect()
        except ConnectionError:
            self.fail(msg="Cache service is not available")
        except Exception as e:
            self.fail(f"An unexpected error occurred during redis connection test: {e}")
            
