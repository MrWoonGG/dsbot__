import disnake
from disnake.ext import commands
from disnake import TextInputStyle
from typing import Optional

import database


class TemplateOrderModal(disnake.ui.Modal):
    def __init__(self, channel: disnake.TextChannel):
        self.channel = channel
        components = [
            disnake.ui.TextInput(
                label="Ссылка на Discord сервер",
                placeholder="https://discord.gg/example",
                custom_id="server_link",
                style=TextInputStyle.short,
                max_length=100,
            ),
            disnake.ui.TextInput(
                label="Для чего нужен шаблон?",
                placeholder="Опишите, для какой цели нужен шаблон...",
                custom_id="template_purpose",
                style=TextInputStyle.paragraph,
            ),
        ]
        super().__init__(
            title="Заказ шаблона Discord-сервера",
            custom_id="order_template",
            components=components,
        )
    
    async def callback(self, inter: disnake.ModalInteraction):
        server_link = inter.text_values["server_link"]
        template_purpose = inter.text_values["template_purpose"]
        
        if not server_link.startswith("https://discord.gg/"):
            await inter.response.send_message(
                "❌ Укажите корректную ссылку на Discord-сервер!", ephemeral=True
            )
            return
        
        db = database.load_db()
        
        # ORDER
        db['orders_counter'] += 1
        order_id = db['orders_counter']
        
        db['orders'][str(order_id)] = {
            'user_id': inter.user.id,
            'worker_id': 0,
            'server_link': server_link,
            'template_purpose': template_purpose
        }
        
        database.save_db(db)
        
        embed = disnake.Embed(
            title=f"📌 Заказ #{str(order_id)}",
            color=disnake.Color.blue()
        )
        embed.add_field(name="🔗 Ссылка на сервер", value=server_link, inline=False)
        embed.add_field(name="📄 Шаблон нужен для...", value=template_purpose[:1024], inline=False)
        
        embed.set_footer(text=f"Заказ от {inter.user}", icon_url=inter.user.avatar.url)
        await inter.response.send_message("Заказ отправлен, ожидайте выполнения!", ephemeral=True)
        
        await self.channel.send(embed=embed, view=TemplateOrder(self.channel))


class TemplateOrder(disnake.ui.View):
    def __init__(self, channel: disnake.TextChannel):
        self.channel = channel
        super().__init__(timeout=None)
    
    @disnake.ui.button(label='Заказать шаблон (БЕСПЛАТНО)', style=disnake.ButtonStyle.green, emoji="✉️")
    async def order_template(self, button: disnake.Button, inter: disnake.Interaction):
        await inter.response.send_modal(modal=TemplateOrderModal(channel=self.channel))
