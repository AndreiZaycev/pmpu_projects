from telethon.sync import TelegramClient
from telethon.tl.types import InputMessagesFilterEmpty, Channel
from collections import defaultdict
import matplotlib.pyplot as plt
from telethon.tl.functions.channels import GetFullChannelRequest
import pandas as pd
import os
import asyncio

__TERMS__ = {
    'спбгу': list(map(str.lower, ['spbgu', 'спбгу', 'спб гу', 'spbu', 'Санкт-Петербургский государственный университет'])),
    'мгу': list(map(str.lower, ['msu', 'мгу', 'Московский государственный университет']))
}

class TelegramAnalyzer:
    def __init__(self, client):
        """
        Инициализация клиента Telegram
        :param client: Телеграм клиент
        """
        # Прокидывается девайс чтобы не разлогинивало со всех устройств
        self.client = client
        self.stats = {
            'total_posts': 0,
            'unique_channels': set(),
            'views': 0,
            'forwards': 0,
            'replies': 0,
            'posts_by_day': defaultdict(int),
            'mentions': defaultdict(int)
        }
        self.data = []
    
    async def search_messages(self, search_terms, limit=3000):
        """
        Поиск сообщений по ключевым словам
        :param search_terms: Список терминов для поиска (например, ['СПбГУ', 'МГУ'])
        :param limit: Максимальное количество сообщений для сбора
        """
        
        await self.client.start()
        dialogs = []
        async for dialog in self.client.iter_dialogs():
            if isinstance(dialog.entity, Channel):  # Только каналы c участниками больше 100
                try:
                    channel_connect  = await self.client.get_entity(dialog.entity)
                    channel_full_info = await self.client(GetFullChannelRequest(channel=channel_connect))
                    participants_count = channel_full_info.full_chat.participants_count
                    if participants_count is not None and participants_count > 100:
                        dialogs.append(dialog)
                except Exception as e:
                    print(f"Ошибка при обработке {dialog.name}: {str(e)}")
        print(f'Найдено {len(dialogs)} чатов по которым будет производиться поиск')
        for university in search_terms:
            print(f'Ищем упоминания вуза {university}')
            for term in search_terms[university]:
                print(f"Поиск терма в сообщениях: {term}")
                for dialog in dialogs:
                    async for message in self.client.iter_messages(
                        dialog.entity,  # Все диалоги/channels
                        limit=limit, # Сколько ищем
                        search=term,
                        filter=InputMessagesFilterEmpty()
                    ):
                        await self.process_message(message, search_terms, term)
                        await self.collect_message(message)


    async def collect_message(self, message):
        if hasattr(message, 'message'):
            self.data.append(message.message)


    async def process_message(self, message, search_terms, found_by_term):
        """Обработка и анализ найденного сообщения"""
        self.stats['total_posts'] += 1
        
        if hasattr(message, 'peer_id') and hasattr(message.peer_id, 'channel_id'):
            self.stats['unique_channels'].add(message.peer_id.channel_id)
        
        self.stats['views'] += getattr(message, 'views', 0) or 0
        self.stats['forwards'] += getattr(message, 'forwards', 0) or 0 
        replies = getattr(message, 'replies', 0)
        if replies and not isinstance(replies, int):
            self.stats['replies'] += replies.replies
        
        post_date = message.date.strftime('%Y-%m-%d')
        self.stats['posts_by_day'][post_date] += 1
        
        for university, aliases in search_terms.items():
            if found_by_term in aliases:
                self.stats['mentions'][university] += 1
    
    def get_statistics(self):
        """Получение собранной статистики"""
        stats = self.stats.copy()
        stats['unique_channels_count'] = len(stats['unique_channels'])
        mentions = list(stats['mentions'].items())
        

        stats_df = {
            'Метрика': [
                'Всего сообщений', 
                'Уникальных каналов', 
                'Просмотров', 
                'Репостов', 
                'Ответов',
                *(f'Упоминаний вуза {mention[0]}' for mention in mentions)
            ],
            'Значение': [
                stats['total_posts'],
                stats['unique_channels_count'],
                stats['views'],
                stats['forwards'],
                stats['replies'],
                *(mention[1] for mention in mentions)
            ]
        }

        stats_df = pd.DataFrame(stats_df)
        stats_df.to_csv('universities_posts_stats.csv', header=True, index=None)
        
        return stats_df
    
    def plot_statistics(self):
        """Визуализация статистики"""
        dates = sorted(self.stats['posts_by_day'].keys())
        counts = [self.stats['posts_by_day'][d] for d in dates]
        
        plt.figure(figsize=(12, 6))
        plt.bar(dates, counts)
        plt.title('Количество публикаций в Telegram по дням')
        plt.xlabel('Дата')
        plt.ylabel('Количество сообщений')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('publications_count.png')
        plt.show()

    def flush_crawled_data(self):
        df_data =pd.DataFrame({'message': self.data})
        df_data.to_csv('crawled_messages.csv', header=True, index=False)


async def main():
    
    API_ID = os.getenv('TELEGRAM_API_ID')
    API_HASH = os.getenv('TELEGRAM_API_HASH')
    client = TelegramClient(
            'universities_mentions_crawler',
            API_ID,
            API_HASH,
            device_model="Desktop",
            system_version="Windows 10",
            app_version="2.0",
            lang_code="en",
            system_lang_code="en-US"
        )
    analyzer = TelegramAnalyzer(client=client)
    
    await analyzer.search_messages(
        search_terms=__TERMS__,
        limit=10_000
    )
    
    stats = analyzer.get_statistics()
    print(stats)
    
    analyzer.plot_statistics()
    analyzer.flush_crawled_data()

if __name__ == "__main__":
    asyncio.run(main())