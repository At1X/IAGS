import logging, requests
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, ApplicationBuilder, filters, ConversationHandler
from decouple import config

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
SCORE = 1
base_api = config('BASE_API')
online_users = {}


async def start(update: Update, context):
    await update.message.reply_text("Hello!\nSend me solution ID and I'll send you solution\ntype /sol <solution_id> to get solution\nwhenever file sent to you, you can send its score.")
    log_msg = f"Started conversation with {update.message.from_user.full_name}"
    # write into logFile
    log_file = open("log.txt", "a")
    log_file.write(log_msg + "\n")
    log_file.close()

async def solution(update: Update, context):
    try:
        solution_id = context.args[0]
        online_users[update.message.from_user.id] = solution_id
    except:
        await update.message.reply_text("invalid input, write solution code infront of /sol")
        return ConversationHandler.END
    if int(online_users[update.message.from_user.id]) < 0:
        await update.message.reply_text("Sorry, negative solution ID's are not defined yet.")
        return ConversationHandler.END
    await update.message.reply_text(f"Solution ID: {online_users[update.message.from_user.id]}\nWait for solution...")
    response = requests.get(f"{base_api}fsm/answers/{online_users[update.message.from_user.id]}/", headers={
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': config('JWT_AUTH'),
    })
    if (response.status_code != 200):
        await update.message.reply_text("An unknown error occured. try again later, if doesnt work call +989900784322")
        return ConversationHandler.END
    await context.bot.send_document(chat_id=update.effective_chat.id, document=response.json()['answer_file'])
    myUser = update.message
    log_msg = f"Solution {online_users[update.message.from_user.id]} sent to Name: {myUser.from_user.first_name} LastName: {myUser.from_user.last_name}"

    # log into file
    log_file = open("log.txt", "a")
    log_file.write(log_msg + "\n")
    log_file.close()

    return SCORE

async def get_score(update: Update, context):
    user_input = update.message.text
    await update.message.reply_text(f"Your score is {user_input} for {online_users[update.message.from_user.id]}\nWait till server accept request.")
    try:
        response = requests.post(f"{base_api}scoring/set_answer_score/", headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': config('JWT_AUTH'),
        }, data={
            'answer_id': online_users[update.message.from_user.id],
            'score': user_input,
            'score_type_id': 4,
        })
        if (response.status_code == 200):
            await update.message.reply_text(f"🎉 Score sent to server!\nSaved.")
            log_msg = f"Saved score {user_input} for {online_users[update.message.from_user.id]} by {update.message.from_user.full_name}"

            # log into file
            log_file = open("log.txt", "a")
            log_file.write(log_msg + "\n")
            log_file.close()

            online_users.pop(update.message.from_user.id)

        else:
            await update.message.reply_text("An unknown error occured. try again later, if doesnt work call +989900784322")
    except:
        await update.message.reply_text(f"Failed to connect to server\nTry again...")

    return ConversationHandler.END

async def cancel(update: Update, context):
    user_input = update.message.text
    await update.message.reply_text(f"Canceled! Your score is {user_input}")
    return ConversationHandler.END

application = ApplicationBuilder().token(config('BOT_TOKEN')).build()

conv_handler = ConversationHandler(
        entry_points=[CommandHandler("sol", solution)],
        states={
            SCORE: [MessageHandler(filters.TEXT, get_score)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
start_handler = CommandHandler('start', start)

application.add_handler(start_handler)
application.add_handler(conv_handler)

application.run_polling()



