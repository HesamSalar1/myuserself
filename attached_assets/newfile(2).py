from pyrogram import Client, filters
from pyrogram.types import Message
from random import choice

api_id = 21555907
api_hash = "16f4e09d753bc4b182434d8e37f410cd"


# ایجاد کلاینت با استفاده از Pyrogram
app = Client("session_name", api_id, api_hash)

# شناسه ادمین (باید با شناسه ادمین واقعی جایگزین شود)
admin_id = 7607882302

# لیست‌های فوش و دشمن
fosh_list = []
enemy_list = []

# دستور اضافه کردن فوش به لیست
@app.on_message(filters.command("addfosh") & filters.user(admin_id))
async def add_fosh(client: Client, message: Message):
    try:
        if len(message.command) < 2:
            await message.edit_text("**لطفاً یک فوش وارد کنید.**")
            return

        fosh = " ".join(message.command[1:])  # کل متن بعد از دستور را به‌عنوان فوش ذخیره می‌کند
        if fosh in fosh_list:
            await message.edit_text(f"**فوش '{fosh}' از قبل در لیست وجود دارد.**")
        else:
            fosh_list.append(fosh)
            await message.edit_text(f"**فوش '{fosh}' به لیست اضافه شد.**")
    except Exception as e:
        print(f"خطا در اضافه کردن فوش: {e}")

# دستور حذف فوش از لیست
@app.on_message(filters.command("delfosh") & filters.user(admin_id))
async def del_fosh(client: Client, message: Message):
    try:
        if len(message.command) < 2:
            await message.edit_text("**لطفاً یک فوش وارد کنید.**")
            return

        fosh = " ".join(message.command[1:])  # کل متن بعد از دستور را به‌عنوان فوش در نظر می‌گیرد
        if fosh not in fosh_list:
            await message.edit_text(f"**فوش '{fosh}' در لیست وجود ندارد.**")
        else:
            fosh_list.remove(fosh)
            await message.edit_text(f"**فوش '{fosh}' از لیست حذف شد.**")
    except Exception as e:
        print(f"خطا در حذف فوش: {e}")

# دستور پاک کردن لیست فوش‌ها
@app.on_message(filters.command("clearfosh") & filters.user(admin_id))
async def clear_fosh(client: Client, message: Message):
    try:
        fosh_list.clear()
        await message.edit_text("**لیست فوش‌ها پاک شد.**")
    except Exception as e:
        print(f"خطا در پاک کردن لیست فوش‌ها: {e}")

# دستور اضافه کردن کاربر به لیست دشمنان
@app.on_message(filters.command("setenemy") & filters.user(admin_id) & filters.reply)
async def set_enemy(client: Client, message: Message):
    try:
        replied = message.reply_to_message
        user_id = replied.from_user.id
        
        if user_id in enemy_list:
            await message.edit_text(f"**کاربر {user_id} از قبل در لیست دشمنان وجود دارد.**")
        else:
            enemy_list.append(user_id)
            await message.edit_text(f"**کاربر {user_id} به لیست دشمنان اضافه شد.**")
    except Exception as e:
        print(f"خطا در اضافه کردن دشمن: {e}")

# دستور حذف کاربر از لیست دشمنان
@app.on_message(filters.command("delenemy") & filters.user(admin_id) & filters.reply)
async def del_enemy(client: Client, message: Message):
    try:
        replied = message.reply_to_message
        user_id = replied.from_user.id

        if user_id not in enemy_list:
            await message.edit_text(f"**کاربر {user_id} در لیست دشمنان وجود ندارد.**")
        else:
            enemy_list.remove(user_id)
            await message.edit_text(f"**کاربر {user_id} از لیست دشمنان حذف شد.**")
    except Exception as e:
        print(f"خطا در حذف دشمن: {e}")

# دستور پاک کردن لیست دشمنان
@app.on_message(filters.command("clearenemy") & filters.user(admin_id))
async def clear_enemy(client: Client, message: Message):
    try:
        enemy_list.clear()
        await message.edit_text("**لیست دشمنان پاک شد.**")
    except Exception as e:
        print(f"خطا در پاک کردن لیست دشمنان: {e}")

# پاسخ به پیام‌های کاربران دشمن
@app.on_message()
async def reply_enemy(client: Client, message: Message):
    try:
        if message.from_user.id in enemy_list and fosh_list:
            # انتخاب یک فوش تصادفی از لیست
            fosh = choice(fosh_list)
            # ارسال فوش به‌عنوان ریپلای به پیام کاربر
            await message.reply_text(fosh, reply_to_message_id=message.id)
    except Exception as e:
        print(f"خطا در پاسخ به دشمن: {e}")

# خوش‌آمدگویی به کاربران جدید
@app.on_chat_member_updated()
async def welcome(client: Client, message: Message):
    try:
        if message.new_chat_member:
            await message.reply_text("خوش آمدید!")
    except Exception as e:
        print(f"خطا در خوش‌آمدگویی: {e}")

# شروع ربات
print("ربات شروع به کار کرد!")
app.run()