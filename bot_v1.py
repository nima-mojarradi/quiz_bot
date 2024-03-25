from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os, psycopg2
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
import psycopg2, json, requests, time
import random
from dotenv import load_dotenv
import telegram


load_dotenv()

TOKEN = os.environ.get('MAIN_BOT')

USER = os.environ.get('USER')
PASSWORD = os.environ.get('PASSWORD')
DATABASE_NAME = os.environ.get('DATABASE_NAME')
DATABASE_SERVER = os.environ.get('DATABASE_SERVER')
DATABASE_PORT = os.environ.get('DATABASE_PORT')

BOT = telegram.Bot(token=TOKEN)

BASE_QUIZ_URL = f'https://api.telegram.org/bot{TOKEN}/sendPoll'

url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
request = requests.get(url=url).json



score = 0

connection = psycopg2.connect(dbname=DATABASE_NAME, password=PASSWORD, user=USER)
cursor = connection.cursor()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"{update.effective_user.username} عزیز خوش آمدید \n امتیاز حال حاضر شما 0 است \n شروع بازی با ربات -> /quiz_with_bot")

async def message_for_playing(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'برای بازی کردن با ربات قوانینی وجود دارد: \n 1)کوییز سه تا سوال دارد \n 2)اگر برنده بازی شوید 3 امتیاز میگیرید \n 3) اگر بازی مساوی به اتمام برسد 1 امتیاز کسب میکنید \n 4)اگر در بازی شکست بخورید و باخت دهید 2 امتیاز از دست میدهید \n اگر آماده شروع هستید بر روی /ready بزنید')
    
    
async def get_categories(update, context):
    categories = []
    try:
        cursor = connection.cursor()
        query = "SELECT title FROM category"
        cursor.execute(query)
        records = cursor.fetchall()
        for row in records:
            categories.append(row[0])
        keyboard = [
                    [InlineKeyboardButton(f'{category}', callback_data=f'{category}')]
                    for category in categories
                ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('What is your favorite category?', reply_markup=reply_markup)
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)

async def handle_category_selection(update: Update, context: CallbackContext):
    category_name = update.callback_query.data
    id_chat = update.callback_query.message.chat_id
    id_message = update.callback_query.message.message_id
    await update.callback_query.answer(f"You selected the category: {category_name}")
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM questions WHERE category = %s', (category_name,))
    category_questions = cursor.fetchall()
    random.shuffle(category_questions)
    selected_questions = category_questions[:3]
    for i in range(3):
        question = selected_questions[i][4]
        question_id = selected_questions[i][3]
        cursor.execute(f'SELECT * FROM options WHERE question_id = {question_id}')
        options = cursor.fetchall()  
        correct_option_index = int(json.dumps(options[0][2]))
        list_of_options = json.dumps(options[0][1])
        print(len(category_questions))
        print(options)
        print(options[0][2])
        print(correct_option_index)
        data = {
            'chat_id': id_chat,
            'question': question,
            'options': list_of_options,
            'type': 'quiz',
            'correct_option_id': list_of_options[correct_option_index],
            'is_anonymous':False
        }
        resp=requests.get(BASE_QUIZ_URL, data=data).json()
        message_id = resp['result']['message_id']
        print(message_id)
        time.sleep(10)
        await BOT.stop_poll(id_chat,message_id)
    

token = os.getenv('TOKEN', TOKEN)
app = ApplicationBuilder().token(token).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("quiz_with_bot", message_for_playing))
app.add_handler(CommandHandler("ready", get_categories))
app.add_handler(CallbackQueryHandler(handle_category_selection))
app.run_polling()
