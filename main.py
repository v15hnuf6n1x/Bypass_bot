from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BotCommand,
    Message,
)
from os import environ, remove
from threading import Thread
from json import load
from database.database import add_user, del_user, full_userbase, present_user
from re import search
from pyrogram import filters
from config import ADMINS, TOKEN, ID, HASH, DB_URL, DB_NAME
from helper_func import subscribed, encode, decode, get_messages
from database.database import add_user, del_user, full_userbase, present_user

from texts import HELP_TEXT
import bypasser
import freewall
from time import time
from db import DB


# bot
with open("config.json", "r") as f:
    DATA: dict = load(f)


def getenv(var):
    return environ.get(var) or DATA.get(var, None)


bot_token = getenv("TOKEN")
api_hash = getenv("HASH")
api_id = getenv("ID")
app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)
with app:
    app.set_bot_commands(
        [
            BotCommand("start", "Welcome Message"),
            BotCommand("help", "List of All Supported Sites"),
        ]
    )

# DB
db_uri = getenv("DB_URI")
db_name = getenv("DB_NAME")
try: database = DB(db_uri=db_owner, db_name=db_name)
except: 
    print("Database is Not Set")
    database = None


# handle index
def handleIndex(ele: str, message: Message, msg: Message):
    result = bypasser.scrapeIndex(ele)
    try:
        app.delete_messages(message.chat.id, msg.id)
    except:
        pass
    if database and result: database.insert(ele, result)
    for page in result:
        app.send_message(
            message.chat.id,
            page,
            reply_to_message_id=message.id,
            disable_web_page_preview=True,
        )


# loop thread
def loopthread(message: Message, otherss=False):

    urls = []
    if otherss:
        texts = message.caption
    else:
        texts = message.text

    if texts in [None, ""]:
        return
    for ele in texts.split():
        if "http://" in ele or "https://" in ele:
            urls.append(ele)
    if len(urls) == 0:
        return

    if bypasser.ispresent(bypasser.ddl.ddllist, urls[0]):
        msg: Message = app.send_message(
            message.chat.id, "⚡ __generating...__", reply_to_message_id=message.id
        )
    elif freewall.pass_paywall(urls[0], check=True):
        msg: Message = app.send_message(
            message.chat.id, "🕴️ __jumping the wall...__", reply_to_message_id=message.id
        )
    else:
        if "https://olamovies" in urls[0] or "https://psa.wf/" in urls[0]:
            msg: Message = app.send_message(
                message.chat.id,
                "⏳ __this might take some time...__",
                reply_to_message_id=message.id,
            )
        else:
            msg: Message = app.send_message(
                message.chat.id, "🔎 __bypassing...__", reply_to_message_id=message.id
            )

    strt = time()
    links = ""
    temp = None

    for ele in urls:
        if database: df_find = database.find(ele)
        else: df_find = None
        if df_find:
            print("Found in DB")
            temp = df_find
        elif search(r"https?:\/\/(?:[\w.-]+)?\.\w+\/\d+:", ele):
            handleIndex(ele, message, msg)
            return
        elif bypasser.ispresent(bypasser.ddl.ddllist, ele):
            try:
                temp = bypasser.ddl.direct_link_generator(ele)
            except Exception as e:
                temp = "**Error**: " + str(e)
        elif freewall.pass_paywall(ele, check=True):
            freefile = freewall.pass_paywall(ele)
            if freefile:
                try:
                    app.send_document(
                        message.chat.id, freefile, reply_to_message_id=message.id
                    )
                    remove(freefile)
                    app.delete_messages(message.chat.id, [msg.id])
                    return
                except:
                    pass
            else:
                app.send_message(
                    message.chat.id, "__Failed to Jump", reply_to_message_id=message.id
                )
        else:
            try:
                temp = bypasser.shortners(ele)
            except Exception as e:
                temp = "**Error**: " + str(e)

        print("bypassed:", temp)
        if temp != None:
            if (not df_find) and ("http://" in temp or "https://" in temp) and database:
                print("Adding to DB")
                database.insert(ele, temp)
            links = links + temp + "\n"

    end = time()
    print("Took " + "{:.2f}".format(end - strt) + "sec")

    if otherss:
        try:
            app.send_photo(
                message.chat.id,
                message.photo.file_id,
                f"__{links}__",
                reply_to_message_id=message.id,
            )
            app.delete_messages(message.chat.id, [msg.id])
            return
        except:
            pass

    try:
        final = []
        tmp = ""
        for ele in links.split("\n"):
            tmp += ele + "\n"
            if len(tmp) > 4000:
                final.append(tmp)
                tmp = ""
        final.append(tmp)
        app.delete_messages(message.chat.id, msg.id)
        tmsgid = message.id
        for ele in final:
            tmsg = app.send_message(
                message.chat.id,
                f"__{ele}__",
                reply_to_message_id=tmsgid,
                disable_web_page_preview=True,
            )
            tmsgid = tmsg.id
    except Exception as e:
        app.send_message(
            message.chat.id,
            f"__Failed to Bypass : {e}__",
            reply_to_message_id=message.id,
        )


