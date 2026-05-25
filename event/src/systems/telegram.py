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

# def build_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
#     prefs = get_user_preferences(user_id)
#     keyboard = []
#     for cam in FRIGATE_CAMERAS:
#         status_emoji = "🔔 ON" if prefs.get(cam, False) else "🔕 OFF"
#         button_text = f"{cam.replace('_', ' ').title()}: {status_emoji}"
#         keyboard.append([InlineKeyboardButton(button_text, callback_data=f"toggle_{cam}")])
#     return InlineKeyboardMarkup(keyboard)
class FoxRoseHandler:
    def __init__(self, system):
        self.system = system

    def build_persistent_keyboard(self, user_id: int) -> ReplyKeyboardMarkup:
        keyboard = []

        # 1. Row for Modes
        keyboard.append([mode.label for mode in self.system.notification_system.modes])

        # 2. Rows for Detection Notifications (Dynamic Toggles)
        notification_row = []
        for cam in self.system.camera_system.cameras:
            status_emoji = "🔔" if self.system.notification_system.get_user_preference(user_id, cam) else "🔕"
            cam_label = cam.title()
            notification_row.append(f"{status_emoji} Notif: {cam_label}")
        keyboard.append(notification_row)

        # 3. Rows for Snapshots
        snapshot_row = [f"📸 Snap: {cam.title()}" for cam in self.system.camera_system.cameras]
        keyboard.append(snapshot_row)

        # Return ReplyKeyboardMarkup instead of Inline
        return ReplyKeyboardMarkup(
            keyboard, 
            resize_keyboard=True,          # Makes buttons fit neatly on screen
            one_time_keyboard=False,       # Keeps the keyboard persistent
            input_field_placeholder="Select an option below..." # Tells them not to type
        )

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        logger.debug(f"Start command received: {update.effective_user.username} ({update.effective_user.id})")
        user_id = update.effective_user.id

        if user_id not in self.system.allowed_users:
            await update.message.reply_text("❌ Unauthorized access.")
            return

        await update.message.reply_text(
            "👋 Manage your Frigate notification settings:",
            reply_markup=build_menu_keyboard(user_id)
        )

    async def handle_keyboard_clicks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        text = update.message.text

        if user_id not in self.system.allowed_users:
            await update.message.reply_text("❌ Unauthorized access.")
            return

        # --- HANDLE MODES ---
        if text in ["🌙 Night", "🧳 Away", "🏠 At Home", "🌐 All"]:
            mode_selected = text.split(" ")[1].lower()
            # TODO: Publish your mode to MQTT here
            logger.info(f"User {user_id} set mode to {mode_selected}")
            await update.message.reply_text(f"✅ Mode changed to: {text}")
            return

        # --- HANDLE NOTIFICATION TOGGLES ---
        elif "Notif:" in text:
            # Extract camera name from string (e.g., "🔔 Notif: Achterdeur" -> "achterdeur")
            cam_title = text.split("Notif: ")[1]
            camera_to_toggle = cam_title.lower()
            
            # Pull preferences and invert the boolean
            new_state = not self.system.notification_system.get_user_preference(user_id, camera_to_toggle)
            self.system.notification_system.set_user_preference(user_id, camera_to_toggle, new_state)
            
            # Publish to MQTT 
            payload = "1" if new_state else "0"
            topic = f"{self.system.notification_system.mqtt_topic}/bot/users/{user_id}/cameras/{camera_to_toggle}"
            self.system.notification_system.publish_retained(topic, payload)

            # Update the user interface keyboard immediately with the new emoji
            await update.message.reply_text(
                f"Updated notification settings for {cam_title}.",
                reply_markup=build_persistent_keyboard(user_id)
            )
            return

        # --- HANDLE SNAPSHOTS ---
        elif "Snap:" in text:
            cam_title = text.split("Snap: ")[1]
            camera_target = cam_title.lower()
            
            await update.message.reply_text(f"⏳ Fetching snapshot for {cam_title}...")
            # TODO: Grab your image from Frigate API and send it:
            # await context.bot.send_photo(chat_id=user_id, photo=open('snap.jpg', 'rb'))
            return

    async def menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
