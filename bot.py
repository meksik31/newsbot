from aiogram import Bot, Dispatcher, executor, types
from aiogram.types.inline_keyboard import InlineKeyboardMarkup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from decouple import config
from updater import update
import time
import logging
import json
import asyncio

API_TOKEN = config('APIKEY')
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class Form(StatesGroup):
    ChoosingCategory = State()
    ChoosingNumber = State()
    IsDate = State()
    ChoosingDate = State()
    Showing = State()

@dp.message_handler(commands=['help'], state='*')
async def send_help(message: types.Message):
    await message.reply('Это новостной бот с разными категориями\nЧтобы выбрать категорию новостей напишите /choose')
    
@dp.message_handler(commands=['start', 'choose'], state='*')
async def send_menu(message: types.Message):
    await Form.ChoosingCategory.set()
    builder = InlineKeyboardMarkup()
    builder.add(types.InlineKeyboardButton(text='Финансы', callback_data='finance'), types.InlineKeyboardMarkup(text='Политика', callback_data='politics'), 
             types.InlineKeyboardButton(text='Наука', callback_data='science'), types.InlineKeyboardButton(text='Технологии', callback_data='techno'), 
             types.InlineKeyboardButton(text='Война', callback_data='war'), types.InlineKeyboardButton(text='Мир', callback_data='world'))
    await message.reply('Выберите категорию новостей', reply_markup=builder)
    
@dp.callback_query_handler(text=['finance', 'politics', 'science', 'techno', 'war', 'world'], state=Form.ChoosingCategory)
async def process_number(callback: types.CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
        data['category'] = callback.data
    await Form.ChoosingNumber.set()
    await callback.message.delete_reply_markup()
    await callback.message.edit_text('Введите количество новостей (от 1 до 10)')
    
@dp.message_handler(lambda message: not message.text.isdigit() or not int(message.text) in list(range(1, 11)), state=Form.ChoosingNumber)
async def process_invalid_number(message: types.Message):
    await message.answer('Количество новостей должно быть числом от 1 до 10')
    
    
@dp.message_handler(state=Form.ChoosingNumber)
async def ask_if_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['number'] = int(message.text)
    await Form.IsDate.set()
    builder = InlineKeyboardMarkup()
    builder.add(types.InlineKeyboardButton(text='Нет', callback_data='no'))
    await message.reply('Ищете новости за конкретную дату? Если да, введите её в чате', reply_markup=builder)
    
    
@dp.callback_query_handler(text='no', state=Form.IsDate)
async def show_result(callback: types.CallbackQuery, state: FSMContext):
    await Form.Showing.set()
    async with state.proxy() as data:
        try:
            with open(f'data/{data["category"]}.json', 'r') as file:
                news = json.loads(file.read())[:data['number']]
        except:
            await callback.message.answer('База данных обновляется, это может занять некоторое время')
            return
    for n in news:
        msg = f'<a href=\"{n["link"]}\">{n["title"]}</a> ({n["date"]})'
        await callback.message.answer_photo(n['image'], msg, parse_mode='HTML')
        time.sleep(3)

@dp.message_handler(state=Form.IsDate)
async def show_nodate_result(message: types.Message, state: FSMContext):
    await Form.Showing.set()
    async with state.proxy() as data:
        data['date'] = message.text
        try:
            with open(f'data/{data["category"]}.json', 'r') as file:
                news = json.loads(file.read())
                if [n for n in news if n['date'] == data['date']] != []:                   
                    news = [n for n in news if n['date'] == data['date']]
            news = news[:data['number']]
        except:
            message.answer('База данных обновляется, это может занять некоторое время')
            return
    for n in news:
        msg = f'<a href=\"{n["link"]}\">{n["title"]}</a> ({n["date"]})'
        await message.answer_photo(n['image'], msg, parse_mode='HTML')
        time.sleep(3)
        
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(update())
    executor.start_polling(dp, skip_updates=True)