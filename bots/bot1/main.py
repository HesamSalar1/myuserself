if fosh.startswith("MEDIA:"):
                        parts = fosh.split(":", 2)
                        media_type = parts[1]
                        media_id = parts[2]
                        await send_media_reply(client, message, media_type, media_id)
                    else:
                        # اضافه کردن تاخیر کوتاه برای جلوگیری از تکرار ID
                        import asyncio
                        await asyncio.sleep(0.1)
                        await message.reply(fosh)