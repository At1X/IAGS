import logging, requests
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CallbackContext, MessageHandler, ApplicationBuilder, ConversationHandler, CommandHandler, filters
from decouple import config

#config
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
base_api = config('BASE_API')
online_users = {}
log_path = "Logs/log.txt"
store_users_path = "Logs/stored_users.txt"
GET_ID, LEVEL, SCORE = range(3)
GET_MESSAGE, CONFIRM = range(2)


def check_validation(id):
    user_file = open(store_users_path, "r")
    lines = user_file.readlines()
    for line in lines:
        if str(id) + '\n' == line:
            return True
    user_file.close()

async def start(update: Update, context):
    myText = "سلام کارسوقمند عزیز!\n تگ /sol را داخل چت بفرستید و تصحیح را با حداکثر سرعت شروع کنید! :)\nدر صورت مشاهده هرگونه اشکال در عملکرد ربات حتما با @blacktid در میان بگذارید."
    await update.message.reply_text(myText)
    log_msg = f"Started conversation with {update.message.from_user.full_name} and id: {update.message.from_user.id}"
    # write into logFile
    log_file = open(log_path, "a")
    log_file.write(log_msg + "\n")
    log_file.close()

async def solution(update: Update, context: CallbackContext.DEFAULT_TYPE) -> int:
    if not check_validation(update.message.from_user.id):
        await update.message.reply_text("حساب کاربری شما فعال نشده است، اگر فکر می‌کنید اشتباهی رخ داده با @blacktid در میان بگذارید.")
        return ConversationHandler.END
    await update.message.reply_text("شناسه سوالی که می‌خواهید تصحیح کنید را وارد کنید")
    return GET_ID

async def get_id(update: Update, context: CallbackContext.DEFAULT_TYPE) -> int:
    solution_id = update.message.text
    online_users[update.message.from_user.id] = {"solution_id": solution_id}
    if not online_users[update.message.from_user.id]["solution_id"].lstrip("-").isdigit():
        await update.message.reply_text("ورودی نامعتبر است، شناسه‌ ورودی را بصورت عددی بنویسید!")
        return ConversationHandler.END
    elif int(online_users[update.message.from_user.id]["solution_id"]) < 0:
        await update.message.reply_text("متاسفیم، شناسه نمی‌تونه عدد منفی باشه! :)")
        return ConversationHandler.END
    await update.message.reply_text("کمی صبر کنید")
    response = requests.get(f"{base_api}fsm/answers/{online_users[update.message.from_user.id]['solution_id']}/", headers={
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': config('JWT_AUTH'),
    })
    if (response.status_code != 200):
        await update.message.reply_text("اشکالی در ارتباط با سرور وجود دارد، با ۰۹۹۰۰۷۸۴۳۲۲ تماس بگیرید.")
        return ConversationHandler.END

    log_msg = f"Solution {online_users[update.message.from_user.id]['solution_id']} sent to {update.message.from_user.full_name} and id: {update.message.from_user.id}"
    await context.bot.send_document(
                                    chat_id=update.effective_chat.id,
                                    document=response.json()['answer_file'],
                                    reply_markup=ReplyKeyboardMarkup([['تصحیح اول','تصحیح دوم']], one_time_keyboard=True, resize_keyboard=True)
                                    )
    # log into file
    log_file = open(log_path, "a")
    log_file.write(log_msg + "\n")
    log_file.close()

    return LEVEL

async def level_identifier(update: Update, context: CallbackContext.DEFAULT_TYPE) -> int:
    if update.message.text == "تصحیح اول":
        online_users[update.message.from_user.id]["level"] = 4
    elif update.message.text == "تصحیح دوم":
        online_users[update.message.from_user.id]["level"] = 5
    else:
        await update.message.reply_text("ورودی نامعبر، دوباره امتحان کنید.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    await update.message.reply_text("نمره تصحیح را وارد کنید",reply_markup=ReplyKeyboardRemove())
    return SCORE

async def get_score(update: Update, context: CallbackContext.DEFAULT_TYPE) -> int:
    online_users[update.message.from_user.id]["score"] = update.message.text
    await update.message.reply_text(f"درحال ارسال به سرور\n لطفا مقداری صبر کنید")
    try:
        response = requests.post(f"{base_api}scoring/set_answer_score/", headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': config('JWT_AUTH'),
        }, data={
            'answer_id': online_users[update.message.from_user.id]["solution_id"],
            'score': online_users[update.message.from_user.id]["score"],
            'score_type_id': online_users[update.message.from_user.id]["level"],
        })
    except:
        response = 0
        await update.message.reply_text(f"اتصال به سرور ناموفق بود، مجددا تلاش کنید")
    if (response.status_code == 200):
        if online_users[update.message.from_user.id]["level"] == 4:
            level_ui = "Primary score"
        elif online_users[update.message.from_user.id]["level"] == 5:
            level_ui = "Secondary score"
        log_msg = f"{level_ui} {online_users[update.message.from_user.id]['score']} for {online_users[update.message.from_user.id]['solution_id']} by {update.message.from_user.full_name}"
        log_msg_for_telegram = log_msg + f"\nUsername: {update.message.from_user.username}\nID: {update.message.from_user.id}"
        await context.bot.send_message(chat_id=update.effective_chat.id, text=log_msg + "\n\n" + "درصورت مغایرت اطلاعات این پیام، فورا اطلاع دهید.")
        await context.bot.send_message(chat_id=config("EVENT_ADMIN"), text=log_msg_for_telegram)
        await update.message.reply_text(f"نمره با موفقیت ذخیره شد. 🎉")
        # log into file
        log_file = open(log_path, "a")
        log_file.write(log_msg + "\n")
        log_file.close()

        online_users.pop(update.message.from_user.id)

    else:
        await update.message.reply_text("اشکالی در ارتباط با سرور وجود دارد، با ۰۹۹۰۰۷۸۴۳۲۲ تماس بگیرید.")
        log_msg = f"Server error report: {update.message.from_user.full_name} typed: {online_users[update.message.from_user.id]['score']} for {online_users[update.message.from_user.id]['solution_id']}"


        # log into file
        log_file = open(log_path, "a")
        log_file.write(log_msg + "\n")
        log_file.close()

    return ConversationHandler.END