# start command
@app.on_message(filters.command('start') & filters.private & subscribed)
asyncdef send_start(client: Client, message: Message):
    id = message.from_user_id
    if not await present_user(id):
        try:
            await add_user(id)
        except:
            pass
    app.send_message(
        message.chat.id,
        f"__👋 Hi **{message.from_user.mention}**, I am Link Bypasser Bot, just send me any supported links and i will you get you results.\nCheckout /help to Read More__",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🌐About",callback_data = "about",)],
                [InlineKeyboardButton("🔔Updates",url="https://t.me/mr_v_bots",)],
                [InlineKeyboardButton("Close",callback_data = "close")]
            ]
        ),
        await reply_to_message_id=message.id,
    )

@app.on_callback_query()
async def close_keyboard(client, callback_query):
    if callback_query.data == "about":
        await callback_query.message.edit_text(
            text = f"<b>✑ Cʀᴇᴀᴛᴏʀ👨‍💻 :<a href='https://t.me/user?id={OWNER_ID}'>Tʜɪs Gᴜʏ</a>\n✑ Lᴀɴɢᴜᴀɢᴇ🗄 :<a>Pʏᴛʜᴏɴ</a>\n✑ Lɪʙʀᴀʀʏ🗃 : <a>Pʏʀᴏɢʀᴀᴍ</a>\n✑ Sᴏᴜʀᴄᴇ Cᴏᴅᴇ📄 : <a href='https://t.me/v15hnuf6n1x'>Gᴇᴛ Hᴇʀᴇ</a>\n✑ Dᴇᴠ🪛 : <a href='https://t.me/Mr_V_bots'>Mʀ.V Bᴏᴛs</a></b>",
            disable_web_page_preview = True)
    elif callback_query.data == "close":
        await callback_query.message.edit_reply_markup(reply_markup=None)
        await callback_query.message.delete()

# help command
@app.on_message(filters.command('help') & filters.private & subscribed)
async def send_help(
    client: Client,
    message: Message,
):
    app.send_message(
        message.chat.id,
        HELP_TEXT,
        reply_to_message_id=message.id,
        disable_web_page_preview=True,
    )


# links
@app.on_message(filters.text & filters.private & subscribed)
def receive(
    client: Client,
    message: Message,
):
    bypass = Thread(target=lambda: loopthread(message), daemon=True)
    bypass.start()


# doc thread
def docthread(message: Message):
    msg: Message = app.send_message(
        message.chat.id, "🔎 __bypassing...__", reply_to_message_id=message.id
    )
    print("sent DLC file")
    file = app.download_media(message)
    dlccont = open(file, "r").read()
    links = bypasser.getlinks(dlccont)
    app.edit_message_text(
        message.chat.id, msg.id, f"__{links}__", disable_web_page_preview=True
    )
    remove(file)


# files
@app.on_message([filters.document, filters.photo, filters.video])
def docfile(
    client: Client,
    message: Message,
):

    try:
        if message.document.file_name.endswith("dlc"):
            bypass = Thread(target=lambda: docthread(message), daemon=True)
            bypass.start()
            return
    except:
        pass

    bypass = Thread(target=lambda: loopthread(message, True), daemon=True)
    bypass.start()


# server loop
print("Bot Starting")
app.run()
