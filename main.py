import threading
from time import sleep

import discum
import datetime

from discum.utils.slash import SlashCommander
from discum.utils.button import Buttoner

self_id = '000000000000000000'
mudae_application_id = '432610292342587392'


def log_to_file(message):
    with open('bot.txt', 'a', encoding='utf-8') as f:
        f.write('[' + str(datetime.datetime.now()) + '] ' + message + '\n')


class c_message:
    def __init__(self, message, command, time, message_id, embed='', components='', raw_components=''):
        self.message = message
        self.message_id = message_id
        self.command = command
        self.embed = embed
        self.time = time
        self.components = components
        self.raw_components = raw_components


class c_command:
    def __init__(self, command, func, target_channels, log=False, allowed_users=None):
        if allowed_users is None:
            allowed_users = []

        self.allowed_users = allowed_users
        self.command = command
        self.do_log = log
        self.target_channels = target_channels

        def wrapper(msg, channel_id, msg_id, msg_author, resp):
            author_id = resp.parsed.auto()['author']['id']
            if len(self.target_channels) > 0 and '*' not in self.target_channels:
                if channel_id not in self.target_channels:
                    # print('Channel ' + channel_id + ' is not allowed to use command ' + self.command)
                    return

            if len(self.allowed_users) > 0 and '*' not in self.allowed_users:
                if author_id not in self.allowed_users:
                    # print('User ' + msg_author + ' is not allowed to use command ' + self.command)
                    return

            if self.do_log:
                embed = ''
                if 'embeds' in resp.parsed.auto() and len(resp.parsed.auto()['embeds']) > 0:
                    embed = resp.parsed.auto()['embeds'][0]
                str_log = 'Invoked command: ' + self.command + ' by ' + msg_author + ' in channel ' + channel_id + \
                          ' with message id ' + msg_id + ' and message: ' + msg + ' and embed: ' + str(embed)
                # print('Invoked command: ' + self.command + ' by ' + msg_author + ' in channel ' + channel_id)
                log_to_file(str_log)

            func(msg, channel_id, msg_id, msg_author, resp)

        self.func = wrapper


class c_listener:
    def __init__(self, func, log, target_channels, target_user):
        self.do_log = log
        self.target_user = target_user
        self.target_channels = target_channels

        def wrapper(msg, channel_id, msg_id, msg_author, resp):
            if channel_id not in self.target_channels:
                return

            resp_parsed = resp.parsed.auto()
            if not 'interaction' in resp_parsed:
                return

            if not resp_parsed['interaction']['user'] or not resp_parsed['interaction']['type'] == 2:
                return

            if resp_parsed['interaction']['user']['id'] != self_id:
                return

            if self.target_user:
                author_id = resp_parsed['author']['id']
                if author_id != self.target_user:
                    return

            if self.do_log:
                embed = ''
                if 'embeds' in resp_parsed and len(resp_parsed['embeds']) > 0:
                    embed = resp_parsed['embeds'][0]
                str_log = 'Invoked listener by ' + msg_author + ' in channel ' + channel_id + \
                          ' with message id ' + msg_id + ' and message: ' + msg + ' and embed: ' + str(embed)
                # print('Invoked listener by ' + msg_author + ' in channel ' + channel_id)
                log_to_file(str_log)

            func(msg, channel_id, msg_id, msg_author, resp)

        self.func = wrapper


