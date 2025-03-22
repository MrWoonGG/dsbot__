import disnake
from disnake.ext import commands
from logger import Logger
import database
from views import TemplateOrder
import threading
# ============================================

TOKEN = "MTM1MjI1MjExOTY4MzY5ODc0OQ.GNBht6.2b--nrO9vvVzPiK9DUFNwXfdPhqFXSZ_l2h9QQ"
GUILD_IDS = [1340550027126505513]

# ============================================

# ============================================

logger = Logger(debug_enabled=True)

bot = commands.Bot(intents=disnake.Intents.all())
db = database.load_db()


def load_db():
    return database.load_db()


@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user.name}")


def has_admin_access(user_roles):
    db = load_db()
    return db['admin_role_id'] == 0 or any(role.id == db['admin_role_id']
                                           for role in user_roles)


def has_worker_access(user_roles):
    db = load_db()
    return db['workers_role_id'] == 0 or any(role.id == db['workers_role_id']
                                             for role in user_roles)


@bot.slash_command(guild_ids=GUILD_IDS,
                   description="Сменить канал с заказом шаблонов")
async def change_channel(inter: disnake.CommandInteraction,
                         channel: disnake.TextChannel = commands.Param(
                             description="Канал для заказов шаблонов")):
    await inter.response.defer(ephemeral=True)

    if has_admin_access(inter.user.roles):
        db['channel_id'] = channel.id
        database.save_db(db)
        await inter.edit_original_response(
            f"Канал изменён на {channel.mention}")
    else:
        await inter.edit_original_response(
            f"Вам нельзя выполнять эту команду (Доступ у <@&{db['admin_role_id']}>)"
        )


@bot.slash_command(guild_ids=GUILD_IDS, description="Сменить роль админа бота")
async def change_admin_role(
    inter: disnake.CommandInteraction,
    role: disnake.Role = commands.Param(
        description="Роль для доступа к настройкам бота")):
    await inter.response.defer(ephemeral=True)

    if has_admin_access(inter.user.roles):
        db['admin_role_id'] = role.id
        database.save_db(db)
        await inter.edit_original_response(f"Роль изменена на {role.mention}")
    else:
        await inter.edit_original_response(
            f"Вам нельзя выполнять эту команду (Доступ у <@&{db['admin_role_id']}>)"
        )


@bot.slash_command(guild_ids=GUILD_IDS,
                   description="Сменить роль работника бота")
async def change_worker_role(
    inter: disnake.CommandInteraction,
    role: disnake.Role = commands.Param(
        description="Роль для доступа к принятию заказов на шаблоны")):
    await inter.response.defer(ephemeral=True)

    if has_admin_access(inter.user.roles):
        db['workers_role_id'] = role.id
        database.save_db(db)
        await inter.edit_original_response(f"Роль изменена на {role.mention}")
    else:
        await inter.edit_original_response(
            f"Вам нельзя выполнять эту команду (Доступ у <@&{db['admin_role_id']}>)"
        )


@bot.slash_command(guild_ids=GUILD_IDS,
                   description="Отправить первое сообщение")
async def send_first_message(inter: disnake.CommandInteraction):
    await inter.response.defer(ephemeral=True)

    if has_admin_access(inter.user.roles):
        channel = bot.get_channel(db['channel_id'])
        await channel.send("Нажмите кнопку ниже, чтобы заказать шаблон:",
                           view=TemplateOrder(channel=channel))
        await inter.edit_original_response("Готово!")
    else:
        await inter.edit_original_response(
            f"Вам нельзя выполнять эту команду (Доступ у <@&{db['admin_role_id']}>)"
        )


