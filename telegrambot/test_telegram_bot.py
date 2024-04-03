import unittest
import psycopg2
from telegram_bot import create_table_if_not_exists

# Mocking the PostgreSQL connection and cursor
class MockCursor:
    def __init__(self):
        print('MockCursor initialized')
        self.tables = set()

    def execute(self, query):
        print('Executing query:', query)
        table_name = query.split()[2]
        self.tables.add(table_name)
        print('Table added:', table_name)

class MockConnection:
    def __init__(self):
        print('MockConnection initialized')
        self.cursor = MockCursor()

def mock_connect(**kwargs):
    print('Mock connect called')
    return MockConnection()

# Patching the psycopg2 module to use the mocked connection
psycopg2.connect = mock_connect

class TestCreateTableIfNotExists(unittest.TestCase):
    def test_create_table_if_not_exists(self):
        table_name = "test_table"
        data = "id SERIAL PRIMARY KEY, name VARCHAR(255)"

        # Create a single instance of MockCursor
        mock_cursor = MockCursor()

        # Call the function
        print('Calling create_table_if_not_exists function')
        create_table_if_not_exists(table_name, data)

        # Assert that the table was created
        print('Asserting table creation')
        self.assertIn(table_name, mock_cursor.tables)

if __name__ == '__main__':
    unittest.main()