async def cancel(update: Update, context):
    user_input = update.message.text
    await update.message.reply_text(f"Canceled! Your score is {user_input}")
    return ConversationHandler.END

async def sendBackup(update: Update, context):
    password = context.args[0]
    if password == config('BACKUP_PASSWORD'):
        await context.bot.send_document(chat_id=config("EVENT_ADMIN"), document=open(log_path, 'rb'))
        await context.bot.send_document(chat_id=config("EVENT_ADMIN"), document=open(store_users_path, 'rb'))
    else:
        await update.message.reply_text("رمزعبور صحیح نیست.")

async def give_permission(update: Update, context):
    if str(update.message.from_user.id) == config('EVENT_ADMIN') or str(update.message.from_user.id) == config('BOT_ADMIN'):
        user_id = context.args[0]
        stored_users = open(store_users_path, 'a+')
        stored_users.write(f"{user_id}\n")
        stored_users.close()
        await update.message.reply_text("درخواست دسترسی با موفقیت انجام شد.")
    else:
        await update.message.reply_text("دسترسی شما برای انجام این کار مسدود می‌باشد!")
        return

async def send_message(update: Update, context):
    if str(update.message.from_user.id) == config('EVENT_ADMIN') or str(update.message.from_user.id) == config('BOT_ADMIN'):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="متن خود را وارد کنید")
        return GET_MESSAGE
    else:
        await update.message.reply_text("دسترسی شما برای انجام این کار مسدود می‌باشد!")
        return ConversationHandler.END

async def get_message(update: Update, context: CallbackContext.DEFAULT_TYPE):
    global text_message
    text_message = update.message.text
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Your message:\n{text_message}")
    await update.message.reply_text("پیام ارسال شود؟",
                                    reply_markup=ReplyKeyboardMarkup([["بله", "خیر"]],
                                    one_time_keyboard=True,
                                    resize_keyboard=True))

    return CONFIRM

async def get_message_confirm(update: Update, context: CallbackContext.DEFAULT_TYPE):
    confirm_message = update.message.text
    if confirm_message == "بله":
        users_file = open(store_users_path, "r")
        lines = users_file.readlines()
        for line in lines:
            user_id = line.strip()
            try:
                await context.bot.send_message(chat_id=user_id, text=text_message)
            except:
                print("Error sending message to user: " + user_id)
        await update.message.reply_text("پیام با موفقیت ارسال شد.",reply_markup=ReplyKeyboardRemove())
    else:
        await update.message.reply_text("پیام ارسال نشد.",reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

application = ApplicationBuilder().token(config('BOT_TOKEN')).build()

conv_handler = ConversationHandler(
        entry_points=[CommandHandler("sol", solution)],
        states={
            GET_ID: [
                MessageHandler(
                    filters.TEXT,
                    get_id,
                )
            ],
            LEVEL: [
                MessageHandler(
                    filters.TEXT,
                    level_identifier,
                )
            ],
            SCORE: [
                MessageHandler(
                    filters.TEXT,
                    get_score,
                )
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
send_message_handler = ConversationHandler(
        entry_points=[CommandHandler("send_message", send_message)],
        states={
            GET_MESSAGE: [
                MessageHandler(
                    filters.TEXT,
                    get_message,
                )
            ],
            CONFIRM: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND & filters.Regex("^(بله|خیر)$"),
                    get_message_confirm,
                )
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
)

start_handler = CommandHandler('start', start)
backup_handler = CommandHandler('backup', sendBackup)
give_permission_handler = CommandHandler('add', give_permission)

application.add_handler(start_handler)
application.add_handler(conv_handler)
application.add_handler(backup_handler)
application.add_handler(give_permission_handler)
application.add_handler(send_message_handler)

application.run_polling()