# Приём заказа
@bot.slash_command(guild_ids=GUILD_IDS, description="Принять заказ шаблона")
async def accept_order(
    inter: disnake.CommandInteraction,
    order_id: int = commands.Param(description="Номер заказа (без #)")):
    await inter.response.defer(ephemeral=True)

    db = load_db()

    if not has_worker_access(inter.user.roles):
        await inter.edit_original_response(
            f"Вам нельзя выполнять эту команду (Доступ у <@&{db['workers_role_id']}>)"
        )
        return

    order_key = str(order_id)
    if order_key not in db["orders"]:
        await inter.edit_original_response("❌ Заказ с таким ID не найден.")
        return

    order = db["orders"][order_key]

    if order["worker_id"] != 0:
        await inter.edit_original_response(
            f"⚠ Заказ #{order_id} уже принят другим исполнителем.")
        return

    order["worker_id"] = inter.user.id
    database.save_db(db)

    embed = disnake.Embed(title="✅ Заказ принят!",
                          description=f"Вы приняли заказ **#{order_id}**\n"
                          f"🔗 **Сервер:** {order['server_link']}\n"
                          f"📝 **Описание:** {order['template_purpose']}",
                          color=disnake.Color.green())
    embed.set_footer(
        text=f"Для отправки шаблона заказчику введите /return_order",
        icon_url=inter.user.avatar.url)

    await inter.edit_original_response(embed=embed)

    channel = bot.get_channel(db['channel_id'])
    if channel:
        embed = disnake.Embed(title=f"🔔 Заказ #{str(order_id)} принят",
                              color=disnake.Color.yellow())
        uid = order["user_id"]
        worker_ = order["worker_id"]
        embed.add_field(name="🧑‍💻 Исполнитель",
                        value=f"<@{worker_}>",
                        inline=False)
        embed.add_field(name="🔗 Ссылка на сервер",
                        value=order['server_link'],
                        inline=False)
        embed.add_field(name="📄 Шаблон нужен для...",
                        value=order['template_purpose'][:1024],
                        inline=False)
        await channel.send(f'||<@{uid}>||',
                           embed=embed,
                           view=TemplateOrder(channel))


@bot.slash_command(guild_ids=GUILD_IDS, description="Возврат готового шаблона")
async def return_order(
    inter: disnake.CommandInteraction,
    order_id: int = commands.Param(description="Номер заказа (без #)"),
    template_link: str = commands.Param(
        description="Ссылка на готовый шаблон")):
    await inter.response.defer(ephemeral=True)

    db = load_db()

    if not has_worker_access(inter.user.roles):
        await inter.edit_original_response(
            f"Вам нельзя выполнять эту команду (Доступ у <@&{db['workers_role_id']}>)"
        )
        return

    order_key = str(order_id)
    if order_key not in db["orders"]:
        await inter.edit_original_response("❌ Заказ с таким ID не найден.")
        return

    order = db["orders"][order_key]

    if order["worker_id"] != inter.user.id:
        await inter.edit_original_response(
            f"⚠ Вы не являетесь исполнителем для заказа #{order_id}.")
        return

    embed = disnake.Embed(title=f"✅ Заказ #{str(order_id)} выполнен",
                          color=disnake.Color.green())
    uid = order["user_id"]
    worker_ = order["worker_id"]
    embed.add_field(name="🧑‍💻 Исполнитель",
                    value=f"<@{worker_}>",
                    inline=False)
    embed.add_field(name="🔗 Ссылка на сервер",
                    value=order['server_link'],
                    inline=False)
    embed.add_field(name="📄 Шаблон нужен для...",
                    value=order['template_purpose'][:1024],
                    inline=False)
    embed.add_field(name="🔗 Ссылка на готовый шаблон",
                    value=template_link,
                    inline=False)

    channel = bot.get_channel(db['channel_id'])
    if channel:
        await channel.send(f'||<@{uid}>||',
                           embed=embed,
                           view=TemplateOrder(channel))

    del db["orders"][order_key]
    database.save_db(db)

    await inter.edit_original_response(
        f"Заказ #{order_id} успешно завершен и удален из базы данных.")


bot.run(TOKEN)
