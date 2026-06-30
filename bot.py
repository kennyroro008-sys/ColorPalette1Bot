import os
import sys
import logging
import json
import random
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get bot token from environment variable
def get_token():
    token = os.environ.get('BOT_TOKEN')
    if not token:
        token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("❌ No BOT_TOKEN found in environment variables!")
        logger.error("Please add BOT_TOKEN to your Railway Variables.")
        sys.exit(1)
    return token

TOKEN = get_token()
logger.info("✅ Bot token loaded successfully!")

# Store user's selected colors
user_colors = {}

# WebApp URL - you can change this to your hosted version
WEBAPP_URL = "https://python-telegram-bot.org/static/webappbot"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message with the color picker button."""
    user = update.effective_user
    
    welcome_text = f"""
🎨 **Welcome to ColorPalette1Bot, {user.first_name}!**

I help you pick and manage colors for your projects.

**What you can do:**
• Pick colors using the interactive color picker
• Generate random color palettes
• Save your favorite colors
• Get HEX, RGB, and HSL values

**Commands:**
/start - Show this menu
/color - Open color picker
/palette - Generate a random palette
/saved - Show your saved colors
/help - Show all commands

Click the button below to pick your first color!
"""
    
    # Create button with WebApp
    keyboard = [
        [KeyboardButton("🎨 Pick a Color", web_app=WebAppInfo(url=WEBAPP_URL))],
        [KeyboardButton("🎲 Random Palette")],
        [KeyboardButton("💾 Save This Color")],
        [KeyboardButton("📋 My Saved Colors")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)


async def color_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Open the color picker via /color command."""
    keyboard = [
        [KeyboardButton("🎨 Pick a Color", web_app=WebAppInfo(url=WEBAPP_URL))],
        [KeyboardButton("❌ Close")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "🎨 **Color Picker**\n\nClick the button below to open the color picker.",
        reply_markup=reply_markup
    )


async def palette_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate a random color palette."""
    # Generate 5 random colors
    palette = []
    for _ in range(5):
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        palette.append(hex_color)
    
    # Create a visual representation using colored text blocks
    palette_text = "🎨 **Your Random Palette:**\n\n"
    for i, color in enumerate(palette, 1):
        palette_text += f"{i}. `{color}`\n"
    
    # Add color preview using emoji squares (approximate)
    palette_text += "\n**Preview:**\n"
    for color in palette:
        # Use colored circles or squares (approximate)
        palette_text += f"🟦 "  # We can't show actual colors in text
    
    palette_text += "\n\n💡 Use /color to pick specific colors!"
    
    await update.message.reply_text(palette_text)


async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the color data sent back from the WebApp."""
    try:
        # Parse the JSON data from the WebApp
        data = json.loads(update.effective_message.web_app_data.data)
        
        hex_color = data.get('hex', '#000000')
        rgb = data.get('rgb', {'r': 0, 'g': 0, 'b': 0})
        hsl = data.get('hsl', {'h': 0, 's': 0, 'l': 0})
        
        rgb_tuple = (rgb.get('r', 0), rgb.get('g', 0), rgb.get('b', 0))
        hsl_tuple = (hsl.get('h', 0), hsl.get('s', 0), hsl.get('l', 0))
        
        user_id = update.effective_user.id
        
        # Store the color
        if user_id not in user_colors:
            user_colors[user_id] = []
        user_colors[user_id].append({
            'hex': hex_color,
            'rgb': rgb_tuple,
            'hsl': hsl_tuple,
            'timestamp': update.effective_message.date
        })
        
        # Keep only last 20 colors
        if len(user_colors[user_id]) > 20:
            user_colors[user_id] = user_colors[user_id][-20:]
        
        # Send the color information back to the user
        response = f"""
✅ **Color Selected!**

🎨 **HEX:** `{hex_color}`
🌈 **RGB:** `{rgb_tuple}`
📐 **HSL:** `{hsl_tuple}`

💡 **What would you like to do?**
• Use /palette to generate a palette
• Send another color
• Use /saved to see your saved colors
"""
        await update.message.reply_text(response)
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse WebApp data: {e}")
        await update.message.reply_text("❌ Sorry, I couldn't parse the color data. Please try again.")


async def saved_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's saved colors."""
    user_id = update.effective_user.id
    
    if user_id not in user_colors or not user_colors[user_id]:
        await update.message.reply_text(
            "📋 **No saved colors yet!**\n\n"
            "Use the color picker to pick and save your first color!"
        )
        return
    
    colors = user_colors[user_id][-10:]  # Show last 10 colors
    
    response = "📋 **Your Saved Colors:**\n\n"
    for i, color in enumerate(colors, 1):
        response += f"{i}. `{color['hex']}` → RGB{color['rgb']}\n"
    
    response += "\n💡 Use /color to pick more colors!"
    
    await update.message.reply_text(response)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages and keyboard buttons."""
    text = update.message.text
    
    if text == "🎨 Pick a Color":
        # This is handled by the WebApp button
        await update.message.reply_text(
            "🎨 Click the button below to open the color picker!",
            reply_markup=ReplyKeyboardMarkup.from_button(
                KeyboardButton("🎨 Open Color Picker", web_app=WebAppInfo(url=WEBAPP_URL))
            )
        )
    elif text == "🎲 Random Palette":
        await palette_command(update, context)
    elif text == "💾 Save This Color":
        user_id = update.effective_user.id
        if user_id in user_colors and user_colors[user_id]:
            last_color = user_colors[user_id][-1]
            await update.message.reply_text(
                f"✅ **Color saved!**\n\n"
                f"HEX: `{last_color['hex']}`\n"
                f"RGB: `{last_color['rgb']}`\n\n"
                f"Use /saved to see all your colors."
            )
        else:
            await update.message.reply_text(
                "❌ No color to save!\n\n"
                "Use the color picker to pick a color first."
            )
    elif text == "📋 My Saved Colors":
        await saved_command(update, context)
    elif text == "❌ Close":
        await update.message.reply_text("✅ Closed.", reply_markup=ReplyKeyboardMarkup.remove_keyboard())
    else:
        await update.message.reply_text(
            "❓ I don't understand that command.\n\n"
            "Use /help to see available commands."
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message."""
    help_text = """
🎨 **ColorPalette1Bot Help**

**Commands:**
/start - Welcome message with menu
/color - Open the color picker
/palette - Generate a random palette
/saved - Show your saved colors
/help - Show this help message

**Keyboard Buttons:**
🎨 Pick a Color - Open the color picker
🎲 Random Palette - Generate random colors
💾 Save This Color - Save the last picked color
📋 My Saved Colors - View saved colors

**How to use:**
1. Click "Pick a Color" to open the picker
2. Choose your color using the interactive picker
3. Click "Choose Color" to send it back
4. Get your HEX and RGB values!

**Tips:**
• Save your favorite colors with the "Save" button
• Generate palettes for inspiration
• All colors are stored in your session
"""
    await update.message.reply_text(help_text)


def main() -> None:
    """Start the bot."""
    try:
        # Create Application
        application = Application.builder().token(TOKEN).build()
        
        # Add command handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("color", color_command))
        application.add_handler(CommandHandler("palette", palette_command))
        application.add_handler(CommandHandler("saved", saved_command))
        
        # Add handler for WebApp data
        application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
        
        # Add handler for text messages
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        
        # Start the Bot
        logger.info("🚀 ColorPalette1Bot started successfully!")
        logger.info("🎨 Press Ctrl+C to stop.")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