class c_discord:
    def __init__(self, live=True, instance_name='Default Instance'):
        self.client = discum.Client(token="your token",
                                    log=False)
        self.live = live
        self.instance_name = instance_name
        # Debug server
        self.target_channel = '000000000000000000'
        self.target_owner = '000000000000000000'
        self.target_mudae = '000000000000000000'
        self.target_guild = '000000000000000000'
        #
        if self.live:
            # Live server
            self.target_channel = '000000000000000000'
            self.target_owner = '000000000000000000'
            self.target_mudae = '000000000000000000'
            self.target_guild = '000000000000000000'
        #
        self.target_debug = '000000000000000000'
        #
        self.commands = {}
        self.listeners = []
        self.mudae_messages = []
        self.last_mudae_message = None
        #
        self.inst_mudae = c_mudae(self)

        def log_mudae(msg, channel_id, msg_id, msg_author, resp):
            embed = None
            if 'embeds' in resp.parsed.auto() and len(resp.parsed.auto()['embeds']) > 0:
                embed = resp.parsed.auto()['embeds'][0]

            if embed is None:
                embed = ''

            components = None
            if 'components' in resp.parsed.auto() and len(resp.parsed.auto()['components']) > 0:
                components = resp.parsed.auto()['components'][0]

            if components is None:
                components = ''

            if 'the roulette is limited to' in msg:
                return

            time = datetime.datetime.now()

            inst_message = c_message(msg, resp.parsed.auto()['interaction']['name'], time, resp.parsed.auto()['id'],
                                     embed, components, resp.parsed.auto()['components'])
            self.last_mudae_message = inst_message
            self.mudae_messages.append(inst_message)

        self.register_listener(log_mudae, True, [self.target_channel], self.target_mudae)

        @self.client.gateway.command
        def on_message(resp):
            if resp.event.message:
                channel_id = resp.parsed.auto()['channel_id']
                msg_author_id = resp.parsed.auto()['id']
                msg_author_user = resp.parsed.auto()['author']['username']
                msg_content = resp.parsed.auto()['content']
                for listener in self.listeners:
                    listener.func(msg_content, channel_id, msg_author_id, msg_author_user, resp)
                for command in self.commands:
                    if msg_content == command:
                        self.commands[command].func(msg_content, channel_id, msg_author_id, msg_author_user, resp)

    def register_command(self, command, func, target_channel, log=False, allowed_users=None):
        if command not in self.commands:
            self.commands[command] = c_command(command, func, target_channel, log, allowed_users)
        else:
            print('Command already registered!')

    def register_listener(self, func, log, target_channels, target_user):
        self.listeners.append(c_listener(func, log, target_channels, target_user))

    def send_claim(self, components, message_id):
        button = Buttoner(components)
        target_button = button.getButton(customID=components[0]['components'][0]['custom_id'])
        if target_button is not None and target_button != []:
            ret = self.client.click(mudae_application_id, channelID=self.target_channel, messageID=message_id,
                                    guildID=self.target_guild, data=target_button, messageFlags=0)
            if ret.status_code == 200 or ret.status_code == 204:
                return True
        else:
            return False

    def send_message_bot(self, msg):
        sleep(1)  # discum bug, needs delay to send messages correctly
        self.client.sendMessage(self.target_debug, '[ ' + str(self.instance_name) + '] ' + msg)

    def send_reply_bot(self, msg, channel_id, msg_id, embed=None):
        sleep(1)  # discum bug, needs delay to send messages correctly
        self.client.reply(channel_id, msg_id, '[:flag_cn: ' + str(self.instance_name) + '] ' + msg, embed=embed)

    def start(self):
        self.client.gateway.run(auto_reconnect=True)

    def run_slash_cmd(self, target_channel, guild_id, command):
        s = SlashCommander(self.client.getSlashCommands(mudae_application_id).json())
        cmd_dict = [command]
        data = s.get(cmd_dict)
        self.client.triggerSlashCommand(mudae_application_id, target_channel, guild_id, data)


