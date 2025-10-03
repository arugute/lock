from pyrogram import Client
import asyncio
import time
from datetime import datetime

class GiftManager:
    def __init__(self, api_id, api_hash):
        self.api_id = api_id
        self.api_hash = api_hash
        self.processed_gifts = set()
    
    async def get_detailed_balance(self, app):
        """Получает детальную информацию о балансе и подарках"""
        try:
            # Получаем текущий баланс - исправленный метод
            balance_result = await app.get_stars_balance()
            balance = balance_result if isinstance(balance_result, int) else 0
            
            # Получаем информацию о подарках - исправленный метод
            gifts_generator = app.get_chat_gifts(chat_id="me")
            gifts = []
            async for gift in gifts_generator:
                gifts.append(gift)
            
            gift_count = len(gifts)
            
            # Анализируем подарки
            convertible_gifts = 0
            total_gift_value = 0
            gift_details = []
            
            for gift in gifts:
                gift_info = {
                    'id': getattr(gift, 'id', 'Unknown'),
                    'price': getattr(gift, 'price', 0),
                    'convert_price': getattr(gift, 'convert_price', 0),
                    'can_convert': hasattr(gift, 'convert_price') and gift.convert_price > 0
                }
                
                if gift_info['can_convert']:
                    convertible_gifts += 1
                    total_gift_value += gift_info['convert_price']
                
                gift_details.append(gift_info)
            
            return {
                'balance': balance,
                'gift_count': gift_count,
                'convertible_gifts': convertible_gifts,
                'total_gift_value': total_gift_value,
                'total_assets': balance + total_gift_value,
                'gift_details': gift_details,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            print(f"❌ Ошибка получения баланса: {e}")
            return None
    
    async def auto_sell_gifts(self, app):
        """Автоматически продает все полученные подарки"""
        try:
            print("🔍 Поиск новых подарков для продажи...")
            
            # Получаем текущие подарки - исправленный метод
            gifts_generator = app.get_chat_gifts(chat_id="me")
            gifts = []
            async for gift in gifts_generator:
                gifts.append(gift)
            
            if not gifts:
                print("📭 Нет полученных подарков")
                return 0
            
            total_earned = 0
            sold_count = 0
            new_gifts = 0
            
            for gift in gifts:
                try:
                    gift_id = getattr(gift, 'id', 'unknown')
                    
                    # Проверяем новый ли это подарок
                    if gift_id not in self.processed_gifts:
                        new_gifts += 1
                        self.processed_gifts.add(gift_id)
                        
                        # Проверяем можно ли конвертировать
                        if hasattr(gift, 'convert_price') and gift.convert_price > 0:
                            print(f"💰 Новый подарок! Продаем за {gift.convert_price} stars...")
                            
                            # Конвертируем подарок в Stars
                            result = await gift.convert()
                            total_earned += gift.convert_price
                            sold_count += 1
                            
                            print(f"✅ Подарок продан за {gift.convert_price} stars")
                            
                            # Пауза между операциями
                            await asyncio.sleep(2)
                        else:
                            print(f"📦 Получен подарок (нельзя продать)")
                    
                except Exception as e:
                    if "GIFT_ALREADY_CONVERTED" in str(e):
                        print("ℹ️ Подарок уже был продан ранее")
                        self.processed_gifts.add(gift_id)
                    else:
                        print(f"❌ Ошибка продажи подарка: {e}")
                    continue
            
            if sold_count > 0:
                print(f"🎯 Продано новых подарков: {sold_count}")
                print(f"💎 Заработано stars: {total_earned}")
            elif new_gifts > 0:
                print(f"📦 Получено {new_gifts} новых подарков (не для продажи)")
            else:
                print("✅ Новых подарков нет")
                
            return total_earned
            
        except Exception as e:
            print(f"❌ Ошибка в auto_sell_gifts: {e}")
            return 0
    
    async def send_gift_manual(self, app):
        """Ручная отправка подарка"""
        try:
            # Получаем текущий баланс
            status = await self.get_detailed_balance(app)
            if not status:
                return
            
            print(f"💰 Текущий баланс: {status['balance']} stars")
            
            # Получаем доступные подарки
            gifts = await app.get_available_gifts()
            print("\n🎁 Доступные подарки:")
            
            affordable_gifts = []
            for i, gift in enumerate(gifts[:10]):
                affordable = gift.price <= status['balance']
                marker = "✅" if affordable else "❌"
                print(f"{i+1}. {marker} {gift.price} stars")
                
                if affordable:
                    affordable_gifts.append((i, gift))
            
            if not affordable_gifts:
                print("❌ Недостаточно Stars для покупки подарков")
                return
            
            gift_index = int(input("Выбери номер подарка: ")) - 1
            selected_gift = gifts[gift_index]
            
            if selected_gift.price > status['balance']:
                print(f"❌ Недостаточно Stars! Нужно: {selected_gift.price}, есть: {status['balance']}")
                return
            
            recipient = input("Введите username получателя: ")
            
            print(f"🔄 Отправляем подарок за {selected_gift.price} stars...")
            
            # Отправляем подарок
            result = await app.send_gift(
                chat_id=recipient,
                gift_id=selected_gift.id
            )
            print("✅ Подарок успешно отправлен!")
            
            # Показываем новый баланс
            new_status = await self.get_detailed_balance(app)
            if new_status:
                print(f"💰 Новый баланс: {new_status['balance']} stars")
            
        except Exception as e:
            print(f"❌ Ошибка отправки подарка: {e}")
    
    async def display_status(self, app):
        """Отображает текущий статус баланса и подарков"""
        status = await self.get_detailed_balance(app)
        if status:
            print(f"\n📊 СТАТУС АККАУНТА [{status['timestamp']}]")
            print("=" * 40)
            print(f"💰 Баланс Stars: {status['balance']}")
            print(f"🎁 Всего подарков: {status['gift_count']}")
            print(f"💸 Можно продать: {status['convertible_gifts']}")
            print(f"📈 Стоимость подарков: {status['total_gift_value']} stars")
            print(f"💎 Общие активы: {status['total_assets']} stars")
            print("=" * 40)
            
            # Показываем детали подарков
            if status['gift_details']:
                print("\n📦 Детали подарков:")
                for i, gift in enumerate(status['gift_details'][:5]):
                    status_icon = "💸" if gift['can_convert'] else "🎁"
                    print(f"  {i+1}. {status_icon} Цена: {gift['price']} | Продажа: {gift['convert_price']} stars")
        else:
            print("❌ Не удалось получить статус аккаунта")
    
    async def auto_monitor(self, app, interval=30):
        """Автоматический мониторинг и продажа подарков"""
        print(f"🚀 Запуск автоматического монитора (интервал: {interval} сек)")
        print("⏹️  Нажмите Ctrl+C для остановки")
        
        try:
            while True:
                # Показываем статус
                await self.display_status(app)
                
                # Автоматически продаем подарки
                earned = await self.auto_sell_gifts(app)
                if earned > 0:
                    # Обновляем статус после продажи
                    print("\n🔄 Обновление статуса после продажи...")
                    await self.display_status(app)
                
                print(f"\n⏰ Следующая проверка через {interval} секунд...")
                await asyncio.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Автоматический монитор остановлен")
    
    async def run(self):
        """Основной цикл программы"""
        async with Client("my_account", api_id=self.api_id, api_hash=self.api_hash) as app:
            while True:
                print("\n" + "="*50)
                print("🤖 АВТОМАТИЧЕСКИЙ МЕНЕДЖЕР ПОДАРКОВ")
                print("="*50)
                
                # Показываем текущий статус
                await self.display_status(app)
                
                print("\n1️⃣ - Автоматически продать все подарки")
                print("2️⃣ - Отправить подарок")
                print("3️⃣ - Автоматический мониторинг (30 сек)")
                print("4️⃣ - Обновить статус")
                print("5️⃣ - Выйти")
                
                choice = input("\nВыберите действие: ")
                
                if choice == "1":
                    earned = await self.auto_sell_gifts(app)
                    if earned > 0:
                        print("\n🔄 Обновление статуса после продажи...")
                        await self.display_status(app)
                
                elif choice == "2":
                    await self.send_gift_manual(app)
                
                elif choice == "3":
                    await self.auto_monitor(app)
                
                elif choice == "4":
                    await self.display_status(app)
                
                elif choice == "5":
                    print("👋 Выход...")
                    break
                
                else:
                    print("❌ Неверный выбор")
                
                await asyncio.sleep(1)

# Запуск программы
if __name__ == "__main__":
    # Твои данные
    API_ID = 27437512
    API_HASH = '0182ac185d966c3dc8ac4ec256e27c8c'
    
    print("🚀 Запуск автоматического менеджера подарков...")
    manager = GiftManager(API_ID, API_HASH)
    asyncio.run(manager.run())