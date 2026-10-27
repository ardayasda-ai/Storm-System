import discord
from discord.ext import commands
import json
import os
import datetime

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True  # Ses kanalları için gerekli intent

bot = commands.Bot(command_prefix="!", intents=intents)

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
# 🛡️ 1. /systemLogKurulum Komutu (Kapsamlı Log Altyapısı)
# -------------------------------------------------------------
@bot.command(name="systemLogKurulum")
@commands.has_permissions(administrator=True)
async def system_log_kurulum(ctx):
    guild = ctx.guild
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
        description=f"✨ Sistem logları ve ses log kanalı başarıyla oluşturuldu!\n\n**Eklenen Kanallar:**\n" + "\n".join([f"• `{c}`" for c in created]),
        color=discord.Color.dark_theme()
    )
    embed.set_footer(text="discord.gg/stormpack")
    await ctx.send(embed=embed)
    await ctx.message.delete()

# -------------------------------------------------------------
# 🧹 2. /TicketPanelSıfırla Komutu
# -------------------------------------------------------------
@bot.command(name="TicketPanelSıfırla")
@commands.has_permissions(administrator=True)
async def ticket_panel_sifirla(ctx):
    guild = ctx.guild
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
        await ctx.send(embed=embed)
    else:
        await ctx.send("⚠️ Silinecek aktif bir ticket kategorisi bulunamadı.")
    await ctx.message.delete()

# -------------------------------------------------------------
# 🎫 3. /TicketKurulum Komutu ve Panel Görünümü
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
            f"👤 @{member.name} tarafından destek talebi **<t:{int(interaction.created_at.timestamp())}:R>** tarihinde "
            f"oluşturuldu. Yetkililer sizinle ilgilenecektir.\n\n"
            f"📌 **Destek Bilgileri**\n"
            f"🆔 Destek ID `#{ticket_id}`\n"
            f"📁 Destek Kategorisi `{category_name}`\n"
            f"⏱️ Ortalama Yanıt Süresi `2 dakika`\n\n"
            f"🛡️ **Destek Durumu**\n"
            f"```Yetkili bekleniyor...```"
        )
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        embed.set_footer(text="StormSystem | Ticket Sistemi.")

        view = TicketManagementView(member.id, ticket_id, category_name)
        await ticket_channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"✅ Destek talebiniz başarıyla oluşturuldu: {ticket_channel.mention}", ephemeral=True)

