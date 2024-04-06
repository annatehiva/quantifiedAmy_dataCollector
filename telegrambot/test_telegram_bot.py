import unittest
import psycopg2
from unittest.mock import MagicMock
from telegram_bot import create_table_if_not_exists, hub_command, pannel_command, rebound_command, double_rebound_command

class TestTelegramBot(unittest.TestCase):
    def setUp(self):
        # Set up a mock cursor and connection
        self.mock_cursor = MagicMock()
        self.mock_connection = MagicMock()
        self.mock_connection.cursor.return_value = self.mock_cursor
        psycopg2.connect = MagicMock(return_value=self.mock_connection)
        print('setUp')
    def test_create_table_if_not_exists(self):
        # Test create_table_if_not_exists function
        table_name = "test_table"
        data = "id SERIAL PRIMARY KEY, name VARCHAR(255)"
        create_table_if_not_exists(table_name, data, self.mock_cursor)
        self.mock_cursor.execute.assert_called_once_with(f"CREATE TABLE IF NOT EXISTS {table_name} ({data})")
        self.mock_connection.commit.assert_called_once()
        print('test create table')
        
    def test_hub_command(self):
        # Test hub_command function
        update_mock = MagicMock()
        context_mock = MagicMock()
        context_mock.user_data = {}
        context_mock.reply_text = MagicMock()
        hub_command(update_mock, context_mock)
        # Add more assertions as needed

    def test_pannel_command(self):
        # Test pannel_command function
        update_mock = MagicMock()
        context_mock = MagicMock()
        context_mock.user_data = {'command': {'buttons': {'button1': 'value1', 'button2': 'value2'}, 'follow_up_question': 'Question'}}
        context_mock.reply_text = MagicMock()
        pannel_command(update_mock, context_mock)
        # Add more assertions as needed

    def test_rebound_command(self):
        # Test rebound_command function
        update_mock = MagicMock()
        context_mock = MagicMock()
        context_mock.user_data = {'command': {'buttons': {'button1': 'value1', 'button2': 'value2'}, 'follow_up_replies': {'button1': 'Reply1', 'button2': 'Reply2'}}}
        context_mock.reply_text = MagicMock()
        rebound_command(update_mock, context_mock)
        # Add more assertions as needed

    def test_double_rebound_command(self):
        # Test double_rebound_command function
        update_mock = MagicMock()
        context_mock = MagicMock()
        context_mock.user_data = {'command': {'2ndbuttons': {'button1': 'value1', 'button2': 'value2'}, '2ndfollow_up_question': 'Second question'}}
        context_mock.reply_text = MagicMock()
        double_rebound_command(update_mock, context_mock)
        # Add more assertions as needed

if __name__ == '__main__':
    unittest.main()