class c_mudae_cmd_tu:
    def __init__(self, discord: c_discord):
        self.message = None
        self.inst_discord = discord
        #
        self.last_tu_time = datetime.datetime.now()
        self.rolls = 0
        self.can_claim = False
        self.next_claim_reset = datetime.datetime.now()
        self.next_roll_reset = datetime.datetime.now()
        self.next_roll_reset_time = ""
        self.next_claim_reset_time = ""
        self.has_daily = False
        self.kakera = 0
        self.can_claim_kakera = False
        self.can_dk = False
        self.can_vote = False

    def parse(self, message):
        self.message = message
        self.rolls = 0
        self.can_claim = False
        self.next_claim_reset = datetime.datetime.now()
        self.next_roll_reset = datetime.datetime.now()
        self.next_roll_reset_time = ""
        self.next_claim_reset_time = ""
        self.has_daily = False
        self.kakera = 0
        self.can_claim_kakera = False
        self.can_dk = False
        self.can_vote = False
        #
        lines = self.message.split('\n')
        for line in lines:
            if "you __can__ claim" in line or "you can't claim" in line:
                if "you __can__ claim" in line:
                    self.can_claim = True
                    self.next_claim_reset_time = line.split('in **')[1].split('**')[0]
                else:
                    self.can_claim = False
                    self.next_claim_reset_time = line.split('for another **')[1].split('**')[0]

                if 'h' in self.next_claim_reset_time:
                    hours = int(self.next_claim_reset_time.split('h')[0])
                    minutes = int(self.next_claim_reset_time.split('h')[1].split(' ')[1])
                    self.next_claim_reset = datetime.datetime.now() + datetime.timedelta(hours=hours, minutes=minutes)
                else:
                    minutes = int(self.next_claim_reset_time.split(' ')[0])
                    self.next_claim_reset = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
            elif "You have" in line:
                self.rolls = int(line.split('**')[1])
                self.next_roll_reset_time = line.split('in **')[1].split('**')[0]
                minutes = int(self.next_roll_reset_time.split(' ')[0])
                self.next_roll_reset = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
            elif "$daily is available!" in line:
                self.has_daily = True
            elif "You __can__ react to kakera" in line or "You can't react to kakera" in line:
                if "You __can__ react to kakera" in line:
                    self.can_claim_kakera = True
            elif "$dk is ready!" in line:
                self.can_dk = True
            elif "You may vote right now!" in line:
                self.can_vote = True
            elif "Stock:" in line:
                self.kakera = int(line.split('**')[1])

    def print_states(self):
        return "[" + self.inst_discord.instance_name + "] Claim reset: " + str(self.next_claim_reset_time) + " | " + \
            "Roll reset: " + str(self.next_roll_reset_time) + " | " + \
            "Rolls: " + str(self.rolls) + " | " + \
            "Kakera: " + str(self.kakera) + " | " + \
            "Can claim kakera: " + str(self.can_claim_kakera) + " | " + \
            "Can claim: " + str(self.can_claim) + " | " + \
            "Can dk: " + str(self.can_dk) + " | " + \
            "Can vote: " + str(self.can_vote) + " | " + \
            "Has daily: " + str(self.has_daily)

    def roll_reset_notification(self):
        self.inst_discord.send_message_bot("Roll reset at " + str(self.next_roll_reset))

    def claim_reset_notification(self):
        self.inst_discord.send_message_bot("Claim reset at " + str(self.next_claim_reset))


class c_mudae_cmd_wa:
    def __init__(self):
        self.message = None
        self.kakera_name = None
        self.is_unclaimable = False
        self.has_kakera_button = False
        self.kakera_value = 0
        self.waifu_name = ""
        self.waifu_image = ""
        self.time = datetime.datetime.now()

    def parse(self, message: c_message):
        self.is_unclaimable = False
        self.has_kakera_button = False
        self.kakera_value = 0
        self.waifu_name = ""
        self.waifu_image = ""
        self.time = datetime.datetime.now()
        self.message = message
        #
        embed = self.message.embed
        #
        component = self.message.components
        #
        self.waifu_name = embed['author']['name']
        self.waifu_image = embed['image']['url']
        #
        if embed['description'].split('\n')[1].split('<')[0].replace('**', '') != '':
            self.kakera_value = int(embed['description'].split('\n')[-1]
                                    .split('<')[0].replace('**', ''))
        #
        self.kakera_name = component['components'][0]['emoji']['name']
        if 'kakera' in self.kakera_name:
            self.is_unclaimable = True
            self.kakera_value = 0


