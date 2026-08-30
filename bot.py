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

MOD_APP_CHANNEL_ID = 1500190383693627463

# Role IDs
ROLE_SUB_ANNOUNCEMENTS = 1538885265941069824
ROLE_ANNOUNCEMENTS = 1538885514353180702
ROLE_GIVEAWAYS = 1538885604782121031
ROLE_JUNIOR_MODERATOR = 1543582430634704946

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

class AppDecisionView(discord.ui.View):
    def __init__(self, applicant):
        super().__init__(timeout=None)
        self.applicant = applicant

    async def _update_message(self, interaction: discord.Interaction, status: str, color: int):
        embed = interaction.message.embeds[0]
        embed.color = color
        embed.set_footer(text=f"Application {status}")
        await interaction.message.edit(embed=embed, view=None)

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green, custom_id="mod_app_accept")
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("You do not have permission to accept applications.", ephemeral=True)
            return

        member = interaction.guild.get_member(self.applicant.id)
        if not member:
            await interaction.response.send_message("The applicant is no longer in this server.", ephemeral=True)
            return

        role = interaction.guild.get_role(ROLE_JUNIOR_MODERATOR)
        if not role:
            await interaction.response.send_message("Junior Moderator role not found.", ephemeral=True)
            return

        await member.add_roles(role)
        await self._update_message(interaction, "Accepted", 0x57F287)
        await interaction.response.send_message(f"Accepted {self.applicant.mention} and gave them the Junior Moderator role.", ephemeral=False)

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.red, custom_id="mod_app_reject")
    async def reject_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("You do not have permission to reject applications.", ephemeral=True)
            return

        await self._update_message(interaction, "Rejected", 0xED4245)
        await interaction.response.send_message(f"Rejected {self.applicant.mention}'s application.", ephemeral=False)

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
                    
            # All answered, format embed
            end_time = datetime.now(timezone.utc)
            duration = int((end_time - start_time).total_seconds())
            
            # Format body
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
                color=0x2b2d31 # Discord dark theme colorish
            )
            
            if user.avatar:
                embed.set_thumbnail(url=user.avatar.url)

            try:
                mod_app_channel = await bot.fetch_channel(MOD_APP_CHANNEL_ID)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                mod_app_channel = None

            if mod_app_channel:
                await mod_app_channel.send(embed=embed, view=AppDecisionView(user))
                await user.send("Your application has been submitted successfully!")
            else:
                await user.send("There was an error submitting your application (Moderator application channel not found or inaccessible). Please contact an admin.")

        except asyncio.TimeoutError:
            await user.send("Your application timed out. Please try again.")
        except discord.Forbidden:
            pass # Cannot send DM


@bot.event
async def on_ready():
    bot.add_view(ApplyView())
    bot.add_view(RoleView())
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('------')

@bot.command()
@commands.has_permissions(administrator=True)
async def roles(ctx):
    """Sets up the self-assignable roles message."""
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
    
    # Try to set server icon as footer icon if available
    icon_url = ctx.guild.icon.url if ctx.guild.icon else None
    embed.set_footer(text=f"{ctx.guild.name} System • Ping Roles", icon_url=icon_url)

    await ctx.send(embed=embed, view=RoleView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_mod(ctx):
    """Sets up the moderator application message in the current channel."""
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
    """Locks a channel so regular users cannot send messages."""
    channel = channel or ctx.channel
    
    # Get the @everyone role
    default_role = ctx.guild.default_role
    
    # Overwrite permissions for @everyone to prevent sending messages
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
    """Unlocks a channel so regular users can send messages again."""
    channel = channel or ctx.channel
    
    default_role = ctx.guild.default_role
    
    overwrite = channel.overwrites_for(default_role)
    overwrite.send_messages = None # Reset to default
    
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
async def ping(ctx):
    """Answers with pong!"""
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
