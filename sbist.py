from redbot.core import commands
from redbot.core.bot import Red
import discord
import random
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
import time
from redbot.core import Config

DICE_EMOJI = '\U0001F3B2'
SWORD_EMOJI = '\U00002694'
SHIELD_EMOJI = '\U0001F6E1'
EVADE_EMOJI = '\U0001F4A8'
ROUND_EMOJI = '\U0001F3C6'
GRAPPLE_EMOJI = '\U0001F40D'
SHIELD_THROW_EMOJI = '\U0001F6E1'

class_icon_dict = {
    'adventurer': ':dagger:',
    'paladin': '<:c_cleric_paladin:570747429633130537>',
    'luchador': ':wrestlers:',
    'blackboss': ':busts_in_silhouette:',
    'berserker': ':rage:'
}

class_dict = {
    'adventurer': {
        'hp' : 5,
        'atk': 0,
        'def': 0,
        'evd': 0
    },
    'paladin': {
        'hp' : 5,
        'atk': -1,
        'def': 2,
        'evd': -1
    },
    'luchador': {
        'hp' : 4,
        'atk': -1,
        'def': -1,
        'evd': 2,
    },
    'blackboss': {
        'hp' : 4,
        'atk': 2,
        'def': -1,
        'evd': -2,
    },
    'berserker': {
        'hp' : 3,
        'atk': 2,
        'def': -2,
        'evd': 1,
    },
}

class_name_dict = {
    'adventurer' : 'Adventurer',
    'paladin' : 'Paladin',
    'luchador' : 'Luchador',
    'blackboss' : 'Black Boss',
    'berserker' : 'Berserker',
    }

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
        self.rounds = kwargs.get('rounds')
        self.died = kwargs.get('died')
        self.class_name = kwargs.get('class_name')