class c_mudae_rolls:
    def __init__(self, inst_tu: c_mudae_cmd_tu):
        self.time = datetime.datetime.now()
        self.inst_tu = inst_tu
        self.timeout = datetime.datetime.now()
        self.rolls = []
        # ----------------
        # rolling configuration
        # ----------------
        self.last_hour_claim = True
        self.first_hour_double_value = True
        self.auto_claim_kakera = True
        self.auto_dk = True
        self.auto_daily = True
        self.auto_claim_waifu = True
        self.claim_threshold = 100  # kakera value

    def logic(self):
        if self.inst_tu.rolls > 0 and self.timeout < datetime.datetime.now() and (
                self.inst_tu.can_claim or self.inst_tu.can_claim_kakera):
            self.timeout = datetime.datetime.now() + datetime.timedelta(seconds=4)
            self.inst_tu.inst_discord.run_slash_cmd(self.inst_tu.inst_discord.target_channel,
                                                    self.inst_tu.inst_discord.target_guild,
                                                    'wa')
            self.inst_tu.inst_discord.send_message_bot('Rolls left: {}'.format(self.inst_tu.rolls - 1))
        elif self.inst_tu.rolls == 0 and len(self.rolls) > 0 and self.timeout < datetime.datetime.now():
            self.inst_tu.inst_discord.send_message_bot('No rolls left, picking waifu!')
            self.timeout = datetime.datetime.now() + datetime.timedelta(seconds=6)

            if self.auto_claim_waifu and self.inst_tu.can_claim:
                target_waifu = self.choose_waifu()
                if target_waifu is not None:
                    self.claim_waifu(target_waifu)
                    self.inst_tu.can_claim = False
                else:
                    self.inst_tu.inst_discord.send_message_bot('No waifu to claim!')
            else:
                self.inst_tu.inst_discord.send_message_bot('Waifu claim unavailable!')

            if self.auto_claim_kakera and self.inst_tu.can_claim_kakera:
                target_kakera = self.choose_kakera()
                if target_kakera is not None:
                    self.claim_waifu(target_kakera)
                    self.inst_tu.can_claim_kakera = False
                else:
                    self.inst_tu.inst_discord.send_message_bot('No kakera to claim!')
            else:
                self.inst_tu.inst_discord.send_message_bot('Kakera claim unavailable!')

            self.rolls.clear()

            if self.auto_dk and self.inst_tu.can_dk:
                self.inst_tu.inst_discord.send_message_bot('Claiming dk!')
                self.inst_tu.inst_discord.run_slash_cmd(self.inst_tu.inst_discord.target_channel,
                                                        self.inst_tu.inst_discord.target_guild,
                                                        'dk')
                self.inst_tu.can_dk = False

            if self.auto_daily and self.inst_tu.has_daily and self.inst_tu.can_claim:
                self.inst_tu.inst_discord.send_message_bot('Claiming daily!')
                self.inst_tu.inst_discord.run_slash_cmd(self.inst_tu.inst_discord.target_channel,
                                                        self.inst_tu.inst_discord.target_guild,
                                                        'daily')
                self.inst_tu.has_daily = False
                sleep(5)
                self.inst_tu.inst_discord.run_slash_cmd(self.inst_tu.inst_discord.target_channel,
                                                        self.inst_tu.inst_discord.target_guild,
                                                        'rolls')
                sleep(5)
                self.inst_tu.inst_discord.run_slash_cmd(self.inst_tu.inst_discord.target_channel,
                                                        self.inst_tu.inst_discord.target_guild,
                                                        'tu')

    def choose_waifu(self):
        min_kakera_value = self.claim_threshold
        current_time = datetime.datetime.now()
        if self.first_hour_double_value:
            min_kakera_value *= 2
        time_delta_to_next_claim_reset = self.inst_tu.next_claim_reset - current_time
        if self.last_hour_claim and time_delta_to_next_claim_reset <= datetime.timedelta(hours=1):
            self.inst_tu.inst_discord.send_message_bot('Last hour claim active, delta: {}'
                                                       .format(time_delta_to_next_claim_reset))
            min_kakera_value = 30

        self.rolls.sort(key=lambda x: x.kakera_value, reverse=True)
        claim_list = list(filter(lambda x: not x.is_unclaimable, self.rolls))
        claim_list = list(filter(lambda x: x.kakera_value >= min_kakera_value, claim_list))

        if len(claim_list) > 0:
            return claim_list[0]
        else:
            self.inst_tu.inst_discord.send_message_bot('No waifu to claim')
            return None

    def choose_kakera(self):
        claim_list = list(filter(lambda x: x.kakera_value == 0, self.rolls))

        if len(claim_list) > 0:
            return claim_list[0]
        else:
            self.inst_tu.inst_discord.send_message_bot('No kakera to claim')
            return None

    def claim_waifu(self, inst_wa: c_mudae_cmd_wa):
        if self.auto_claim_waifu:
            self.inst_tu.inst_discord.send_message_bot('Claiming {} for {} kakera'.format(inst_wa.waifu_name,
                                                                                          inst_wa.kakera_value))
            result = self.inst_tu.inst_discord.send_claim(inst_wa.message.raw_components, inst_wa.message.message_id)
            if result:
                self.inst_tu.can_claim = False
        else:
            self.inst_tu.inst_discord.send_message_bot('Recommended claim {} value {}'.format(inst_wa.waifu_name,
                                                                                              inst_wa.kakera_value))

    def add_roll(self, inst_wa: c_mudae_cmd_wa):
        print('[' + self.inst_tu.inst_discord.instance_name + '] New roll: {} {} {}'.format(inst_wa.waifu_name,
                                                                                            inst_wa.kakera_name,
                                                                                            inst_wa.kakera_value))
        self.inst_tu.rolls -= 1
        self.rolls.append(inst_wa)


