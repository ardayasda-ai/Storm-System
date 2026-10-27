import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import datetime
from flask import Flask
from threading import Thread

# -------------------------------------------------------------
# 🌐 Render 7/24 Uykuyu Önleme (Keep-Alive) ve Dinamik Port Altyapısı
# -------------------------------------------------------------
app = Flask('')

@app.route('/')
def home():
    return "StormSystem 7/24 Aktif ve Çalışıyor!"

def run():
    # Render'ın atadığı dinamik portu okuyoruz (Port hata uyarısını çözer)
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# -------------------------------------------------------------
# 🤖 Discord Bot Başlangıç ve Intent Ayarları
# -------------------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

class StormBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Slash komutlarını Discord'a senkronize ediyoruz
        await self.tree.sync()
        print("✨ Tüm Slash (/) komutları senkronize edildi!")

bot = StormBot()

# ID sayacı ve İstatistik verilerini tutmak için dosya yönetimi
ID_FILE = "ticket_data.json"

def load_data():
    if os.path.exists(ID_FILE):
        with open(ID_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_id": 0, "stats": {}}

def save_data(data):
    with open(ID_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_next_ticket_id():
    data = load_data()
    data["last_id"] += 1
    save_data(data)
    return data["last_id"]

def add_staff_stat(staff_id: str):
    data = load_data()
    if "stats" not in data:
        data["stats"] = {}
    data["stats"][staff_id] = data["stats"].get(staff_id, 0) + 1
    save_data(data)

# -------------------------------------------------------------
# 🛡️ 1. /systemlogkurulum Komutu
# -------------------------------------------------------------
@bot.tree.command(name="systemlogkurulum", description="Kapsamlı sistem log kanallarını otomatik kurar.")
@app_commands.checks.has_permissions(administrator=True)
async def system_log_kurulum(interaction: discord.Interaction):
    guild = interaction.guild
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True)
    }

    category = discord.utils.get(guild.categories, name="🛡️ StormSystem Loglar")
    if not category:
        category = await guild.create_category("🛡️ StormSystem Loglar", overwrites=overwrites)

    log_channels = [
        "📋-ticket-log",
        "⚙️-moderatör-işlem-log",
        "🔑-rol-yetki-log",
        "📁-kanal-düzen-log",
        "💬-mesaj-akış-log",
        "👤-üye-giriş-çıkış-log",
        "🎧-ses-sistem-log"
    ]

    created = []
    for channel_name in log_channels:
        existing = discord.utils.get(category.channels, name=channel_name)
        if not existing:
            await guild.create_text_channel(channel_name, category=category)
            created.append(channel_name)

    embed = discord.Embed(
        title="🛡️ **StormSystem Log Kurulumu**",
        description=f"✨ Sistem logları başarıyla oluşturuldu!\n\n**Eklenen Kanallar:**\n" + "\n".join([f"• `{c}`" for c in created]),
        color=discord.Color.dark_theme()
    )
    embed.set_footer(text="discord.gg/stormpack")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# -------------------------------------------------------------
# 🧹 2. /ticketpanelsifirla Komutu
# -------------------------------------------------------------
@bot.tree.command(name="ticketpanelsifirla", description="Ticket kategorisini ve tüm aktif biletleri temizler.")
@app_commands.checks.has_permissions(administrator=True)
async def ticket_panel_sifirla(interaction: discord.Interaction):
    guild = interaction.guild
    category = discord.utils.get(guild.categories, name="🎫 | Destek Talepleri")
    if category:
        for channel in category.channels:
            await channel.delete()
        await category.delete()
        
        embed = discord.Embed(
            title="🧹 **Ticket Sıfırlama İşlemi**",
            description="✨ Ticket kategorisi ve içindeki tüm aktif bilet kanalları başarıyla temizlendi.",
            color=discord.Color.red()
        )
        embed.set_footer(text="discord.gg/stormpack")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message("⚠️ Silinecek aktif bir ticket kategorisi bulunamadı.", ephemeral=True)

