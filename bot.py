import discord
from discord.ext import commands
import os
import asyncio
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Set up the bot with required intents
intents = discord.Intents.default()
intents.message_content = True  # Required to read message content
intents.members = True # Useful for getting join date

bot = commands.Bot(command_prefix='!', intents=intents)

SUBMISSION_CHANNEL_ID = 1538878995431686184
BOOST_CHANNEL_ID = 1539256731966898216

# Role IDs
ROLE_SUB_ANNOUNCEMENTS = 1538885265941069824
ROLE_ANNOUNCEMENTS = 1538885514353180702
ROLE_GIVEAWAYS = 1538885604782121031

QUESTIONS = [
    ("1. Do you have any moderation experience?", "yesno"),
    ("2. If a moderator abuses his powers what will you do?", "text"),
    ("3. A viral thread descends into chaos—do you lock the thread immediately?", "yesno"),
    ("4. Have you ever been publicly accused of mod abuse or censorship?", "yesno"),
    ("5. Can constructive criticism easily cross the line into harassment?", "yesno"),
    ("6. Is reactive moderation (handling reports after the fact) more effective than strict prevention?", "yesno"),
    ("7. Would you ban a toxic user who technically follows every single rule?", "yesno")
]

class RoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def handle_role(self, interaction: discord.Interaction, role_id: int, role_name: str):
        role = interaction.guild.get_role(role_id)
        if not role:
            await interaction.response.send_message(f"Error: Could not find the {role_name} role. Please contact an admin.", ephemeral=True)
            return

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"Removed the **{role_name}** role.", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"Added the **{role_name}** role.", ephemeral=True)

    @discord.ui.button(label="Announcements", style=discord.ButtonStyle.primary, emoji="📣", custom_id="role_announcements")
    async def btn_announcements(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_role(interaction, ROLE_ANNOUNCEMENTS, "Announcements")

    @discord.ui.button(label="Giveaways", style=discord.ButtonStyle.success, emoji="🎉", custom_id="role_giveaways")
    async def btn_giveaways(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_role(interaction, ROLE_GIVEAWAYS, "Giveaways")

    @discord.ui.button(label="Sub Announcements", style=discord.ButtonStyle.danger, emoji="🎊", custom_id="role_sub_announcements")
    async def btn_sub_announcements(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_role(interaction, ROLE_SUB_ANNOUNCEMENTS, "Sub Announcements")

class YesNoView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=300)
        self.user = user
        self.value = None

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def yes_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.user.id:
            self.value = "Yes"
            await interaction.response.edit_message(view=None)
            self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def no_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.user.id:
            self.value = "No"
            await interaction.response.edit_message(view=None)
            self.stop()

class ApplicationReviewView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def handle_action(self, interaction: discord.Interaction, action: str):
        embed = interaction.message.embeds[0]
        import re
        match = re.search(r'UserId: `(\d+)`', embed.description)
        if not match:
            await interaction.response.send_message("Could not find User ID in embed.", ephemeral=True)
            return

        user_id = int(match.group(1))
        member = interaction.guild.get_member(user_id)

        status_text = ""
        role_text = ""

        if action == "accept":
            status_text = f"✅ Accepted by {interaction.user.mention}"
            if member:
                role = interaction.guild.get_role(1538118635858427974)
                if role:
                    try:
                        await member.add_roles(role)
                        role_text = f"✅ {role.mention} has been added to {member.mention}"
                    except Exception as e:
                        role_text = f"❌ Failed to add role. {e}"
                else:
                    role_text = "❌ Mod role not found."

                try:
                    await member.send("Congrats! youve been selected to be a mod")
                except:
                    pass
            else:
                status_text += " (User not in server)"

        elif action == "reject":
            status_text = f"❌ Rejected by {interaction.user.mention}"
        elif action == "blacklist":
            status_text = f"⛔ Blacklisted by {interaction.user.mention}"

        embed.description += f"\n\n**Status**\n{status_text}"
        if role_text:
            embed.description += f"\n**Role Granted**\n{role_text}"

        if action == "accept":
            embed.color = 0x57F287
        elif action == "reject":
            embed.color = 0xED4245
        elif action == "blacklist":
            embed.color = 0x000000

        await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success, custom_id="review_accept")
    async def btn_accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_action(interaction, "accept")

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger, custom_id="review_reject")
    async def btn_reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_action(interaction, "reject")

    @discord.ui.button(label="Blacklist", style=discord.ButtonStyle.secondary, custom_id="review_blacklist")
    async def btn_blacklist(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_action(interaction, "blacklist")

class ApplyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Apply for Moderator", style=discord.ButtonStyle.primary, custom_id="apply_mod_btn")
    async def apply_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("I have sent you a DM to begin your application!", ephemeral=True)

        user = interaction.user
        answers = []
        start_time = datetime.now(timezone.utc)

        try:
            for q_text, q_type in QUESTIONS:
                if q_type == "yesno":
                    view = YesNoView(user)
                    msg = await user.send(f"**{q_text}**", view=view)
                    await view.wait()
                    if view.value is None:
                        await user.send("Application timed out.")
                        return
                    answers.append((q_text, view.value))
                else:
                    await user.send(f"**{q_text}**")
                    def check(m):
                        return m.author == user and isinstance(m.channel, discord.DMChannel)

                    msg = await bot.wait_for('message', check=check, timeout=300)
                    answers.append((q_text, msg.content))

            end_time = datetime.now(timezone.utc)
            duration = int((end_time - start_time).total_seconds())

            description = ""
            for q, a in answers:
                description += f"**{q}**\n\n{a}\n\n"

            joined_at = "Unknown"
            if hasattr(user, 'joined_at') and user.joined_at:
                days_ago = (datetime.now(timezone.utc) - user.joined_at).days
                if days_ago == 0:
                    joined_at = "today"
                else:
                    joined_at = f"{days_ago} days ago"

            description += (
                f"**Submission stats**\n"
                f"UserId: `{user.id}`\n"
                f"Username: `{user.name}`\n"
                f"User: {user.mention}\n"
                f"Duration: `{duration}s`\n"
                f"Joined guild: `{joined_at}`"
            )

            embed = discord.Embed(
                title=f"{user.name}'s 'Moderator Application' Application Submitted",
                description=description,
                color=0x2b2d31
            )

            if user.avatar:
                embed.set_thumbnail(url=user.avatar.url)

            channel = bot.get_channel(SUBMISSION_CHANNEL_ID)
            if channel:
                await channel.send(embed=embed, view=ApplicationReviewView())
                await user.send("Your application has been submitted successfully!")
            else:
                await user.send("There was an error submitting your application (Submission channel not found). Please contact an admin.")

        except asyncio.TimeoutError:
            await user.send("Your application timed out. Please try again.")
        except discord.Forbidden:
            pass


async def send_boost_embed(channel, member):
    """Sends the boost thank you embed for a given member."""
    embed = discord.Embed(
        title=f"{member.guild.name}'s Boosters Message",
        color=0xf47fff
    )

    embed.description = (
        f"**Thanks for boosting,\n{member.mention}**\n\n"
        f"You Are Now Part Of The Booster Club\n"
        f"Welcome\n\n"
        f"**Carrier Benefits**\n"
        f"🎖️ Skip the queue – get instant help\n"
        f"🎖️ Extra support on every ticket\n"
        f"🎖️ Bypass message requirements\n\n"
        f"**Server Benefits**\n"
        f"🎖️ 30% XP boost for faster leveling\n"
        f"🎖️ Post images, GIFs & edit nickname\n"
        f"🎖️ 2x giveaway entries"
    )

    if member.avatar:
        embed.set_thumbnail(url=member.avatar.url)

    if member.guild.icon:
        embed.set_footer(text=f"{member.guild.name} • Thank you for boosting!", icon_url=member.guild.icon.url)
    else:
        embed.set_footer(text=f"{member.guild.name} • Thank you for boosting!")

    await channel.send(embed=embed)


@bot.event
async def on_member_update(before, after):
    """Fires when a member gets the Server Booster role."""
    booster_role = after.guild.premium_subscriber_role
    if booster_role is None:
        return

    had_boost = booster_role in before.roles
    has_boost = booster_role in after.roles

    if not had_boost and has_boost:
        channel = bot.get_channel(BOOST_CHANNEL_ID)
        if channel:
            await send_boost_embed(channel, after)


@bot.event
async def on_ready():
    bot.add_view(ApplyView())
    bot.add_view(RoleView())
    bot.add_view(ApplicationReviewView())
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('------')

@bot.command()
@commands.has_permissions(administrator=True)
async def roles(ctx):
    try:
        await ctx.message.delete()
    except:
        pass

    description = (
        "| ℹ️ **Stay in the loop!**\n"
        "| Click a button below to toggle your ping roles.\n"
        "| Click again at any time to remove it.\n\n"
        "📣 **Announcement Pings** — Server news & important updates\n"
        "🎉 **Giveaway Pings** — Get notified when giveaways go live\n"
        "🎊 **Sub Announcement Pings** — Minor updates & extra info"
    )

    embed = discord.Embed(
        title="🔔 Notification Pings",
        description=description,
        color=0x2b2d31
    )

    icon_url = ctx.guild.icon.url if ctx.guild.icon else None
    embed.set_footer(text=f"{ctx.guild.name} System • Ping Roles", icon_url=icon_url)
    await ctx.send(embed=embed, view=RoleView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_mod(ctx):
    try:
        await ctx.message.delete()
    except:
        pass

    embed = discord.Embed(
        title="Moderator Application",
        description="Click the button below to start your moderator application.",
        color=0x5865F2
    )
    await ctx.send(embed=embed, view=ApplyView())

@bot.command()
@commands.has_permissions(administrator=True)
async def lockdown(ctx, channel: discord.TextChannel = None):
    channel = channel or ctx.channel
    default_role = ctx.guild.default_role
    overwrite = channel.overwrites_for(default_role)
    overwrite.send_messages = False
    await channel.set_permissions(default_role, overwrite=overwrite)

    embed = discord.Embed(
        title="🔒 Channel Locked",
        description=f"{channel.mention} has been locked down. Only Administrators can send messages now.",
        color=0xED4245
    )
    await ctx.send(embed=embed)
    try:
        await ctx.message.delete(delay=5.0)
    except:
        pass

@bot.command()
@commands.has_permissions(administrator=True)
async def unlock(ctx, channel: discord.TextChannel = None):
    channel = channel or ctx.channel
    default_role = ctx.guild.default_role
    overwrite = channel.overwrites_for(default_role)
    overwrite.send_messages = None
    await channel.set_permissions(default_role, overwrite=overwrite)

    embed = discord.Embed(
        title="🔓 Channel Unlocked",
        description=f"{channel.mention} has been unlocked. Regular users can now send messages.",
        color=0x57F287
    )
    await ctx.send(embed=embed)
    try:
        await ctx.message.delete(delay=5.0)
    except:
        pass

@bot.command()
@commands.has_permissions(administrator=True)
async def test_boost(ctx, member: discord.Member = None):
    """Usage: !test_boost @user"""
    try:
        await ctx.message.delete()
    except:
        pass

    target = member or ctx.author
    channel = bot.get_channel(BOOST_CHANNEL_ID)
    if channel:
        await send_boost_embed(channel, target)
        await ctx.send(f"✅ Test boost message sent for {target.mention}!", delete_after=5)
    else:
        await ctx.send("❌ Boost channel not found! Check the channel ID.", delete_after=5)

@bot.command()
async def ping(ctx):
    try:
        await ctx.message.delete()
    except:
        pass
    await ctx.send('pong!')

if __name__ == '__main__':
    if TOKEN is None:
        print("Error: DISCORD_TOKEN is not set in the .env file.")
    else:
        bot.run(TOKEN)
