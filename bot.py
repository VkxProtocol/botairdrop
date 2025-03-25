from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import requests
import json
from datetime import datetime, timedelta
import random

# Configurações
API_URL = "https://www.vkinha.com/php/bta.php"
API_KEY = '[REDACTED_SECRET]'
TOKEN = '[REDACTED_SECRET]'

def fetch_user_data(user_id=None, wallet=None):
    """Busca os dados do usuário na API."""
    try:
        if user_id:
            url = f"{API_URL}?api_key={API_KEY}&user_id={user_id}"
        elif wallet:
            url = f"{API_URL}?api_key={API_KEY}&wallet={wallet}"
        else:
            return {"error": "user_id ou wallet necessário"}
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
        }
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code (fetch_user_data): {response.status_code}")
        print(f"Resposta (fetch_user_data): {response.text}")
        if response.status_code == 200:
            return response.json()
        return {"error": f"Erro ao acessar a API: Status {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Exceção na requisição: {str(e)}"}

def save_wallet(user_id, wallet):
    """Salva a carteira do usuário na API."""
    try:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        data = {
            "action": "save_wallet",
            "user_id": user_id,
            "wallet": wallet
        }
        response = requests.post(API_URL, json=data, headers=headers, timeout=10)
        print(f"Status Code (save_wallet): {response.status_code}")
        print(f"Resposta (save_wallet): {response.text}")
        return response.status_code == 200 and response.json().get("status") == "success"
    except Exception as e:
        print(f"Erro ao salvar wallet: {e}")
        return False

def update_tokens(user_id, tokens, task):
    """Atualiza os tokens do usuário na API."""
    try:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        data = {
            "action": "update_tokens",
            "user_id": user_id,
            "tokens": tokens,
            "task": task
        }
        response = requests.post(API_URL, json=data, headers=headers, timeout=10)
        print(f"Status Code (update_tokens): {response.status_code}")
        print(f"Resposta (update_tokens): {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Erro ao atualizar tokens: {e}")
        return False