class TicketManagementView(discord.ui.View):
    def __init__(self, creator_id: int, ticket_id: int, category_name: str):
        super().__init__(timeout=None)
        self.creator_id = creator_id
        self.ticket_id = ticket_id
        self.category_name = category_name
        self.claimed_by = None

    @discord.ui.button(label="Yetkili - Sahiplen", style=discord.ButtonStyle.primary, emoji="👥", custom_id="ticket_claim")
    async def sahiplen(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name="Ticket Sorumlusu")
        if not role or role not in interaction.user.roles:
            await interaction.response.send_message("❌ Bu butonu yalnızca **Ticket Sorumlusu** rolüne sahip yetkililer kullanabilir.", ephemeral=True)
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

    @discord.ui.button(label="Yetkili - Kapat", style=discord.ButtonStyle.secondary, emoji="💾", custom_id="ticket_close_staff")
    async def yetkili_kapat(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = discord.utils.get(interaction.guild.roles, name="Ticket Sorumlusu")
        if not role or role not in interaction.user.roles:
            await interaction.response.send_message("❌ Bu butonu yalnızca **Ticket Sorumlusu** yetkilileri kullanabilir.", ephemeral=True)
            return
        await self.close_ticket(interaction, kapatan="Yetkili")

    @discord.ui.button(label="Oyuncu - Kapat", style=discord.ButtonStyle.danger, emoji="⚙️", custom_id="ticket_close_user")
    async def oyuncu_kapat(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.creator_id and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Bu butonu sadece talebi açan oyuncu kullanabilir.", ephemeral=True)
            return
        await self.close_ticket(interaction, kapatan="Oyuncu")

    async def close_ticket(self, interaction: discord.Interaction, kapatan: str):
        guild = interaction.guild
        creator = guild.get_member(self.creator_id)
        creator_name = creator.name if creator else f"Bilinmeyen Kullanıcı ({self.creator_id})"
        staff_name = self.claimed_by.name if self.claimed_by else "Sahiplenilmedi"

        log_channel = discord.utils.get(guild.text_channels, name="📋-ticket-log")
        if log_channel:
            log_embed = discord.Embed(title=f"🔒 **Destek Talebi Kapatıldı (#{self.ticket_id})**", color=discord.Color.red())
            log_embed.add_field(name="🆔 Destek ID", value=f"#{self.ticket_id}", inline=True)
            log_embed.add_field(name="📁 Kategori", value=self.category_name, inline=True)
            log_embed.add_field(name="👤 Açan Oyuncu", value=creator_name, inline=True)
            log_embed.add_field(name="👥 Sahiplenen Yetkili", value=staff_name, inline=True)
            log_embed.add_field(name="⚙️ Kapatan Taraf", value=f"{kapatan} ({interaction.user.name})", inline=True)
            log_embed.timestamp = discord.utils.utcnow()
            log_embed.set_footer(text="StormSystem | Kapsamlı Log Sistemi")
            await log_channel.send(embed=log_embed)

        await interaction.response.send_message("⚠️ Destek talebi kapatılıyor ve kanal siliniyor...", ephemeral=True)
        await interaction.channel.delete()

@bot.command(name="TicketKurulum")
@commands.has_permissions(administrator=True)
async def ticket_kurulum(ctx, banner_url: str):
    embed = discord.Embed(title="🎫 **Stormpack Destek Merkezi**", color=discord.Color.dark_theme())
    embed.description = (
        "📋 **Destek Sistemi Kuralları ve Bilgilendirme**\n"
        "• 🛠️ Destek açmak için aşağıdaki butonlardan uygun kategoriyi seçin.\n"
        "• ⚠️ Lütfen gereksiz veya boş yere destek talebi açmaktan kaçının.\n"
        "• ⏱️ Yetkili ekibimiz en kısa sürede talebinizle ilgilenecektir."
    )
    embed.set_image(url=banner_url)
    embed.set_footer(text="discord.gg/stormpack")

    view = TicketSelectView()
    await ctx.send(embed=embed, view=view)
    await ctx.message.delete()

# -------------------------------------------------------------
# 📊 4. /TicketSıralama Komutu (Stormpack Liderlik Tablosu)
# -------------------------------------------------------------
@bot.command(name="TicketSıralama")
async def ticket_siralama(ctx):
    data = load_data()
    stats = data.get("stats", {})
    
    if not stats:
        await ctx.send("📊 Henüz sonuçlandırılmış veya sahiplenilmiş bir ticket verisi bulunmuyor.")
        return

    sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)
    
    description = ""
    for index, (staff_id, count) in enumerate(sorted_stats, start=1):
        member = ctx.guild.get_member(int(staff_id))
        name = member.name if member else f"Yetkili ({staff_id})"
        
        if index == 1:
            medal = "👑"
        elif index == 2:
            medal = "🥈"
        elif index == 3:
            medal = "🥉"
        else:
            medal = f"**{index}.**"
            
        description += f"{medal} • **{name}** — ` {count} Destek `\n"

    embed = discord.Embed(
        title="🏆 **Stormpack | Yetkili Destek Sıralaması**",
        description=description,
        color=discord.Color.gold()
    )
    embed.set_footer(text="discord.gg/stormpack • En aktif yetkililer listesi")
    await ctx.send(embed=embed)
    await ctx.message.delete()

# -------------------------------------------------------------
# 🖼️ 5. /Avatar Komutu (Genel Kullanıcı Komutu)
# -------------------------------------------------------------
@bot.command(name="Avatar")
async def avatar(ctx, member: discord.Member = None):
    target = member or ctx.author
    embed = discord.Embed(title=f"🖼️ {target.name} adlı kullanıcının avatarı:", color=discord.Color.dark_theme())
    embed.set_image(url=target.display_avatar.url)
    embed.set_footer(text="discord.gg/stormpack")
    await ctx.send(embed=embed)

# -------------------------------------------------------------
# 🔑 6. Rol Yönetim Komutları (/rol ver & /rol al)
# -------------------------------------------------------------
@bot.command(name="rolver")
@commands.has_permissions(manage_roles=True)
async def rol_ver(ctx, member: discord.Member, *, role: discord.Role):
    if role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
        await ctx.send("❌ Bu rolü verebilecek yetkiye sahip değilsin (Rol senin yetki seviyenin üstünde).")
        return

    await member.add_roles(role)
    await ctx.send(f"✅ Başarıyla **{member.name}** adlı kullanıcıya **{role.name}** rolü verildi.")

    log_channel = discord.utils.get(ctx.guild.text_channels, name="🔑-rol-yetki-log")
    if log_channel:
        embed = discord.Embed(title="🔑 **Rol Verme İşlemi Gerçekleşti**", color=discord.Color.green())
        embed.add_field(name="👤 İşlem Yapılan Üye", value=f"{member.mention} (`{member.id}`)", inline=True)
        embed.add_field(name="🛡️ Verilen Rol", value=f"`{role.name}`", inline=True)
        embed.add_field(name="👮 İşlem Yapan Yetkili", value=f"{ctx.author.mention}", inline=False)
        embed.timestamp = discord.utils.utcnow()
        embed.set_footer(text="StormSystem | Rol Log Sistemi")
        await log_channel.send(embed=embed)

@bot.command(name="rolal")
@commands.has_permissions(manage_roles=True)
async def rol_al(ctx, member: discord.Member, *, role: discord.Role):
    if role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
        await ctx.send("❌ Bu rolü alabilecek yetkiye sahip değilsin (Rol senin yetki seviyenin üstünde).")
        return

    await member.remove_roles(role)
    await ctx.send(f"✅ Başarıyla **{member.name}** adlı kullanıcıdan **{role.name}** rolü alındı.")

    log_channel = discord.utils.get(ctx.guild.text_channels, name="🔑-rol-yetki-log")
    if log_channel:
        embed = discord.Embed(title="🔑 **Rol Alma İşlemi Gerçekleşti**", color=discord.Color.orange())
        embed.add_field(name="👤 İşlem Yapılan Üye", value=f"{member.mention} (`{member.id}`)", inline=True)
        embed.add_field(name="🛡️ Alınan Rol", value=f"`{role.name}`", inline=True)
        embed.add_field(name="👮 İşlem Yapan Yetkili", value=f"{ctx.author.mention}", inline=False)
        embed.timestamp = discord.utils.utcnow()
        embed.set_footer(text="StormSystem | Rol Log Sistemi")
        await log_channel.send(embed=embed)

# -------------------------------------------------------------
# 🔇 7. Moderasyon Komutları (/mute & /unmute)
# -------------------------------------------------------------
@bot.command(name="mute")
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, minutes: int, *, reason: str = "Belirtilmedi"):
    duration = discord.utils.utcnow() + datetime.timedelta(minutes=minutes)
    try:
        await member.timeout(duration, reason=reason)
        await ctx.send(f"🔇 **{member.name}** adlı kullanıcı {minutes} dakika süreyle susturuldu.")

        log_channel = discord.utils.get(ctx.guild.text_channels, name="⚙️-moderatör-işlem-log")
        if log_channel:
            embed = discord.Embed(title="🔇 **Üye Susturuldu (Timeout)**", color=discord.Color.red())
            embed.add_field(name="👤 Susturulan Üye", value=f"{member.mention} (`{member.id}`)", inline=True)
            embed.add_field(name="⏱️ Süre", value=f"`{minutes} Dakika`", inline=True)
            embed.add_field(name="📄 Sebep", value=f"`{reason}`", inline=False)
            embed.add_field(name="👮 Yetkili", value=f"{ctx.author.mention}", inline=False)
            embed.timestamp = discord.utils.utcnow()
            embed.set_footer(text="StormSystem | Moderasyon Log")
            await log_channel.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Susturma işlemi başarısız oldu: {e}")

