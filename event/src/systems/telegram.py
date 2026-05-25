from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

def send_to_telegram(notification_system, image_bytes, camera_name):
    target_chat_ids = []

    for user_id, camera_settings in notification_system.user_prefs_cache.items():
        if user_id in notification_system.allowed_users and camera_settings.get(camera_name, False):
            target_chat_ids.append(user_id)

    url =  f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    for chat_id in target_chat_ids:
        files = {'photo': ('snapshot.jpg', io.BytesIO(image_bytes), 'image/jpeg')}
        data = {'chat_id': chat_id, 'caption': f"Person detected on {camera_name}"}
        
        try:
            response = requests.post(url, files=files, data=data)
            print(f"Sent snapshot from {camera_name}: {response.status_code}")
        except Exception as e:
            print(f"Error sending to Telegram: {e}")

def build_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    prefs = get_user_preferences(user_id)
    keyboard = []
    for cam in FRIGATE_CAMERAS:
        status_emoji = "🔔 ON" if prefs.get(cam, False) else "🔕 OFF"
        button_text = f"{cam.replace('_', ' ').title()}: {status_emoji}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"toggle_{cam}")])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f"Start command received: {update.effective_user.username} ({update.effective_user.id})")
    user_id = update.effective_user.id

    if user_id not in ALLOWED_USERS:
        await update.message.reply_text("❌ Unauthorized access.")
        return

    await update.message.reply_text(
        "👋 Manage your Frigate notification settings:",
        reply_markup=build_menu_keyboard(user_id)
    )

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f"{update=}")
    query = update.callback_query
    user_id = query.from_user.id
    
    if user_id not in ALLOWED_USERS:
        await query.answer("Unauthorized.", show_alert=True)
        return

    await query.answer()

    if query.data.startswith("toggle_"):
        camera_to_toggle = query.data.split("toggle_")[1]
        
        if user_id not in user_prefs_cache:
            user_prefs_cache[user_id] = {cam: False for cam in FRIGATE_CAMERAS}
            
        current_state = user_prefs_cache[user_id].get(camera_to_toggle, False)
        new_state = not current_state
        user_prefs_cache[user_id][camera_to_toggle] = new_state
        
        await query.edit_message_reply_markup(reply_markup=build_menu_keyboard(user_id))
        
        payload = "1" if new_state else "0"
        topic = f"{BOT_TOPIC}/bot/users/{user_id}/cameras/{camera_to_toggle}"
        
        #mqttc.publish(topic, payload=payload, qos=1, retain=True)
        if mqttc and mqttc.is_connected():
            mqttc.publish(topic, payload=payload, qos=1, retain=True)
            logger.info(f"📤 Sent retain preference to MQTT topic: {topic} -> {payload}")
        else:
            logger.error("❌ Primary MQTT client is offline. Configuration state could not be sent.")

from telegram.ext import MessageHandler, filters

async def global_debug_inspector(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Intercepts absolutely any incoming message text for verification"""
    logger.info("========================================")
    logger.info(f"🚨 RAW UPDATE RECEIVED!")
    logger.info(f"User Text: {update.message.text if update.message else 'No Text'}")
    logger.info(f"User Object: {update.effective_user}")
    logger.info("========================================")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Logs exceptions thrown inside the async worker context to trace failures"""
    logger.error(f"⚠️ Exception occurred inside Telegram framework core: {context.error}", exc_info=context.error)
