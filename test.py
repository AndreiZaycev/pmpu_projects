import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from collections import defaultdict
import pandas as pd
from datetime import datetime
from telethon.tl.types import Message, PeerChannel, Channel, MessageReplies
from telethon.tl.functions.channels import GetFullChannelRequest
import pandas as pd 
from pandas.testing import assert_frame_equal
from universities_crawler import TelegramAnalyzer, __TERMS__

class TestTelegramAnalyzer(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client_mock = AsyncMock()
        
        self.analyzer = TelegramAnalyzer(self.client_mock)
        
        self.test_message = MagicMock(spec=Message)
        self.test_message.message = "Тестовое сообщение с упоминанием СПбГУ"
        self.test_message.peer_id = MagicMock(spec=PeerChannel)
        self.test_message.peer_id.channel_id = 123
        self.test_message.views = 100
        self.test_message.forwards = 10
        self.test_message.replies = MagicMock(spec=MessageReplies)
        self.test_message.replies.replies = 5
        self.test_message.date = datetime.now()

        self.channel_mock = MagicMock(spec=Channel)
        self.channel_mock.id = 123
        
        self.dialog_mock = MagicMock()
        self.dialog_mock.entity = MagicMock(spec=Channel)
        
        self.channel_full_mock = MagicMock()
        self.channel_full_mock.full_chat = MagicMock()
        self.channel_full_mock.full_chat.participants_count = 1000

    async def test_search_messages(self):
        async def mock_iter_dialogs():
            yield self.dialog_mock
        self.client_mock.iter_dialogs = mock_iter_dialogs

        self.client_mock.get_entity.return_value = self.channel_mock

        self.client_mock.return_value = self.channel_full_mock
        async def mock_iter_messages(*args, **kwargs):
            yield self.test_message
        self.client_mock.iter_messages = mock_iter_messages

        await self.analyzer.search_messages(__TERMS__, limit=10)

        self.client_mock.assert_awaited_once()
        
        self.assertEqual(self.analyzer.stats['total_posts'], 8) # мы проглядываем посты для каждого терма поэтому ожидается 8 * 1
        self.assertEqual(len(self.analyzer.stats['unique_channels']), 1)
        self.assertEqual(self.analyzer.stats['views'], 8 * 100)
        self.assertEqual(self.analyzer.stats['forwards'], 8 * 10)
        self.assertEqual(self.analyzer.stats['replies'], 8 * 5)
        
    async def test_process_message(self):
        await self.analyzer.process_message(self.test_message, __TERMS__, 'спбгу')
        
        self.assertEqual(self.analyzer.stats['total_posts'], 1)
        self.assertEqual(len(self.analyzer.stats['unique_channels']), 1)
        self.assertEqual(self.analyzer.stats['views'], 100)
        self.assertEqual(self.analyzer.stats['forwards'], 10)
        self.assertEqual(self.analyzer.stats['replies'], 5)
        self.assertEqual(self.analyzer.stats['mentions']['спбгу'], 1)
        
        await self.analyzer.collect_message(self.test_message)
        self.assertEqual(len(self.analyzer.data), 1)
        self.assertEqual(self.analyzer.data[0], self.test_message.message)

    def test_get_statistics(self):
        self.analyzer.stats = {
            'total_posts': 10,
            'unique_channels': {1, 2, 3},
            'views': 1000,
            'forwards': 100,
            'replies': 50,
            'posts_by_day': defaultdict(int, {'2023-01-01': 5, '2023-01-02': 5}),
            'mentions': {'спбгу': 7, 'мгу': 3}
        }

        stats_df = {
            'Метрика': [
                'Всего сообщений', 
                'Уникальных каналов', 
                'Просмотров', 
                'Репостов', 
                'Ответов',
                'Упоминаний вуза спбгу',
                'Упоминаний вуза мгу'
            ],
            'Значение': [
                10,
                3,
                1000,
                100,
                50,
                7,
                3
            ]
        }
        
        stats_df = self.analyzer.get_statistics()
        
        self.assertIsInstance(stats_df, pd.DataFrame)
        self.assertEqual(len(stats_df), 7)  # 5 базовых метрик + 2 упоминания
        data = pd.read_csv('universities_posts_stats.csv')
        assert_frame_equal(data, pd.DataFrame(stats_df))

    @patch('matplotlib.pyplot.show')
    def test_plot_statistics(self, mock_show):
        self.analyzer.stats['posts_by_day'] = defaultdict(int, {
            '2023-01-01': 228, 
            '2023-01-02': 1337
        })
        import os
        if os.path.exists(
            'publications_count.png'
        ):
            os.remove('publications_count.png')
        self.analyzer.plot_statistics()
        
        mock_show.assert_called_once()
        
        self.assertTrue(os.path.exists('publications_count.png'))
        os.remove('publications_count.png')

    def test_flush_crawled_data(self):
        self.analyzer.data = ["msg1", "msg2", "msg3"]
        
        self.analyzer.flush_crawled_data()
        
        with open('crawled_messages.csv', 'r') as f:
            content = f.read()
            self.assertIn('msg1', content)
            self.assertIn('msg2', content)
            self.assertIn('msg3', content)

    async def test_search_messages_with_small_channel(self):
        # Настраиваем мок для канала с малым количеством участников
        async def mock_iter_dialogs():
            yield self.dialog_mock
        self.client_mock.iter_dialogs = mock_iter_dialogs



        small_channel_mock = MagicMock()
        small_channel_mock.entity = MagicMock(spec=Channel)
        self.client_mock.get_entity.return_value = small_channel_mock

        channel_full_small_mock = MagicMock()
        channel_full_small_mock.full_chat = MagicMock()
        channel_full_small_mock.full_chat.participants_count = 50  # меньше 100
        self.client_mock.return_value = channel_full_small_mock
        async def mock_iter_messages(*args, **kwargs):
            yield self.test_message
        self.client_mock.iter_messages = mock_iter_messages

        await self.analyzer.search_messages(__TERMS__, limit=10)

        self.client_mock.assert_awaited_once()
        
        await self.analyzer.search_messages(__TERMS__, limit=10)
        
        self.assertEqual(self.analyzer.stats['total_posts'], 0)


if __name__ == '__main__':
    unittest.main()