# -------------------------------------------------------------
# 🎫 3. /ticketkurulum Komutu
# -------------------------------------------------------------
class TicketSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Genel Destek", style=discord.ButtonStyle.primary, emoji="🛠️", custom_id="ticket_genel")
    async def genel_destek(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "Genel Destek")

    @discord.ui.button(label="Satın Alım", style=discord.ButtonStyle.success, emoji="💸", custom_id="ticket_satin_alim")
    async def satin_alim(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "Satın Alım")

    @discord.ui.button(label="Partnerlik", style=discord.ButtonStyle.secondary, emoji="🤝", custom_id="ticket_partner")
    async def partnerlik(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "Partnerlik")

    async def create_ticket(self, interaction: discord.Interaction, category_name: str):
        guild = interaction.guild
        member = interaction.user
        ticket_id = get_next_ticket_id()

        category = discord.utils.get(guild.categories, name="🎫 | Destek Talepleri")
        if not category:
            overwrites_cat = {
                guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False, add_reactions=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            category = await guild.create_category("🎫 | Destek Talepleri", overwrites=overwrites_cat)

        storm_team = discord.utils.get(guild.roles, name="Storm Team")
        
        overwrites_channel = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        if storm_team:
            overwrites_channel[storm_team] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel_name = f"destek-{ticket_id}"
        ticket_channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites_channel)

        embed = discord.Embed(title=f"🎫 Destek Talebi #{ticket_id}", color=discord.Color.dark_theme())
        embed.description = (
            f"👤 @{member.name} tarafından destek talebi oluşturuldu.\n\n"
            f"📌 **Destek Bilgileri**\n"
            f"🆔 Destek ID `#{ticket_id}`\n"
            f"📁 Kategori `{category_name}`\n\n"
            f"🛡️ **Destek Durumu**\n"
            f"```Yetkili bekleniyor...```"
        )
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        embed.set_footer(text="StormSystem | Ticket Sistemi.")

        view = TicketManagementView(member.id, ticket_id, category_name)
        await ticket_channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"✅ Destek talebiniz oluşturuldu: {ticket_channel.mention}", ephemeral=True)

class TicketManagementView(discord.ui.View):
    def __init__(self, creator_id: int, ticket_id: int, category_name: str):
        super().__init__(timeout=None)
        self.creator_id = creator_id
        self.ticket_id = ticket_id
        self.category_name = category_name
        self.claimed_by = None

    @discord.ui.button(label="Sahiplen", style=discord.ButtonStyle.primary, emoji="👥", custom_id="ticket_claim")
    async def sahiplen(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name="Ticket Sorumlusu")
        if not role or role not in interaction.user.roles:
            await interaction.response.send_message("❌ Bu butonu yalnızca **Ticket Sorumlusu** kullanabilir.", ephemeral=True)
            return

        self.claimed_by = interaction.user
        add_staff_stat(str(interaction.user.id))
        
        button.disabled = True
        button.label = f"Sahiplenildi: {interaction.user.name}"

        msg = interaction.message
        if msg.embeds:
            emb = msg.embeds[0]
            emb.description = emb.description.replace("```Yetkili bekleniyor...```", f"```Sahiplenen Yetkili: {interaction.user.name}```")
            await msg.edit(embed=emb, view=self)

        await interaction.response.send_message(f"✨ Bu ticket **{interaction.user.name}** tarafından üstlenildi!", ephemeral=False)

    @discord.ui.button(label="Kapat", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="ticket_close")
    async def kapat(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.delete()

@bot.tree.command(name="ticketkurulum", description="Destek panelini belirtilen banner ile kurar.")
@app_commands.checks.has_permissions(administrator=True)
async def ticket_kurulum(interaction: discord.Interaction, banner_url: str):
    embed = discord.Embed(title="🎫 **Stormpack Destek Merkezi**", color=discord.Color.dark_theme())
    embed.description = (
        "📋 **Destek Sistemi Kuralları ve Bilgilendirme**\n"
        "• 🛠️ Destek açmak için aşağıdaki butonlardan uygun kategoriyi seçin.\n"
        "• ⚠️ Lütfen gereksiz destek talebi açmaktan kaçının."
    )
    embed.set_image(url=banner_url)
    embed.set_footer(text="discord.gg/stormpack")

    view = TicketSelectView()
    await interaction.channel.send(embed=embed, view=view)
    await interaction.response.send_message("✅ Ticket paneli kuruldu.", ephemeral=True)

# -------------------------------------------------------------
# 📊 4. /ticketsiralama Komutu
# -------------------------------------------------------------
@bot.tree.command(name="ticketsiralama", description="En çok tickete bakan yetkilileri listeler.")
async def ticket_siralama(interaction: discord.Interaction):
    data = load_data()
    stats = data.get("stats", {})
    
    if not stats:
        await interaction.response.send_message("📊 Henüz sonuçlandırılmış ticket verisi bulunmuyor.", ephemeral=True)
        return

    sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)
    description = ""
    for index, (staff_id, count) in enumerate(sorted_stats, start=1):
        member = interaction.guild.get_member(int(staff_id))
        name = member.name if member else f"Yetkili ({staff_id})"
        description += f"**{index}.** • **{name}** — ` {count} Destek `\n"

    embed = discord.Embed(title="🏆 **Stormpack | Yetkili Destek Sıralaması**", description=description, color=discord.Color.gold())
    embed.set_footer(text="discord.gg/stormpack")
    await interaction.response.send_message(embed=embed)

