#!/usr/bin/env python
# -*- coding: utf-8 -*-

# بوت النشر التلقائي الاحترافي
# المطور: @Motazalkade
# القناة: @enmotaz

from flask import Flask
import threading

app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

threading.Thread(target=run_flask).start()

import os
from telethon.sessions import StringSession
import asyncio
from kvsqlite.sync import Client as uu
from telethon import TelegramClient, events, Button
import random
from datetime import datetime, timedelta
from telethon.errors import FloodWaitError, SessionPasswordNeededError
from telethon.tl.functions.channels import JoinChannelRequest, GetParticipantRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest
from telethon.errors.rpcerrorlist import UserNotParticipantError

if not os.path.isdir('database'):
    os.makedirs('database')

# ========== بياناتك الشخصية ==========
API_ID = 35983238
API_HASH = "daf2ef391f5d9017043b33f4d1f84052"
BOT_TOKEN = "8954040848:AAGZ4DMXjk9HmHU7WJt-ZXo7h2o7EkqDkx4"
ADMIN_ID = 5517628630
ADMIN_USERNAME = "Motazalkade"
REQUIRED_CHANNEL = "enmotaz"
# ====================================

client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
db = uu('database/bot_data.ss', 'bot')

# ========== تهيئة قاعدة البيانات (بدون أخطاء) ==========
if not db.exists("users"):
    db.set("users", {})
if not db.exists("accounts_settings"):
    db.set("accounts_settings", {})
if not db.exists("memberships"):
    db.set("memberships", {})
if not db.exists("pending_requests"):
    db.set("pending_requests", {})
if not db.exists("admins"):
    db.set("admins", [ADMIN_ID])
if not db.exists("bot_enabled"):
    db.set("bot_enabled", True)

# دالة مساعدة لقراءة البيانات بأمان
def get_data(key, default=None):
    if db.exists(key):
        return db.get(key)
    return default or {}

# ========== رسائل البوت ==========
MAIN_MENU = """
╔══════════════════════════════════════════════════════╗
║     🔥 بوت النشر التلقائي - الإصدار الاحترافي 🔥     ║
╚══════════════════════════════════════════════════════╝

🚀 أرسل رسالتك مرة واحدة فقط والبوت ينشرها تلقائياً

📖 **طريقة الاستخدام:**
[1] اضغط ➕ إضافة حساب
[2] أدخل رقم هاتفك مع رمز الدولة
[3] أدخل كود التحقق
[4] اذهب إلى 📤 إدارة الحسابات
[5] اختر حسابك ثم عين الكليشة والفاصل
[6] اضغط ✅ تفعيل النشر

👨‍💻 **المطور:** @Motazalkade
📢 **القناة:** @enmotaz
"""

ADMIN_PANEL = """
👑 **لوحة تحكم المشرف**

📊 إحصائيات:
👥 المستخدمين: {}
📱 الحسابات: {}
💎 المميزين: {}
⏳ طلبات الانتظار: {}
"""

NO_SUBSCRIPTION = "⚠️ هذا البوت للاشتراك فقط\nللاشتراك، اضغط على زر الاشتراك أدناه"
SUBSCRIBE_REQUEST_SENT = "✅ تم إرسال طلب اشتراكك للمشرف"
SUBSCRIBE_APPROVED = "🎉 تم تفعيل اشتراكك لمدة {} يوم!"
SUBSCRIBE_DENIED = "❌ تم رفض طلب الاشتراك"

# ========== دوال التحقق ==========
async def is_admin(user_id):
    return user_id == ADMIN_ID

async def check_subscription(user_id):
    if user_id == ADMIN_ID:
        return True
    memberships = get_data("memberships")
    user_sub = memberships.get(str(user_id), {})
    if user_sub.get("active", False):
        expiry = user_sub.get("expiry")
        if expiry and datetime.now().timestamp() > expiry:
            memberships.pop(str(user_id), None)
            db.set("memberships", memberships)
            return False
        return True
    return False

async def is_user_member(user_id):
    if not REQUIRED_CHANNEL:
        return True
    try:
        channel_entity = await client.get_entity(f"t.me/{REQUIRED_CHANNEL}")
        await client(GetParticipantRequest(channel=channel_entity, participant=user_id))
        return True
    except:
        return False

