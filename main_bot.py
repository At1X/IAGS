import logging, requests
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, ApplicationBuilder, filters, ConversationHandler
from decouple import config

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
SCORE = 1
base_api = config('BASE_API')


async def solution(update: Update, context):
    global solution_id
    solution_id = context.args[0]
    if int(solution_id) < 0:
        await update.message.reply_text("Sorry, negative solution ID's are not defined yet.")
        return
    await update.message.reply_text(f"Solution ID: {solution_id}\nWait for solution...")
    response = requests.get(f"{base_api}fsm/answers/{solution_id}/", headers={
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': config('JWT_AUTH'),
    })
    await context.bot.send_document(chat_id=update.effective_chat.id, document=response.json()['answer_file'])
    myUser = update.message
    print(f"Solution {solution_id} sent to Name: {myUser.from_user.first_name} LastName: {myUser.from_user.last_name}")

    return SCORE

async def get_score(update: Update, context):
    user_input = update.message.text
    await update.message.reply_text(f"Done! Your score is {user_input} for {solution_id}")
    try:
        response = requests.post(f"{base_api}scoring/set_answer_score/", headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': config('JWT_AUTH'),
        }, data={
            'answer_id': solution_id,
            'score': user_input,
            'score_type_id': 4,
        })
        print(response)
        await update.message.reply_text(f"Score sent to server!\n")
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

application.add_handler(conv_handler)



application.run_polling()