class c_mudae:
    def worker(self):
        last_execution = datetime.datetime.now()
        while True:
            #
            if (datetime.datetime.now() - last_execution).total_seconds() < 1:
                continue
            last_execution = datetime.datetime.now()

            if not self.initial_tu:
                self.initial_tu = True
                self.inst_discord.run_slash_cmd(self.inst_discord.target_channel, self.inst_discord.target_guild, 'tu')
                sleep(5)
                continue
            else:
                #
                time_now = datetime.datetime.now() - datetime.timedelta(seconds=60)
                if self.tu_module.next_roll_reset < time_now:
                    self.tu_module.next_roll_reset = datetime.datetime.now() + datetime.timedelta(hours=1, minutes=1)
                    self.inst_discord.send_message_bot('Roll timer expired')
                    self.inst_discord.run_slash_cmd(self.inst_discord.target_channel,
                                                    self.inst_discord.target_guild,
                                                    'tu')
                    sleep(5)
                    continue

                #
                self.roll_module.logic()

                if len(self.inst_discord.mudae_messages) > 0:
                    #
                    self.inst_discord.mudae_messages.sort(key=lambda x: x.time, reverse=True)
                    #
                    for msg in self.inst_discord.mudae_messages:
                        if msg.command == 'tu' and msg.time > self.last_tu_time:
                            self.last_tu_time = msg.time
                            self.tu_module.parse(msg.message)
                            self.tu_module.roll_reset_notification()
                            self.tu_module.claim_reset_notification()
                            self.inst_discord.send_message_bot(self.tu_module.print_states())
                            print(self.tu_module.print_states())
                            self.inst_discord.mudae_messages.remove(msg)
                            continue
                        if msg.command == 'wa':
                            self.inst_discord.mudae_messages.remove(msg)
                            inst_wa = c_mudae_cmd_wa()
                            inst_wa.parse(msg)
                            self.roll_module.add_roll(inst_wa)

    def __init__(self, instance_discord: c_discord):
        self.inst_discord = instance_discord
        self.initial_tu = False
        #
        self.tu_module = c_mudae_cmd_tu(instance_discord)
        self.last_tu_time = datetime.datetime.now()
        #
        self.roll_module = c_mudae_rolls(self.tu_module)
        #
        self.worker_thread = threading.Thread(target=self.worker)
        self.worker_thread.start()


if __name__ == '__main__':
    inst_discord_live = c_discord(True, 'Name of instance')
    inst_thread_live = threading.Thread(target=inst_discord_live.start)
    inst_thread_live.start()
