from redbot.core import commands
from redbot.core.bot import Red
import discord
import random
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS

DICE_EMOJI = '\U0001F3B2'
SWORD_EMOJI = '\U00002694'
SHIELD_EMOJI = '\U0001F6E1'
EVADE_EMOJI = '\U0001F4A8'

class Player():
    def __init__(self, **kwargs):
        self.author = kwargs.get('author')
        self.name = kwargs.get('name')
        self.roll = kwargs.get('roll')
        self.max_hp = kwargs.get('max_hp')
        self.hp = kwargs.get('hp')
        self.atk = kwargs.get('atk')
        self.dfn = kwargs.get('dfn')
        self.evd = kwargs.get('evd')
        self.first = kwargs.get('first')
        self.embed = kwargs.get('embed')


class SBIST(commands.Cog):
    """My custom cog"""
    
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.message = None
        self.turns = 1
        self.player_one = None
        self.player_two = None
        self.waiting_on_player_one = False
        self.waiting_on_player_two = False
        self.in_progress = False
        self.text = ''
        self.calculating = False

    # GAME SETUP 
    @commands.command()
    async def sbistest (self, ctx):
        if ctx.message.mentions:
            self.player_one = Player(author=ctx.message.author, name=ctx.message.author.name, roll=0, hp=5, max_hp=5, atk=0,dfn=0,evd=0,first=True)
            self.player_two = Player(author=ctx.message.mentions[0], name=ctx.message.mentions[0].name, roll=0, hp=5, max_hp=5, atk=0,dfn=0,evd=0,first=False)
            
            self.text = await ctx.send(':stars:  |  **{}** has challenged **{}** to **Squanch Battle: In-Finite[st]**!\n__**Turn {}**__'.format(self.player_one.name, self.player_two.name,self.turns))
            
            self.in_progress = True
            
            #while self.in_progress:
            self.player_one.embed = await ctx.send(embed=self.battle_meter(self.player_one))
            self.message = self.player_one.embed
            self.player_two.embed = await ctx.send(embed=self.battle_meter(self.player_two))
            self.waiting_on_player_one = True
            self.text = await ctx.send("Waiting {}'s on attack roll.".format(self.player_one.name))
            await self.message.add_reaction(SWORD_EMOJI)
   
    def reset(self):
        self.message = None
        self.turns = 1
        self.player_one = None
        self.player_two = None
        self.waiting_on_player_one = False
        self.waiting_on_player_two = False
        self.in_progress = False
        self.text = ''
    
    def roll (self):
        return random.randint(1,6)
    
    def swap_turns(self):
        self.waiting_on_player_one = True if self.waiting_on_player_one == False else False
        self.waiting_on_player_two = True if self.waiting_on_player_two == False else False
        
    def swap_first(self):
        self.player_one.first = 1 if self.player_one.first == 0 else 0
        self.player_two.first = 1 if self.player_two.first == 0 else 0
        self.player_one.roll = 0
        self.player_two.roll = 0
    
    def check_health(self):
        if self.player_one.hp <= 0:
            return 1
        elif self.player_two.hp <= 0:
            return 2
        else:
            return 0
    
    def battle_meter(self, player):
        em = discord.Embed(title='', description='', colour=player.author.color)
        em.set_thumbnail(url=player.author.avatar_url).set_author(
            name=player.author.display_name)
        if player.hp < 0:
            player.hp = 0
        hp = 'HP: {}/{}'.format(player.hp, player.max_hp)
        if player.first == True:
            hp += ' :crossed_swords:'
        else:
            hp += ' :shield:' 
        life = ''
        for i in range(player.hp):
            life +=':heart:'
        for i in range(player.max_hp-player.hp):
            life +=':black_heart:'
        em.add_field(name=hp, value=life)
        return em       
    
    # GAME LOGIC
    async def on_raw_reaction_add(self, payload):
        if self.in_progress and self.message != None:
            if self.message.id == payload.message_id:
                if self.waiting_on_player_one == True:
                    player = self.player_one
                    opponent = self.player_two
                else: 
                    player = self.player_two
                    opponent = self.player_one
                if payload.user_id == player.author.id and self.calculating != True:
                    if player.first == 1:
                        if payload.emoji.name == SWORD_EMOJI:
                            self.calculating == True
                            player.roll = self.roll()
                            await player.embed.clear_reactions()
                            self.swap_turns()
                            await self.text.channel.send("{} rolled a {}!\nWaiting on {}'s defensive action.".format(player.name,player.roll,opponent.name))
                            await opponent.embed.add_reaction(SHIELD_EMOJI)
                            await opponent.embed.add_reaction(EVADE_EMOJI)
                            self.message = opponent.embed
                            self.calculating == False
                    else:
                        defense = [SHIELD_EMOJI, EVADE_EMOJI]
                        if payload.emoji.name in defense:
                            self.calculating == True
                            player.roll = self.roll()
                            print('rolled')
                            await self.text.channel.send("{} rolled a {}!".format(player.name ,player.roll))
                            damage = 0
                            damage_text = ''
                            if payload.emoji.name == SHIELD_EMOJI:
                                print('blocked')
                                damage = opponent.roll - player.roll if player.roll < opponent.roll else 1
                                damage_text = '{} blocked and took {} damage.'.format(player.name, damage)
                            elif payload.emoji.name == EVADE_EMOJI:
                                print('dodged')
                                damage = 0 if player.roll > opponent.roll else opponent.roll
                                damage_text = '{} successfully dodged the attack!'.format(player.name, damage) if damage == 0 else '{} tried to dodge but took {} damage.'.format(player.name, damage)
                            await self.text.channel.send(damage_text)
                            await player.embed.clear_reactions()
                            if player.name == self.player_one.name:
                                self.player_one.hp = self.player_one.hp - damage
                            else:
                                self.player_two.hp = self.player_two.hp - damage
                            self.calculating == False
                            #END OF TURN
                            self.swap_first()
                            await self.player_one.embed.edit(embed=self.battle_meter(self.player_one))
                            await self.player_two.embed.edit(embed=self.battle_meter(self.player_two))
                            
                            game_done = self.check_health()
                            if game_done == 0:
                                self.message = self.player_two.embed if self.player_two.first == 1 else self.player_one.embed
                                await self.message.add_reaction(SWORD_EMOJI)
                            elif game_done == 1:
                                await self.text.channel.send("{} won!".format(self.player_two.name))
                                self.reset()
                            else:
                                await self.text.channel.send("{} won!".format(self.player_one.name))
                                self.reset()
                        
def setup(bot):
    bot.add_cog(SBIST(bot))