# ========== النشر التلقائي ==========
async def auto_post_loop(user_id, phone, session_str):
    acc_key = f"acc_{phone}"
    print(f"🔄 بدء النشر التلقائي للحساب {phone}")
    
    while True:
        if not db.get("bot_enabled"):
            await asyncio.sleep(10)
            continue
        
        settings = get_data("accounts_settings")
        acc_settings = settings.get(acc_key, {})
        
        if not acc_settings.get("enabled", False):
            print(f"⏹️ إيقاف النشر للحساب {phone}")
            break
        
        post_msg = acc_settings.get("message", "مرحباً")
        interval = max(acc_settings.get("interval", 120), 30)
        
        try:
            temp = TelegramClient(StringSession(session_str), API_ID, API_HASH)
            await temp.connect()
            
            if not await temp.is_user_authorized():
                print(f"❌ الحساب {phone} غير مصرح")
                await temp.disconnect()
                break
            
            dialogs = await temp.get_dialogs()
            groups = [d for d in dialogs if d.is_group]
            
            if groups:
                random.shuffle(groups)
                for group in groups[:30]:
                    settings = get_data("accounts_settings")
                    if not settings.get(acc_key, {}).get("enabled", False):
                        break
                    try:
                        await temp.send_message(group.entity, post_msg)
                        print(f"✅ {phone}: تم النشر في {group.name}")
                        await asyncio.sleep(random.uniform(3, 7))
                    except FloodWaitError as e:
                        await asyncio.sleep(e.seconds)
                    except:
                        await asyncio.sleep(5)
            
            await temp.disconnect()
            
            for _ in range(interval):
                await asyncio.sleep(1)
                settings = get_data("accounts_settings")
                if not settings.get(acc_key, {}).get("enabled", False):
                    break
                    
        except Exception as e:
            print(f"❌ خطأ في حساب {phone}: {e}")
            await asyncio.sleep(60)

# ========== لوحة المشرف ==========
async def admin_menu():
    users = get_data("users")
    real_users = sum(1 for k in users.keys() if k.isdigit())
    accounts = sum(len(u.get("accounts", [])) for u in users.values())
    premium = len(get_data("memberships"))
    pending = len(get_data("pending_requests"))
    
    text = ADMIN_PANEL.format(real_users, accounts, premium, pending)
    buttons = [
        [Button.inline("📊 الإحصائيات", b"stats")],
        [Button.inline("👥 المستخدمين", b"user_list"), Button.inline("💎 المميزين", b"premium_list")],
        [Button.inline("⏳ طلبات الاشتراك", b"show_pending")],
        [Button.inline("➕ ترقية عضوية", b"upgrade"), Button.inline("➖ إزالة عضوية", b"remove")],
        [Button.inline("📢 إذاعة", b"broadcast"), Button.inline("📤 نشر جماعي", b"mass_post")],
        [Button.inline("🔛 تعطيل البوت", b"disable")]
    ]
    await client.send_message(ADMIN_ID, text, buttons=buttons)

# ========== أمر /start ==========
@client.on(events.NewMessage(pattern="/start", func=lambda x: x.is_private))
async def start_cmd(event):
    user_id = event.chat_id
    
    if not await is_user_member(user_id):
        return await event.respond(f"⚠️ يجب عليك الانضمام إلى قناتنا أولاً\n@{REQUIRED_CHANNEL}")
    
    if not await check_subscription(user_id):
        buttons = [[Button.inline("💎 طلب اشتراك", b"request_sub")]]
        return await event.respond(NO_SUBSCRIPTION, buttons=buttons)
    
    users = get_data("users")
    accounts = users.get(str(user_id), {}).get("accounts", [])
    has_account = len(accounts) > 0
    
    buttons = [
        [Button.inline(f"📱 الحساب : {'✅' if has_account else '❌'}", b"none")],
        [Button.inline("➕ إضافة حساب", b"add_account")],
        [Button.inline("📤 إدارة الحسابات", b"manage_accounts")],
        [Button.inline("🔗 انضمام لمجموعة", b"join_section")],
        [Button.inline("💎 طلب اشتراك", b"request_sub")]
    ]
    
    await event.respond(MAIN_MENU, buttons=buttons)
    
    if await is_admin(user_id):
        await admin_menu()