async def notify_user(context: ContextTypes.DEFAULT_TYPE):
    """Envia uma notificação para o usuário quando a Tarefa 4 estiver disponível."""
    user_id = context.job.context['user_id']
    await context.bot.send_message(
        chat_id=user_id,
        text="⏰ A Tarefa 4 está disponível! Volte ao bot para receber sua recompensa (0.10000 a 2.000000 VKINHA)."
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler do comando /start."""
    user_id = update.effective_user.id
    print(f"User ID: {user_id}")

    user_data = fetch_user_data(user_id=user_id)

    if "error" in user_data:
        # Usuário não encontrado, solicita a carteira
        await update.message.reply_text(
            "🚀 Bem-vindo ao Airdrop VKINHA!\n"
            "⚠️ Utilize uma carteira da rede BNB Chain (MetaMask ou Trust Wallet) para receber seus tokens $VKINHA.\n"
            "Por favor, envie o endereço da sua carteira (ex.: 0x...):"
        )
        context.user_data['awaiting_wallet'] = True
    else:
        # Usuário já tem carteira, exibe as tarefas
        wallet = user_data.get("wallet")
        balance = float(user_data.get("tokens", 0)) + float(user_data.get("click_tokens", 0))
        await update.message.reply_text(
            f"👋 Bem-vindo novamente {update.effective_user.first_name}!\n"
            f"Carteira: {wallet}\n"
            f"Saldo atual: {balance:.8f} $VKINHA\n\n"
            "Deseja continuar suas tarefas?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📋 Continuar Tarefas", callback_data='show_tasks')],
                [InlineKeyboardButton("🔄 Atualizar", callback_data='refresh_balance')]
            ])
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para mensagens de texto (recebe a carteira)."""
    user_id = update.effective_user.id
    if context.user_data.get('awaiting_wallet'):
        wallet = update.message.text.strip()
        print(f"Carteira recebida: {wallet}")

        # Validação básica do endereço (exemplo simples, ajuste conforme necessário)
        if not wallet.startswith("0x") or len(wallet) != 42:
            await update.message.reply_text(
                "⚠️ Endereço inválido! Por favor, envie um endereço válido da rede BNB Chain (ex.: 0x...). Tente novamente:"
            )
            return

        # Salva a carteira no banco de dados
        if save_wallet(user_id, wallet):
            context.user_data['awaiting_wallet'] = False
            await update.message.reply_text(
                f"🎉 Carteira {wallet} salva com sucesso!\n"
                "Agora você pode começar as tarefas para ganhar $VKINHA:"
            )
            await show_tasks(update, context)
        else:
            await update.message.reply_text(
                "❌ Erro ao salvar a carteira. Tente novamente ou entre em contato com o suporte (@feelipw)."
            )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para os botões de callback."""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_data = fetch_user_data(user_id=user_id)

    if query.data == 'show_tasks':
        await show_tasks(update, context)

    elif query.data == 'refresh_balance':
        wallet = user_data.get("wallet")
        balance = float(user_data.get("tokens", 0)) + float(user_data.get("click_tokens", 0))
        await query.edit_message_text(
            f"🔄 Dados atualizados:\n"
            f"Carteira: {wallet}\n"
            f"Saldo total: {balance:.8f} $VKINHA",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📋 Voltar às Tarefas", callback_data='show_tasks')],
                [InlineKeyboardButton("🔄 Atualizar", callback_data='refresh_balance')]
            ])
        )

    elif query.data.startswith('task_'):
        task = query.data.split('_')[1]
        user_data = fetch_user_data(user_id=user_id)

        if task in ['instagram', 'twitter', 'telegram', 'threads']:
            task_field = f"{task}_done"
            if user_data.get(task_field) == "1":
                await query.answer("Você já completou esta tarefa!", show_alert=True)
                return
            reward = random.uniform(10, 25)
            if update_tokens(user_id, reward, task_field):
                await query.answer(f"Parabéns! Você ganhou {reward:.8f} $VKINHA!", show_alert=True)
                await show_tasks(update, context)
            else:
                await query.answer("Erro ao processar a tarefa. Tente novamente.", show_alert=True)

        elif task == 'hourly':
            last_reward = user_data.get("last_reward_time")
            if last_reward:
                last_reward_time = datetime.strptime(last_reward, "%Y-%m-%d %H:%M:%S")
                if (datetime.now() - last_reward_time).total_seconds() < 2 * 3600:
                    remaining = 2 * 3600 - (datetime.now() - last_reward_time).total_seconds()
                    await query.answer(f"Espere {int(remaining/60)} minutos para esta tarefa!", show_alert=True)
                    return
            reward = random.uniform(0.1, 2.0)
            if update_tokens(user_id, reward, "last_reward_time"):
                await query.answer(f"Parabéns! Você ganhou {reward:.8f} $VKINHA!", show_alert=True)
                context.job_queue.run_once(notify_user, 2 * 3600 - 1, context={'user_id': user_id})
                await show_tasks(update, context)
            else:
                await query.answer("Erro ao processar a tarefa. Tente novamente.", show_alert=True)

        elif task == 'share':
            status_text = "Venha receber airdrop vkinha! www.vkinha.com/airdrop"
            await query.message.reply_text(
                f"📢 Publique este status no Telegram:\n\n{status_text}\n\nApós publicar, clique em 'Confirmar'.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Confirmar", callback_data='confirm_share')]
                ])
            )

        elif task == 'click':
            reward = 0.0001
            if update_tokens(user_id, reward, "click_tokens"):
                user_data = fetch_user_data(user_id=user_id)
                balance = float(user_data.get("tokens", 0)) + float(user_data.get("click_tokens", 0))
                await query.answer(f"Você ganhou {reward:.8f} $VKINHA!", show_alert=True)
                await query.message.reply_text(f"💰 Saldo atualizado: {balance:.8f} $VKINHA")
                await show_tasks(update, context)
            else:
                await query.answer("Erro ao processar a tarefa. Tente novamente.", show_alert=True)

        elif task == 'invite':
            await query.message.reply_text(
                "📩 Convide 10 amigos para o grupo Telegram: https://t.me/vkinhacoin\n"
                "Após convidar, clique em 'Confirmar'.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Confirmar", callback_data='confirm_invite')]
                ])
            )

    elif query.data == 'confirm_share':
        reward = random.uniform(5, 20)
        if update_tokens(user_id, reward, "share_done"):
            await query.answer(f"Parabéns! Você ganhou {reward:.8f} $VKINHA!", show_alert=True)
            await show_tasks(update, context)
        else:
            await query.answer("Erro ao processar a tarefa. Tente novamente.", show_alert=True)

    elif query.data == 'confirm_invite':
        user_data = fetch_user_data(user_id=user_id)
        invited_friends = int(user_data.get("invited_friends", 0))
        if invited_friends >= 10:
            await query.answer("Você já completou esta tarefa!", show_alert=True)
            return
        reward = random.uniform(10, 25)
        if update_tokens(user_id, reward, "invited_friends"):
            await query.answer(f"Parabéns! Você ganhou {reward:.8f} $VKINHA!", show_alert=True)
            await show_tasks(update, context)
        else:
            await query.answer("Erro ao processar a tarefa. Tente novamente.", show_alert=True)

async def show_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Exibe as tarefas disponíveis."""
    query = update.callback_query if update.callback_query else None
    user_id = update.effective_user.id
    user_data = fetch_user_data(user_id=user_id)

    wallet = user_data.get("wallet")
    balance = float(user_data.get("tokens", 0)) + float(user_data.get("click_tokens", 0))

    instagram_done = user_data.get("instagram_done") == "1"
    twitter_done = user_data.get("twitter_done") == "1"
    telegram_done = user_data.get("telegram_done") == "1"
    threads_done = user_data.get("threads_done") == "1"
    invited_friends = int(user_data.get("invited_friends", 0))

    tasks_buttons = [
        [InlineKeyboardButton(
            f"📸 Tarefa 1: Seguir Instagram @vkinhacoin {'✅' if instagram_done else ''}",
            callback_data='task_instagram' if not instagram_done else 'task_completed'
        )],
        [InlineKeyboardButton(
            f"🐦 Tarefa 2: Seguir Twitter @vkinhac {'✅' if twitter_done else ''}",
            callback_data='task_twitter' if not twitter_done else 'task_completed'
        )],
        [InlineKeyboardButton(
            f"💬 Tarefa 3: Entrar no Grupo Telegram {'✅' if telegram_done else ''}",
            callback_data='task_telegram' if not telegram_done else 'task_completed'
        )],
        [InlineKeyboardButton(
            "⏰ Tarefa 4: Voltar a Cada 2 Horas",
            callback_data='task_hourly'
        )],
        [InlineKeyboardButton(
            f"📢 Tarefa 5: Compartilhar com Amigos {'✅' if user_data.get('share_done') else ''}",
            callback_data='task_share'
        )],
        [InlineKeyboardButton(
            "👆 Tarefa 6: Clique para Ganhar Tokens",
            callback_data='task_click'
        )],
        [InlineKeyboardButton(
            f"📩 Tarefa 7: Convidar 10 Amigos {'✅' if invited_friends >= 10 else ''}",
            callback_data='task_invite' if invited_friends < 10 else 'task_completed'
        )],
        [InlineKeyboardButton(
            f"🧵 Tarefa 8: Seguir Threads @vkinhacoin {'✅' if threads_done else ''}",
            callback_data='task_threads' if not threads_done else 'task_completed'
        )],
        [InlineKeyboardButton("🔄 Atualizar", callback_data='refresh_balance')]
    ]

    message_text = (
        f"📋 **Lista de Tarefas do Airdrop VKINHA**\n\n"
        f"Carteira: {wallet}\n"
        f"Saldo total: {balance:.8f} $VKINHA\n\n"
        "Complete as tarefas abaixo para ganhar mais tokens $VKINHA:"
    )

    if query:
        await query.edit_message_text(message_text, reply_markup=InlineKeyboardMarkup(tasks_buttons))
    else:
        await update.message.reply_text(message_text, reply_markup=InlineKeyboardMarkup(tasks_buttons))

if __name__ == "__main__":
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot iniciado em modo polling...")
    application.run_polling()