# -------------------------------------------------------------
# 🖼️ 5. /avatar Komutu
# -------------------------------------------------------------
@bot.tree.command(name="avatar", description="Belirtilen kullanıcının avatarını gösterir.")
async def avatar(interaction: discord.Interaction, member: discord.Member = None):
    target = member or interaction.user
    embed = discord.Embed(title=f"🖼️ {target.name} adlı kullanıcının avatarı:", color=discord.Color.dark_theme())
    embed.set_image(url=target.display_avatar.url)
    embed.set_footer(text="discord.gg/stormpack")
    await interaction.response.send_message(embed=embed)

# -------------------------------------------------------------
# 🔑 6. /rolver & /rolal Komutları
# -------------------------------------------------------------
@bot.tree.command(name="rolver", description="Üyeye belirtilen rolü verir.")
@app_commands.checks.has_permissions(manage_roles=True)
async def rol_ver(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    await member.add_roles(role)
    await interaction.response.send_message(f"✅ Başarıyla **{member.name}** adlı kullanıcıya **{role.name}** rolü verildi.")

@bot.tree.command(name="rolal", description="Üyeden belirtilen rolü alır.")
@app_commands.checks.has_permissions(manage_roles=True)
async def rol_al(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    await member.remove_roles(role)
    await interaction.response.send_message(f"✅ Başarıyla **{member.name}** adlı kullanıcıdan **{role.name}** rolü alındı.")

# -------------------------------------------------------------
# 🔇 7. /mute & /unmute Komutları
# -------------------------------------------------------------
@bot.tree.command(name="mute", description="Üyeyi belirli süreyle susturur.")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "Belirtilmedi"):
    duration = discord.utils.utcnow() + datetime.timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    await interaction.response.send_message(f"🔇 **{member.name}** {minutes} dakika süreyle susturuldu.")

@bot.tree.command(name="unmute", description="Üyenin susturmasını kaldırır.")
@app_commands.checks.has_permissions(moderate_members=True)
async def unmute(interaction: discord.Interaction, member: discord.Member):
    await member.timeout(None)
    await interaction.response.send_message(f"🔊 **{member.name}** adlı kullanıcının susturması kaldırıldı.")

# -------------------------------------------------------------
# 🎧 8. /systemseskatıl & /systemsesayrıl Komutları
# -------------------------------------------------------------
@bot.tree.command(name="systemseskatil", description="Botu ses kanalına sokar ve 7/24 aktif tutar.")
@app_commands.checks.has_permissions(administrator=True)
async def system_ses_katil(interaction: discord.Interaction, channel: discord.VoiceChannel):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.move_to(channel)
    else:
        await channel.connect()
    await interaction.response.send_message(f"🎧 **{channel.name}** kanalına giriş yapıldı.", ephemeral=True)

@bot.tree.command(name="systemsesayril", description="Botu ses kanalından çıkarır.")
@app_commands.checks.has_permissions(administrator=True)
async def system_ses_ayril(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("🎧 Ses kanalından ayrıldı.", ephemeral=True)
    else:
        await interaction.response.send_message("⚠️ Bot zaten bir ses kanalında değil.", ephemeral=True)

@bot.event
async def on_ready():
    print(f"{bot.user} olarak giriş yapıldı. StormSystem tamamen aktif ve Slash uyumlu!")

if __name__ == "__main__":
    keep_alive()
    bot.run(os.getenv("DISCORD_TOKEN"))