# ========== طلب اشتراك ==========
@client.on(events.CallbackQuery(data=b"request_sub"))
async def request_subscription(event):
    user_id = event.chat_id
    if await is_admin(user_id):
        return await event.answer("أنت المشرف!", alert=True)
    
    pending = get_data("pending_requests")
    if str(user_id) in pending:
        return await event.answer("لديك طلب قيد الانتظار", alert=True)
    
    user = await event.get_sender()
    pending[str(user_id)] = {
        "name": user.first_name or "مستخدم",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    db.set("pending_requests", pending)
    
    await client.send_message(
        ADMIN_ID,
        f"🆕 **طلب اشتراك جديد!**\n👤 {pending[str(user_id)]['name']}\n🆔 `{user_id}`",
        buttons=[[Button.inline("✅ قبول", f"accept_{user_id}".encode()), Button.inline("❌ رفض", f"reject_{user_id}".encode())]]
    )
    await event.edit(SUBSCRIBE_REQUEST_SENT)

# ========== قبول اشتراك ==========
@client.on(events.CallbackQuery(data=lambda x: x and x.startswith(b"accept_")))
async def accept_subscription(event):
    if not await is_admin(event.chat_id):
        return
    
    user_id = int(event.data.decode().split("_")[1])
    await event.edit(f"✅ قبول طلب `{user_id}`\n📅 أرسل عدد الأيام:")
    
    @client.on(events.NewMessage(incoming=True, from_users=ADMIN_ID))
    async def get_days(msg):
        client.remove_event_handler(get_days)
        try:
            days = int(msg.text)
            memberships = get_data("memberships")
            memberships[str(user_id)] = {"active": True, "expiry": (datetime.now() + timedelta(days=days)).timestamp()}
            db.set("memberships", memberships)
            
            pending = get_data("pending_requests")
            pending.pop(str(user_id), None)
            db.set("pending_requests", pending)
            
            await client.send_message(user_id, SUBSCRIBE_APPROVED.format(days))
            await event.reply(f"✅ تم تفعيل اشتراك `{user_id}` لـ {days} يوم")
            await admin_menu()
        except:
            await event.reply("⚠️ أرسل رقماً صحيحاً")

# ========== رفض اشتراك ==========
@client.on(events.CallbackQuery(data=lambda x: x and x.startswith(b"reject_")))
async def reject_subscription(event):
    if not await is_admin(event.chat_id):
        return
    
    user_id = int(event.data.decode().split("_")[1])
    pending = get_data("pending_requests")
    pending.pop(str(user_id), None)
    db.set("pending_requests", pending)
    await client.send_message(user_id, SUBSCRIBE_DENIED)
    await event.edit(f"✅ تم رفض طلب `{user_id}`")

# ========== إضافة حساب ==========
@client.on(events.CallbackQuery(data=b"add_account"))
async def add_account(event):
    user_id = event.chat_id
    async with client.conversation(user_id) as conv:
        await conv.send_message("📱 أرسل رقم الهاتف مع رمز الدولة\nمثال: +966512345678")
        phone = (await conv.get_response()).text.replace("+", "").replace(" ", "")
        
        await conv.send_message("🔄 جاري إرسال كود التحقق...")
        temp = TelegramClient(StringSession(), API_ID, API_HASH)
        await temp.connect()
        await temp.send_code_request(phone)
        
        await conv.send_message("📝 أرسل كود التحقق")
        code = (await conv.get_response()).text.replace(" ", "")
        
        try:
            await temp.sign_in(phone, code)
            session_str = temp.session.save()
            await temp.disconnect()
            
            users = get_data("users")
            user_data = users.get(str(user_id), {"accounts": []})
            
            if any(a["phone"] == phone for a in user_data["accounts"]):
                await conv.send_message(f"⚠️ الحساب {phone} مضاف مسبقاً")
                return
            
            user_data["accounts"].append({"phone": phone, "session": session_str})
            users[str(user_id)] = user_data
            db.set("users", users)
            await conv.send_message(f"✅ تم إضافة الحساب {phone}")
        except Exception as e:
            await conv.send_message(f"❌ خطأ: {str(e)[:100]}")

# ========== إدارة الحسابات ==========
@client.on(events.CallbackQuery(data=b"manage_accounts"))
async def manage_accounts(event):
    user_id = event.chat_id
    users = get_data("users")
    accounts = users.get(str(user_id), {}).get("accounts", [])
    
    if not accounts:
        return await event.answer("❌ لا توجد حسابات! أضف حساباً أولاً", alert=True)
    
    buttons = []
    for acc in accounts:
        phone = acc["phone"]
        settings = get_data("accounts_settings")
        acc_settings = settings.get(f"acc_{phone}", {})
        status = "✅" if acc_settings.get("enabled") else "❌"
        buttons.append([Button.inline(f"{status} {phone}", f"manage_acc_{phone}".encode())])
    
    buttons.append([Button.inline("➕ إضافة حساب جديد", b"add_account")])
    buttons.append([Button.inline("🔙 رجوع", b"back_main")])
    
    await event.edit("📤 اختر حساباً للتحكم فيه:", buttons=buttons)

# ========== إدارة حساب فردي ==========
@client.on(events.CallbackQuery(data=lambda x: x and x.startswith(b"manage_acc_")))
async def manage_single_account(event):
    phone = event.data.decode().split("_")[2]
    user_id = event.chat_id
    
    users = get_data("users")
    accounts = users.get(str(user_id), {}).get("accounts", [])
    account = next((a for a in accounts if a["phone"] == phone), None)
    
    if not account:
        return await event.answer("❌ الحساب غير موجود", alert=True)
    
    settings = get_data("accounts_settings")
    acc_settings = settings.get(f"acc_{phone}", {})
    
    if 'enabled' not in acc_settings: acc_settings['enabled'] = False
    if 'message' not in acc_settings: acc_settings['message'] = "مرحباً"
    if 'interval' not in acc_settings: acc_settings['interval'] = 30
    
    status = "✅ مفعل" if acc_settings['enabled'] else "❌ معطل"
    
    buttons = [
        [Button.inline("📋 جلب المجموعات", f"get_groups_{phone}".encode())],
        [Button.inline("✏️ تعيين الكليشة", f"set_msg_{phone}".encode())],
        [Button.inline("⏱ تعيين الفاصل", f"set_int_{phone}".encode())],
        [Button.inline("🔄 تفعيل/تعطيل", f"toggle_{phone}".encode())],
        [Button.inline("🗑 حذف الحساب", f"delete_acc_{phone}".encode())],
        [Button.inline("🔙 رجوع", b"manage_accounts")]
    ]
    
    msg = f"📱 **{phone}**\n📊 حالة النشر: {status}\n⏱ الفاصل: {acc_settings['interval']} ثانية"
    await event.edit(msg, buttons=buttons)

# ========== جلب المجموعات ==========
@client.on(events.CallbackQuery(data=lambda x: x and x.startswith(b"get_groups_")))
async def get_groups(event):
    phone = event.data.decode().split("_")[2]
    user_id = event.chat_id
    
    users = get_data("users")
    accounts = users.get(str(user_id), {}).get("accounts", [])
    account = next((a for a in accounts if a["phone"] == phone), None)
    
    if not account:
        return await event.answer("❌ الحساب غير موجود", alert=True)
    
    await event.edit("🔄 جاري جلب المجموعات...")
    try:
        temp = TelegramClient(StringSession(account["session"]), API_ID, API_HASH)
        await temp.connect()
        dialogs = await temp.get_dialogs()
        groups = [d for d in dialogs if d.is_group]
        await temp.disconnect()
        
        if not groups:
            return await event.edit("⚠️ لا توجد مجموعات", buttons=[[Button.inline("🔙 رجوع", f"manage_acc_{phone}".encode())]])
        
        msg = f"📋 **قائمة المجموعات**\n📞 {phone}\n📊 العدد: {len(groups)}\n\n"
        for i, g in enumerate(groups[:30], 1):
            msg += f"{i}. {g.name}\n🆔 `{g.id}`\n\n"
        
        await event.edit(msg, buttons=[[Button.inline("🔙 رجوع", f"manage_acc_{phone}".encode())]])
    except Exception as e:
        await event.edit(f"❌ خطأ: {str(e)[:100]}", buttons=[[Button.inline("🔙 رجوع", f"manage_acc_{phone}".encode())]])

# ========== تعيين الكليشة ==========
@client.on(events.CallbackQuery(data=lambda x: x and x.startswith(b"set_msg_")))
async def set_message(event):
    phone = event.data.decode().split("_")[2]
    await event.edit("✏️ أرسل الكليشة الجديدة", buttons=[[Button.inline("إلغاء", f"manage_acc_{phone}".encode())]])
    
    @client.on(events.NewMessage(incoming=True, from_users=event.chat_id))
    async def save_msg(msg):
        client.remove_event_handler(save_msg)
        settings = get_data("accounts_settings")
        settings[f"acc_{phone}"] = settings.get(f"acc_{phone}", {})
        settings[f"acc_{phone}"]["message"] = msg.text
        db.set("accounts_settings", settings)
        await msg.reply(f"✅ تم حفظ الكليشة", buttons=[[Button.inline("🔙 رجوع", f"manage_acc_{phone}".encode())]])

# ========== تعيين الفاصل ==========
@client.on(events.CallbackQuery(data=lambda x: x and x.startswith(b"set_int_")))
async def set_interval(event):
    phone = event.data.decode().split("_")[2]
    await event.edit("⏱ أرسل الفاصل الزمني (30-300 ثانية)", buttons=[[Button.inline("إلغاء", f"manage_acc_{phone}".encode())]])
    
    @client.on(events.NewMessage(incoming=True, from_users=event.chat_id))
    async def save_int(msg):
        client.remove_event_handler(save_int)
        try:
            interval = max(30, min(300, int(msg.text)))
            settings = get_data("accounts_settings")
            settings[f"acc_{phone}"] = settings.get(f"acc_{phone}", {})
            settings[f"acc_{phone}"]["interval"] = interval
            db.set("accounts_settings", settings)
            await msg.reply(f"✅ تم تعيين الفاصل {interval} ثانية", buttons=[[Button.inline("🔙 رجوع", f"manage_acc_{phone}".encode())]])
        except:
            await msg.reply("⚠️ أرسل رقماً صحيحاً")

# ========== تفعيل/تعطيل النشر ==========
@client.on(events.CallbackQuery(data=lambda x: x and x.startswith(b"toggle_")))
async def toggle_post(event):
    phone = event.data.decode().split("_")[1]
    user_id = event.chat_id
    
    settings = get_data("accounts_settings")
    acc_settings = settings.get(f"acc_{phone}", {"enabled": False})
    new_state = not acc_settings.get("enabled", False)
    
    settings[f"acc_{phone}"] = acc_settings
    settings[f"acc_{phone}"]["enabled"] = new_state
    db.set("accounts_settings", settings)
    
    if new_state:
        users = get_data("users")
        accounts = users.get(str(user_id), {}).get("accounts", [])
        account = next((a for a in accounts if a["phone"] == phone), None)
        if account:
            asyncio.create_task(auto_post_loop(user_id, phone, account["session"]))
            await event.answer(f"✅ تم تفعيل النشر للحساب {phone}")
    else:
        await event.answer(f"⏹️ تم إيقاف النشر للحساب {phone}")
    
    await manage_single_account(event)

# ========== حذف حساب ==========
@client.on(events.CallbackQuery(data=lambda x: x and x.startswith(b"delete_acc_")))
async def delete_account(event):
    phone = event.data.decode().split("_")[2]
    user_id = event.chat_id
    
    settings = get_data("accounts_settings")
    if settings.get(f"acc_{phone}", {}).get("enabled"):
        settings[f"acc_{phone}"]["enabled"] = False
        db.set("accounts_settings", settings)
    
    users = get_data("users")
    user_data = users.get(str(user_id), {})
    user_data["accounts"] = [a for a in user_data.get("accounts", []) if a["phone"] != phone]
    users[str(user_id)] = user_data
    db.set("users", users)
    
    await event.answer("✅ تم حذف الحساب", alert=True)
    await manage_accounts(event)

# ========== انضمام لمجموعة ==========
@client.on(events.CallbackQuery(data=b"join_section"))
async def join_section(event):
    user_id = event.chat_id
    users = get_data("users")
    accounts = users.get(str(user_id), {}).get("accounts", [])
    
    if not accounts:
        return await event.answer("❌ لا توجد حسابات", alert=True)
    
    buttons = [[Button.inline(f"📱 {a['phone']}", f"join_with_{a['phone']}".encode())] for a in accounts]
    buttons.append([Button.inline("🔙 رجوع", b"back_main")])
    await event.edit("🔗 اختر الحساب للانضمام:", buttons=buttons)

@client.on(events.CallbackQuery(data=lambda x: x and x.startswith(b"join_with_")))
async def join_with_account(event):
    phone = event.data.decode().split("_")[2]
    user_id = event.chat_id
    
    users = get_data("users")
    accounts = users.get(str(user_id), {}).get("accounts", [])
    account = next((a for a in accounts if a["phone"] == phone), None)
    
    if not account:
        return await event.answer("❌ الحساب غير موجود", alert=True)
    
    await event.edit("🔗 أرسل الروابط (كل رابط في سطر)\n\nثم أرسل وقت الانتظار")
    
    @client.on(events.NewMessage(incoming=True, from_users=user_id))
    async def get_links(msg):
        client.remove_event_handler(get_links)
        links = [l.strip() for l in msg.text.split('\n') if l.strip()]
        await event.edit("⏱ أرسل وقت الانتظار (5-30 ثانية)")
        
        @client.on(events.NewMessage(incoming=True, from_users=user_id))
        async def get_wait(w):
            client.remove_event_handler(get_wait)
            wait = max(5, min(30, int(w.text) if w.text.isdigit() else 10))
            await event.edit(f"🔄 جاري الانضمام إلى {len(links)} رابط...")
            success, failed = 0, 0
            
            for link in links:
                try:
                    temp = TelegramClient(StringSession(account["session"]), API_ID, API_HASH)
                    await temp.connect()
                    
                    if 't.me/joinchat/' in link or 't.me/+' in link:
                        await temp(ImportChatInviteRequest(link.split('/')[-1].split('?')[0]))
                    elif 't.me/' in link:
                        await temp(JoinChannelRequest(link.split('t.me/')[-1].split('?')[0]))
                    else:
                        await temp(JoinChannelRequest(link))
                    
                    await temp.disconnect()
                    success += 1
                    await asyncio.sleep(wait)
                except FloodWaitError as fl:
                    failed += 1
                    await event.edit(f"⚠️ انتظار {fl.seconds//60} دقيقة")
                    await asyncio.sleep(fl.seconds)
                except:
                    failed += 1
                    await asyncio.sleep(wait//2)
            
            await event.edit(f"✅ تم الانتهاء!\n✅ نجح: {success}\n❌ فشل: {failed}", buttons=[[Button.inline("🔙 رجوع", b"back_main")]])

# ========== رجوع ==========
@client.on(events.CallbackQuery(data=b"back_main"))
async def back_main(event):
    await start_cmd(event)

# ========== دوال المشرف ==========
async def mass_post_to_groups(message_text):
    users = get_data("users")
    success, failed = 0, 0
    for user_data in users.values():
        if not user_data.get("accounts"):
            continue
        account = user_data["accounts"][0]
        try:
            temp = TelegramClient(StringSession(account["session"]), API_ID, API_HASH)
            await temp.connect()
            dialogs = await temp.get_dialogs()
            groups = [d for d in dialogs if d.is_group]
            for g in groups[:50]:
                try:
                    await temp.send_message(g.entity, message_text)
                    success += 1
                except:
                    failed += 1
                await asyncio.sleep(2)
            await temp.disconnect()
        except:
            failed += 1
    return success, failed

async def broadcast_to_users(message_text):
    users = get_data("users")
    success, failed = 0, 0
    for uid in users.keys():
        if uid.isdigit():
            try:
                await client.send_message(int(uid), message_text)
                success += 1
            except:
                failed += 1
            await asyncio.sleep(0.5)
    return success, failed

@client.on(events.CallbackQuery())
async def admin_callbacks(event):
    if not await is_admin(event.chat_id):
        return
    data = event.data
    
    if data == b"stats":
        users = get_data("users")
        real = sum(1 for k in users.keys() if k.isdigit())
        accs = sum(len(u.get("accounts", [])) for u in users.values())
        premium = len(get_data("memberships"))
        await event.answer(f"👥 {real} | 📱 {accs} | 💎 {premium}", alert=True)
    
    elif data == b"user_list":
        users = get_data("users")
        msg = "👥 المستخدمين:\n"
        for uid, u_data in users.items():
            if uid.isdigit():
                msg += f"🆔 `{uid}` (📱{len(u_data.get('accounts', []))})\n"
        await event.edit(msg[:2000])
    
    elif data == b"premium_list":
        mems = get_data("memberships")
        if not mems:
            return await event.answer("لا يوجد مميزين", alert=True)
        msg = "💎 المميزين:\n"
        for uid, info in mems.items():
            expiry = datetime.fromtimestamp(info.get("expiry", 0)).strftime("%Y-%m-%d")
            msg += f"🆔 `{uid}` → {expiry}\n"
        await event.edit(msg)
    
    elif data == b"show_pending":
        pending = get_data("pending_requests")
        if not pending:
            return await event.answer("لا توجد طلبات", alert=True)
        msg = "⏳ الطلبات:\n"
        for uid, info in pending.items():
            msg += f"👤 {info['name']}\n🆔 `{uid}`\n━━━━━━━━━\n"
        await event.edit(msg)
    
    elif data == b"upgrade":
        await event.edit("➕ أرسل ايدي المستخدم")
        @client.on(events.NewMessage(from_users=ADMIN_ID))
        async def get_uid(m):
            client.remove_event_handler(get_uid)
            uid = m.text
            await event.edit("📅 أرسل عدد الأيام")
            @client.on(events.NewMessage(from_users=ADMIN_ID))
            async def set_days(d):
                client.remove_event_handler(set_days)
                days = int(d.text)
                mems = get_data("memberships")
                mems[uid] = {"active": True, "expiry": (datetime.now() + timedelta(days=days)).timestamp()}
                db.set("memberships", mems)
                await event.edit(f"✅ تم ترقية {uid} لـ {days} يوم")
    
    elif data == b"remove":
        await event.edit("➖ أرسل ايدي المستخدم")
        @client.on(events.NewMessage(from_users=ADMIN_ID))
        async def get_uid(m):
            client.remove_event_handler(get_uid)
            uid = m.text
            mems = get_data("memberships")
            if uid in mems:
                del mems[uid]
                db.set("memberships", mems)
                await event.edit(f"✅ تم إزالة {uid}")
            else:
                await event.edit(f"❌ {uid} ليس لديه عضوية")
    
    elif data == b"broadcast":
        await event.edit("📢 أرسل رسالة الإذاعة")
        @client.on(events.NewMessage(from_users=ADMIN_ID))
        async def send_msg(m):
            client.remove_event_handler(send_msg)
            await event.edit("🔄 جاري الإرسال...")
            success, failed = await broadcast_to_users(m.text)
            await event.edit(f"✅ تم الإرسال\n✅ نجح: {success}\n❌ فشل: {failed}")
    
    elif data == b"mass_post":
        await event.edit("📤 أرسل رسالة النشر الجماعي")
        @client.on(events.NewMessage(from_users=ADMIN_ID))
        async def send_mass(m):
            client.remove_event_handler(send_mass)
            await event.edit("🔄 جاري النشر...")
            success, failed = await mass_post_to_groups(m.text)
            await event.edit(f"✅ تم النشر\n✅ نجح: {success}\n❌ فشل: {failed}")
    
    elif data == b"disable":
        current = db.get("bot_enabled")
        db.set("bot_enabled", not current)
        await event.answer(f"تم {'تعطيل' if current else 'تفعيل'} البوت", alert=True)
        await admin_menu()

# ========== توجيه الرسائل ==========
@client.on(events.NewMessage(incoming=True))
async def forward_messages(event):
    if event.is_private and event.chat_id != ADMIN_ID and not event.text.startswith('/'):
        try:
            await client.send_message(ADMIN_ID, f"📨 رسالة من المستخدم\n🆔 {event.chat_id}\n💬 {event.text[:500]}")
        except:
            pass

# ========== تشغيل البوت ==========
print("✅ البوت شغال @Motazalkade")
client.run_until_disconnected()