class SBIST(commands.Cog):
    """My custom cog"""
    
    def __init__(self, bot):
        super().__init__()
        self.config = Config.get_conf(self, identifier=1234567890)
        default_user = {
            'user_data': {
                        'registered': False,
                        'class_name': 'adventurer',
                        'win': 0,
                        'loss': 0,
                        'level': 1,
                        'xp': 0,
                        'elo': 1200,
                        'battle': 'https://www.youtube.com/watch?v=lWHgMcIOsuw',
                        'victory': 'https://www.youtube.com/watch?v=-YCN-a0NsNk',
                        }
                    }
        self.config.register_user(**default_user)
        
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
        self.delete = []
        
        self.channel = self.bot.get_channel(570836980271808522)
        self.ctx = None  
        
        
    # GAME SETUP 
    @commands.command()
    async def sbistest (self, ctx):
        registered = await self.config.user(ctx.author).user_data.registered() == True
        if registered == True: 
            if ctx.message.mentions:
                if ctx.message.mentions[0].id != ctx.message.author.id:
                    registered = await self.config.user(ctx.message.mentions[0]).user_data.registered() == True
                    if registered == True: 
                        if self.ctx == None:
                            self.ctx = await self.bot.get_context(await self.channel.send('text'))
                            self.ctx.message.author = ctx.author
                        
                        self.reset()
                        
                        self.player_one = self.create_player(ctx.message.author, await self.config.user(ctx.message.author).user_data.class_name())
                        self.player_two = self.create_player(ctx.message.mentions[0], await self.config.user(ctx.message.mentions[0]).user_data.class_name())
                        
                        self.text = await ctx.send(':stars:  |  **{}** has challenged **{}** to **Squanch Battle: In-Finite[st]**!'.format(self.player_one.name, self.player_two.name))
                        
                        self.in_progress = True
                        
                        if self.player_one.class_name == 'blackboss':
                            player = self.player_two
                            self.waiting_on_player_two = True
                            self.player_two.first = True
                        elif self.player_two.class_name == 'blackboss':
                            player = self.player_one
                            self.waiting_on_player_one = True
                            self.player_one.first = True
                        else:
                            coin_flip = random.randint(0,1)
                            player = self.player_one if coin_flip == 0 else self.player_two
                            self.player_one.first = True if coin_flip == 0 else False
                            self.player_two.first = False if coin_flip == 0 else True
                            self.waiting_on_player_one = True if coin_flip == 0 else False
                            self.waiting_on_player_two = False if coin_flip == 0 else True
                        
                        self.player_one.embed = await ctx.send(embed=self.battle_meter(self.player_one))
                        self.player_two.embed = await ctx.send(embed=self.battle_meter(self.player_two))
                            
                        self.message = player.embed
                        self.text = await ctx.send("\n__**Turn {}**__\nWaiting {}'s on attack roll.".format(self.turns,player.name))
                        self.delete.append(self.text)
                        await self.set_attack_reactions(player)
                        
                        audio = self.bot.get_cog('Audio')
                        stop = audio.bot.get_command('stop')
                        play = audio.bot.get_command('play')
                        await self.ctx.invoke(stop)
                        theme = await self.get_theme(1,random.choice([self.player_one.author, self.player_two.author]))
                        await self.ctx.invoke(play, query=theme)
                    else:
                        await self.embed_msg(ctx, '{} has not registered a class for SBI[ST] yet.'.format(ctx.message.mentions[0].name))
        else:
            await self.embed_msg(ctx, 'You have not registered a class for SBI[ST] yet.')
                
    @commands.group()
    async def profile(self, ctx):
        """"""
        pass 
        
    @profile.command()
    async def stats(self, ctx):
        """See your Squanch Battle In-Finite[st] stats."""
        registered = await self.config.user(ctx.author).user_data.registered() == True
        if registered == True:
            if ctx.message.mentions:
                targetUser = ctx.message.mentions[0]
            else:
                targetUser = ctx.message.author
            user_data = await self.config.user(targetUser).user_data()
            
            em = discord.Embed(title='', description='', colour=targetUser.color)
            em.set_thumbnail(url=targetUser.avatar_url).set_author(name=targetUser.display_name,
                                                                   icon_url=targetUser.avatar_url)
            str = 'Class: {} {}\nLevel: {} ({}/{})'.format(class_name_dict[user_data['class_name']], class_icon_dict[user_data['class_name']],
                                                           user_data['level'], user_data['xp'], self.getXP(user_data['level']))
            em.add_field(name='Information', value=str)
            winrate = 0
            loserate = 0
            if user_data['win'] > 0:
                winrate = user_data['win'] / (user_data['win'] + user_data['loss'])
            if user_data['loss'] > 0:
                loserate = user_data['loss'] / (user_data['win'] + user_data['loss'])
            str = 'Wins: {} - {}%\nLosses: {} - {}%\n'.format(user_data['win'], round(winrate * 100), user_data['loss'],
                                                                       round(loserate * 100))
            em.add_field(name='Statistics', value=str)
            em.add_field(name='Themes', value='{}, {}'.format(user_data['battle'], user_data['victory']))
            await ctx.send(embed=em)
        else:
            await self.embed_msg(ctx, 'You have not registered a class for SBI[ST] yet.')
    
    @profile.command()
    async def battletheme(self, ctx, url: str):
        """Set your custom battle theme."""
        registered = await self.config.user(ctx.author).user_data.registered() == True
        if registered == True:
            if url == '':
                await self.embed_msg(ctx,'Please enter a URL.')
            else:
                await self.config.user(ctx.author).user_data.battle.set(url)
                await self.embed_msg(ctx,'You have successfully updated your battle theme.')
        else:
            await self.embed_msg(ctx, 'You have not registered a class for SBI[ST] yet.')
            
    @profile.command()
    async def victorytheme(self, ctx, url: str):
        """Set your custom victory theme."""
        registered = await self.config.user(ctx.author).user_data.registered() == True
        if registered == True:
            if url == '':
                await self.embed_msg(ctx,'Please enter a URL.')
            else:
                await self.config.user(ctx.author).user_data.victory.set(url)
                await self.embed_msg(ctx,'You have successfully updated your victory theme.')
        else:
            await self.embed_msg(ctx, 'You have not registered a class for SBI[ST] yet.')
    
    @commands.command()
    async def register(self, ctx, classtype: str):
        """Register your class for Squanch Battle In-Finite[st]."""
        if classtype != '':
            if await self.config.user(ctx.author).user_data.registered() == False:
                classtype = classtype.lower()
                classes = list(class_name_dict.keys())
                if classtype in classes:
                    await self.config.user(ctx.author).user_data.class_name.set(classtype)
                    await self.config.user(ctx.author).user_data.registered.set(True)
                    await self.embed_msg(ctx, 'You have successfully registered your class as {}.'.format(class_name_dict[classtype]))
                else:
                    await self.embed_msg(ctx, 'You did not enter a valid class.')
            else:
                await self.embed_msg(ctx, 'You have already registered a class.')
        
    
    @commands.command()
    async def change(self, ctx, classtype: str):
        """Change your class for Squanch Battle In-Finite[st]."""
        if not self.in_progress:
            if await self.config.user(ctx.author).user_data.registered() == True:
                classtype = classtype.lower()
                classes = list(class_name_dict.keys())
                if classtype in classes:
                    await self.config.user(ctx.author).user_data.class_name.set(classtype)
                    em = discord.Embed(title='Class Change', description='{} You have successfully changed your class to {}.'.format(ctx.message.author.mention, class_name_dict[classtype]), colour=0x2ecc71)
                    await ctx.send(embed=em)
                else:
                    em = discord.Embed(title='Class Change', description='{} You did not enter a valid class.'.format(ctx.message.author.mention, colour=0xe74c3c))
                    await ctx.send(embed=em)
            else:
                await self.embed_msg(ctx, 'You have not registered a class yet.')
                
    @commands.command()
    async def matchup(self, ctx, class_type: str):
        if not self.in_progress:
            if class_type in list(class_name_dict.keys()):
                start = time.time()
                total_wins = 0
                total_loss = 0
                run_num = 10000
                result_text = ':crossed_swords:  |  **P1 Matchup Results for {}**\n\n'.format(class_type)
                result_text += '```Python\nSimulations: {}\n-------------------------------------\n'.format(run_num)
                classes = list(class_name_dict.keys())
                for key in classes:
                    if class_type != key:
                        wins = await self.simulate(run_num, class_type, key, ctx) 
                        result_text += 'Vs. {}: {} / {} - {}%\n'.format(key, wins[0], wins[1],
                                                                        round((wins[0] / (wins[0] + wins[1]) * 100), 2))
                        total_wins += wins[0]
                        total_loss += wins[1]
                result_text +='Average Win Rate: {}%\n'.format(round((total_wins / (total_wins + total_loss) * 100), 2))
                end = time.time()
                result_text += '-------------------------------------\n{} seconds elapsed.'.format(round(end - start, 2))
                result_text += '```'
                await ctx.send(result_text)
                
                start = time.time()
                total_wins = 0
                total_loss = 0
                run_num = 10000
                result_text = ':crossed_swords:  |  **P2 Matchup Results for {}**\n\n'.format(class_type)
                result_text += '```Python\nSimulations: {}\n-------------------------------------\n'.format(run_num)
                classes = list(class_name_dict.keys())
                for key in classes:
                    if class_type != key:
                        wins = await self.simulate(run_num, class_type, key, ctx, True) 
                        result_text += 'Vs. {}: {} / {} - {}%\n'.format(key, wins[0], wins[1],
                                                                        round((wins[0] / (wins[0] + wins[1]) * 100), 2))
                        total_wins += wins[0]
                        total_loss += wins[1]
                result_text +='Average Win Rate: {}%\n'.format(round((total_wins / (total_wins + total_loss) * 100), 2))
                end = time.time()
                result_text += '-------------------------------------\n{} seconds elapsed.'.format(round(end - start, 2))
                result_text += '```'
                await ctx.send(result_text)
            else:
                em = discord.Embed(title='Matchup Simulation', description='{} You did not enter a valid class.'.format(ctx.message.author.mention, colour=0xe74c3c))
                await ctx.send(embed=em)
        else:
            await self.embed_msg(ctx, 'You cannot run a matchup simulation while a match is in progress.')
        
    async def simulate(self, run_num: int, class_one: str, class_two: str, ctx, second: bool = False):
        if second == True:
            player_one = self.create_sim_player(class_one, False)
            player_two = self.create_sim_player(class_two, True)
        else:
            player_one = self.create_sim_player(class_one, True)
            player_two = self.create_sim_player(class_two, False)
        class_one_wins = 0
        class_two_wins = 0
        i = 0
        
        while i < run_num:
            while player_one.rounds != 2 and player_two.rounds != 2:
                if player_one.first == True:
                    player = player_one
                    opponent = player_two
                elif player_two.first == True:
                    player = player_two
                    opponent = player_one
                player.roll = self.roll() + player.atk
                opponent.roll = self.roll()
                choice = self.seagull_sim(opponent.hp, opponent.dfn, opponent.evd, player.roll)
                damage = 0
                if player.class_name == 'luchador':
                    choice = 2
                if choice == 1:
                    opponent.roll += opponent.dfn
                    opponent.roll = 1 if opponent.roll <= 0 else opponent.roll
                    damage = player.roll - opponent.roll if opponent.roll < player.roll else 1
                elif choice == 2:
                    opponent.roll += opponent.evd
                    damage = 0 if opponent.roll > player.roll else player.roll
                opponent.hp -= damage
                #print('{} took {} damage and has {} health'.format(opponent.class_name, damage, opponent.hp))
                #await ctx.send('{} took {} damage and has {} health'.format(opponent.class_name, damage, opponent.hp))
                
                #update health
                if player_one.first == True:
                    player_two.hp = opponent.hp
                elif player_two.first == True:
                    player_one.hp = opponent.hp
                    
                if player.class_name == 'paladin' and player.roll > opponent.roll and player.hp > 0 and choice == 1:
                    shield_damage = player.roll  - opponent.roll if (player.roll - opponent.roll) <= 2 else 2
                    if player_two.first == True:
                        player_one.hp -= shield_damage
                    else:
                        player_two.hp -= shield_damage
                        
                #check if anyone is dead
                if player_one.hp <= 0:
                    #print('{} died'.format(player_one.class_name))
                    #await ctx.send('{} died'.format(player_one.class_name))
                    player_one.hp = player_one.max_hp
                    if player_one.class_name == 'berserker':
                        player_one = self.swap_stats(player_one, 3, -3, 1)
                    player_two.rounds += 1
                elif player_two.hp <= 0:
                    #print('{} died'.format(player_two.class_name))
                    #await ctx.send('{} died'.format(player_two.class_name))
                    player_two.hp = player_two.max_hp
                    if player_two.class_name == 'berserker':
                        player_two = self.swap_stats(player_two, 3, -3, 1)
                    player_one.rounds += 1
                #print('{} {}'.format(player_one.rounds, player_two.rounds))
                if player_one.rounds == 2 or player_two.rounds == 2:
                    break
                    
                #swap turns
                player_one.first = 1 if player_one.first == 0 else 0
                player_two.first = 1 if player_two.first == 0 else 0
                player_one.roll = 0
                player_two.roll = 0
            if player_one.rounds == 2:
                #print('{} won'.format(player_one.class_name))
                #await ctx.send('{} won'.format(player_one.class_name))
                class_one_wins += 1
            elif player_two.rounds == 2:
                #print('{} won'.format(player_two.class_name))
                #await ctx.send('{} won'.format(player_two.class_name))
                class_two_wins += 1
            if second == True:
                    player_one = self.create_sim_player(class_one, False)
                    player_two = self.create_sim_player(class_two, True)
            else:
                    player_one = self.create_sim_player(class_one, True)
                    player_two = self.create_sim_player(class_two, False)
            i += 1
        return [class_one_wins, class_two_wins]  
    
    async def get_theme(self, type: int, player):
        if type == 1:
            return await self.config.user(player).user_data.battle()
        if type == 2:
            return await self.config.user(player).user_data.victory()
            
    def seagull_sim(self, hp: int, def_: int, evd: int, roll: int):
            avg_def = 0
            pct_def = 0
            min_def = 0
            avg_evd = 0
            pct_evd = 0
            min_evd = 0
            
            # DEF CALCULATIONS
            for x in range(1,7):
                def_calc = x + def_
                if (def_calc) <= 0:
                    def_calc = 1
                if (def_calc) >= roll:
                    dmg_taken = 1
                else:
                    dmg_taken = roll - (def_calc)
                if dmg_taken < hp:
                    pct_def += 1
                    if min_def == 0:
                        min_def = x
                avg_def += dmg_taken
            avg_def = avg_def/6
            pct_def = pct_def/6
            # EVD CALCULATIONS
            for x in range(1,7):
                dmg_taken = 0
                if (x+evd) <= roll:
                    dmg_taken = roll
                if dmg_taken < hp:
                    pct_evd += 1
                    if min_evd == 0:
                        min_evd = x
                avg_evd += dmg_taken
            avg_evd = avg_evd/6
            pct_evd = pct_evd/6
            
            if pct_evd == 0 and pct_def == 0:
                return 1
            elif pct_evd == pct_def:
                if avg_evd < avg_def:
                    return 2
                else:
                    return 1
            elif pct_evd > pct_def:
                return 2
            else:
                return 1
            
            
    def create_sim_player(self, class_name, first_check):
        result = Player(
            roll=0,
            max_hp=class_dict[class_name]['hp'],
            hp=class_dict[class_name]['hp'],
            atk=class_dict[class_name]['atk'],
            dfn=class_dict[class_name]['def'],
            evd=class_dict[class_name]['evd'],
            first=first_check,
            rounds=0,
            class_name=class_name
        )
        return result
        
    def create_player(self, player, class_name, first_check: bool = False):
        result = Player(
            author=player,
            name=player.name,
            roll=0,
            max_hp=class_dict[class_name]['hp'],
            hp=class_dict[class_name]['hp'],
            atk=class_dict[class_name]['atk'],
            dfn=class_dict[class_name]['def'],
            evd=class_dict[class_name]['evd'],
            first=first_check,
            rounds=0,
            dies=False,
            class_name=class_name
        )
        
        return result
        
    def swap_stats(self, player, atk, dfn, evd):
        player.atk = atk
        player.dfn = dfn
        player.evd = evd
        return player
        
    def getXP(self, level):
        result = (69 + (30 * level))
        return result
        
    def reset(self):
        self.message = None
        self.turns = 1
        self.player_one = None
        self.player_two = None
        self.waiting_on_player_one = False
        self.waiting_on_player_two = False
        self.in_progress = False
        self.text = ''
        self.delete = []
    
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
            
    def check_rounds(self):
        if self.player_one.rounds == 2:
            return 1
        elif self.player_two.rounds == 2:
            return 2
        else:
            return 0
            
    def battle_meter(self, player):
        em = discord.Embed(title='', description='', colour=player.author.color)
        em.set_thumbnail(url=player.author.avatar_url).set_author(
            name=player.author.display_name)
        if player.hp < 0:
            player.hp = 0
        hp = 'HP: {}/{} {}'.format(player.hp, player.max_hp, class_icon_dict[player.class_name])
        if player.rounds > 0:
            hp += ' :trophy:' if player.rounds == 1 else ' :trophy: :trophy:'
        life = ''
        for i in range(player.hp):
            if player.died:
                life+=':broken_heart:'
            else:
                life +=':heart:'
        for i in range(player.max_hp-player.hp):
            life +=':black_heart:'
        if player.first == True:
            life += ' :crossed_swords:'
        else:
            life += ' :shield:' 
        em.add_field(name=hp, value=life)
        em.add_field(name='ATK/DEF/EVD', value='{}/{}/{}'.format(self.add_sign(player.atk),self.add_sign(player.dfn), self.add_sign(player.evd)),inline=False)
        actions = ''
        if player.first == 1:
            actions = 'Attack'
            if player.class_name == 'luchador':
                actions += ', Anaconda Squeeze'
        elif player.first == 0:
            actions = 'Defend, Evade'
        em.add_field(name='Actions', value=actions)
        return em 
        
    def add_sign(self, number):
        if number == 0:
            return '±'+str(number)
        elif number > 0:
            return '+'+str(number)
        else:
            return number
            
    async def set_attack_reactions(self, player):
        attack = [SWORD_EMOJI]
        if player.class_name == 'luchador':
            attack.append(GRAPPLE_EMOJI)
        for emoji in attack:
            await self.message.add_reaction(emoji)
    
    async def embed_msg(self, ctx, title):
        embed = discord.Embed(colour=await ctx.embed_colour(), title=title)
        await ctx.send(embed=embed)
        
    async def update_battle_meter(self):
        await self.player_one.embed.edit(embed=self.battle_meter(self.player_one))
        await self.player_two.embed.edit(embed=self.battle_meter(self.player_two))
        
    async def on_message(self, message):
        if message.author != self.bot.user:
            if self.in_progress == True:
                if message.channel.id == self.text.channel.id:
                    print('adding deleted message')
                    self.delete.append(message)
                
    # GAME LOGIC
    async def on_raw_reaction_add(self, payload):
        if self.in_progress and self.message != None:
            print(payload.emoji.name)
            if self.message.id == payload.message_id:
                if self.waiting_on_player_one == True:
                    player = self.player_one
                    opponent = self.player_two
                else: 
                    player = self.player_two
                    opponent = self.player_one
                if payload.user_id == player.author.id and self.calculating != True:
                    #OFFENSIVE TURN
                    attack = [SWORD_EMOJI]
                    if player.class_name == 'luchador':
                        attack.append(GRAPPLE_EMOJI)
                    if player.first == 1:
                        if payload.emoji.name in attack:
                            self.calculating == True
                            player.roll = self.roll() + player.atk
                            player.roll = 1 if player.roll <= 0 else player.roll
                            await player.embed.clear_reactions()
                            self.swap_turns()
                            self.delete.append(await self.text.channel.send("{} rolled a {}!\nWaiting on {}'s defensive action.".format(player.name,player.roll,opponent.name)))
                            if payload.emoji.name == GRAPPLE_EMOJI:
                                await opponent.embed.add_reaction(EVADE_EMOJI)
                            else:
                                await opponent.embed.add_reaction(SHIELD_EMOJI)
                                await opponent.embed.add_reaction(EVADE_EMOJI)
                            self.message = opponent.embed
                            self.calculating == False
                            
                    else:
                        #DEFENSIVE TURN
                        defense = [SHIELD_EMOJI, EVADE_EMOJI]
                        if payload.emoji.name in defense:
                            self.calculating == True
                            player.roll = self.roll()
                            damage = 0
                            damage_text = ''
                            if payload.emoji.name == SHIELD_EMOJI:
                                player.roll += player.dfn
                                player.roll = 1 if player.roll <= 0 else player.roll
                                damage_text += "{} rolled a {}!".format(player.name, player.roll)
                                damage = opponent.roll - player.roll if player.roll < opponent.roll else 1
                                damage_text += '\n{} blocked and took {} damage.'.format(player.name, damage)
                            elif payload.emoji.name == EVADE_EMOJI:
                                player.roll += player.evd
                                player.roll = 1 if player.roll <= 0 else player.roll
                                damage_text += "{} rolled a {}!".format(player.name, player.roll)
                                damage = 0 if player.roll > opponent.roll else opponent.roll
                                damage_text += '\n{} successfully dodged the attack!'.format(player.name, damage) if damage == 0 else '\n{} tried to dodge but took {} damage.'.format(player.name, damage)
                                
                            #APPLYING DAMAGE
                            player.hp -= damage
                            if player.name == self.player_one.name:
                                self.player_one.hp = player.hp
                            else:
                                self.player_two.hp = player.hp
                            if player.class_name == 'paladin' and player.roll > opponent.roll and player.hp > 0 and payload.emoji.name == SHIELD_EMOJI:
                                    shield_damage = player.roll  - opponent.roll if (player.roll - opponent.roll) <= 2 else 2
                                    damage_text += '\nBlessed Shield dealt {} damage to {}.'.format(shield_damage, opponent.name)
                                    if opponent.name == self.player_one.name:
                                        self.player_one.hp -= shield_damage
                                    else:
                                        self.player_two.hp -= shield_damage
                            self.delete.append(await self.text.channel.send(damage_text))
                            await player.embed.clear_reactions()
                            self.calculating == False
                            
                            #END OF TURN
                            self.swap_first()
                            
                            round_done = self.check_health()
                            if round_done == 0:
                                await self.update_battle_meter()
                                time.sleep(3)
                                self.turns += 1
                                await self.text.channel.delete_messages(self.delete)
                                self.delete = []
                                player = self.player_one if self.player_one.first == 1 else self.player_two
                                self.delete.append(await self.text.channel.send("\n__**Turn {}**__\nWaiting {}'s on attack roll.".format(self.turns, player.name)))
                                self.message = player.embed
                                await self.set_attack_reactions(player)
                            else:
                                if self.player_one.hp <= 0:
                                    self.player_two.rounds += 1
                                    if self.player_two.rounds != 2:
                                        self.player_one.hp = self.player_one.max_hp
                                        self.player_one.died = True
                                        if self.player_one.class_name == 'berserker':
                                            self.player_one = self.swap_stats(self.player_one,self.player_one.atk+1,self.player_one.dfn-1,self.player_one.evd)
                                    
                                elif self.player_two.hp <= 0:
                                    self.player_one.rounds += 1
                                    if self.player_one.rounds != 2:
                                        self.player_two.hp = self.player_two.max_hp
                                        self.player_two.died = True
                                        if self.player_two.class_name == 'berserker':
                                            self.player_two = self.swap_stats(self.player_two,self.player_two.atk+1,self.player_two.dfn-1,self.player_two.evd)

                                game_done = self.check_rounds()
                                audio = self.bot.get_cog('Audio')
                                stop = audio.bot.get_command('stop')
                                play = audio.bot.get_command('play')
                                if game_done == 0:
                                    await self.update_battle_meter()
                                    time.sleep(3)
                                    await self.text.channel.delete_messages(self.delete)
                                    self.turns += 1
                                    self.delete = []
                                    player = self.player_one if self.player_one.first == 1 else self.player_two
                                    self.delete.append(await self.text.channel.send("\n__**Turn {}**__\nWaiting {}'s on attack roll.".format(self.turns, player.name)))
                                    self.message = player.embed
                                    await self.set_attack_reactions(player)
                                elif game_done == 1:
                                    await self.ctx.invoke(stop)
                                    theme = await self.get_theme(2,self.player_one.author)
                                    await self.ctx.invoke(play, query=theme)
                                    await self.update_battle_meter()
                                    await self.text.channel.send("{} won!".format(self.player_one.name))
                                    self.reset()
                                elif game_done == 2:
                                    await self.ctx.invoke(stop)
                                    theme = await self.get_theme(2,self.player_two.author)
                                    await self.ctx.invoke(play, query=theme)
                                    await self.update_battle_meter()
                                    await self.text.channel.send("{} won!".format(self.player_two.name))
                                    self.reset()
def setup(bot):
    bot.add_cog(SBIST(bot))