@bot.command(name="unmute")
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, member: discord.Member):
    try:
        await member.timeout(None)
        await ctx.send(f"🔊 **{member.name}** adlı kullanıcının susturması kaldırıldı.")

        log_channel = discord.utils.get(ctx.guild.text_channels, name="⚙️-moderatör-işlem-log")
        if log_channel:
            embed = discord.Embed(title="🔊 **Üyenin Susturması Kaldırıldı**", color=discord.Color.green())
            embed.add_field(name="👤 Üye", value=f"{member.mention} (`{member.id}`)", inline=True)
            embed.add_field(name="👮 Yetkili", value=f"{ctx.author.mention}", inline=False)
            embed.timestamp = discord.utils.utcnow()
            embed.set_footer(text="StormSystem | Moderasyon Log")
            await log_channel.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Susturma kaldırılamadı: {e}")

# -------------------------------------------------------------
# 🎧 8. Ses Kanalı Komutları (/systemseskatıl & /systemsesayrıl)
# -------------------------------------------------------------
@bot.command(name="systemseskatıl")
@commands.has_permissions(administrator=True)
async def system_ses_katil(ctx, *, channel: discord.VoiceChannel):
    try:
        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()

        await ctx.send(f"🎧 Başarıyla **{channel.name}** ses kanalına giriş yapıldı ve 7/24 aktif konuma getirildi.")

        log_channel = discord.utils.get(ctx.guild.text_channels, name="🎧-ses-sistem-log")
        if log_channel:
            embed = discord.Embed(title="🎧 **Bot Ses Kanalına Katıldı (7/24)**", color=discord.Color.blue())
            embed.add_field(name="🔊 Ses Kanalı", value=f"`{channel.name}` (`{channel.id}`)", inline=True)
            embed.add_field(name="👮 İşlem Yapan Yetkili", value=f"{ctx.author.mention}", inline=False)
            embed.timestamp = discord.utils.utcnow()
            embed.set_footer(text="StormSystem | Ses Log Sistemi")
            await log_channel.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Ses kanalına katılırken bir hata oluştu: {e}")

@bot.command(name="systemsesayrıl")
@commands.has_permissions(administrator=True)
async def system_ses_ayril(ctx):
    if ctx.voice_client:
        channel_name = ctx.voice_client.channel.name
        await ctx.voice_client.disconnect()
        await ctx.send("🎧 Bot ses kanalından ayrıldı.")

        log_channel = discord.utils.get(ctx.guild.text_channels, name="🎧-ses-sistem-log")
        if log_channel:
            embed = discord.Embed(title="🎧 **Bot Ses Kanalından Ayrıldı**", color=discord.Color.orange())
            embed.add_field(name="🔊 Ayrılan Kanal", value=f"`{channel_name}`", inline=True)
            embed.add_field(name="👮 İşlem Yapan Yetkili", value=f"{ctx.author.mention}", inline=False)
            embed.timestamp = discord.utils.utcnow()
            embed.set_footer(text="StormSystem | Ses Log Sistemi")
            await log_channel.send(embed=embed)
    else:
            await ctx.send("⚠️ Bot halihazırda bir ses kanalında bulunmuyor.")

@bot.event
async def on_ready():
    print(f"{bot.user} olarak giriş yapıldı. StormSystem tamamen aktif!")

bot.run(os.getenv("DISCORD_TOKEN"))