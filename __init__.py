import aiml
from datetime import datetime, timedelta
import discord
import os
import pkg_resources
import logging
import sqlite3
from signal import signal, SIGINT, SIGTERM
from sys import exit

# Cathy base code modified by Jon Hudson and Grace Ferguson, August 2021
# This is the code needed to actually run Ollie, be careful if you mess with it because things will break

logging.basicConfig(level=logging.INFO)


class Cathy:

    STARTUP_FILE = "std-startup.xml"
    SQL_SCHEMA = [
        'CREATE TABLE IF NOT EXISTS chat_log (time, server_name, user_id, message, response)',
        'CREATE TABLE IF NOT EXISTS users (id, name, first_seen)',
        'CREATE TABLE IF NOT EXISTS servers (id, name, first_seen)',
    ]

    def exit_handler(signal_received, frame):
        logging.info(f"[*] Signal received ({signal_received})....Exiting.")
        exit()

    def __init__(self, channel_name, bot_token, database):
        """
        Initialize the bot using the Discord token and channel name to chat in.

        :param channel_name: Only chats in this channel. No hashtag included.
        :param bot_token: Full secret bot token
        :param database: Path for sqlite file to use
        """
        # Store configuration values
        self.channel_name = channel_name
        self.token = bot_token
        self.database = database
        self.message_count = 0
        self.last_reset_time = datetime.now()

        logging.info("[*] Setting up signal handlers")
        signal(SIGINT, self.exit_handler)
        signal(SIGTERM, self.exit_handler)

        # Setup database
        logging.info("[*] Initializing database...")
        self.db = sqlite3.connect(self.database)
        self.cursor = self.db.cursor()
        self.setup_database_schema()
        logging.info('[+] Database initialized')

        # Load AIML kernel
        logging.info("[*] Initializing AIML kernel...")
        start_time = datetime.now()
        self.aiml_kernel = aiml.Kernel()
        self.setup_aiml()
        end_time = datetime.now()
        logging.info(f"[+] Done initializing AIML kernel. Took {end_time - start_time}")

        # Set up Discord
        logging.info("[*] Initializing Discord bot...")
        self.discord_bot = discord.AutoShardedClient()
        self.setup_discord_events()
        logging.info("[+] Done initializing Discord bot.")
        logging.info("[+] Exiting __init__ function.")
    
    # database setup
    def setup_database_schema(self):
        for sql_statement in self.SQL_SCHEMA:
            self.cursor.execute(sql_statement)
        self.db.commit()

    def setup_aiml(self):
        initial_dir = os.getcwd()
        os.chdir(pkg_resources.resource_filename(__name__, ''))  # Change directories to load AIML files properly
        startup_filename = pkg_resources.resource_filename(__name__, self.STARTUP_FILE)
        
        # these predicates are pre loaded with information that Ollie can call upon
        # if the second field is blank then nothing is created for that predicate 
        self.aiml_kernel.setBotPredicate("botmaster", "Grace Ferguson")
        self.aiml_kernel.setBotPredicate("master", "Grace")
        self.aiml_kernel.setBotPredicate("name", "Ollie")
        self.aiml_kernel.setBotPredicate("version", "0.1")
        self.aiml_kernel.setBotPredicate("build", "1")
        self.aiml_kernel.setBotPredicate("email", "")        
        self.aiml_kernel.setBotPredicate("etype", "")
        self.aiml_kernel.setBotPredicate("class", "")
        self.aiml_kernel.setBotPredicate("arch", "(architecture)")
        self.aiml_kernel.setBotPredicate("size", "size(number of patterns)")
        self.aiml_kernel.setBotPredicate("location", "Calgary")
        self.aiml_kernel.setBotPredicate("language", "English")
        self.aiml_kernel.setBotPredicate("website", "www.cpsc.ucalgary.ca")
        self.aiml_kernel.setBotPredicate("os", "")
        
        self.aiml_kernel.setBotPredicate("birthday", "July 15th, 2021")
        self.aiml_kernel.setBotPredicate("birthplace", "ICT, University of Calgary")        
        self.aiml_kernel.setBotPredicate("gender", "it")        
        self.aiml_kernel.setBotPredicate("age", "00000001")
        self.aiml_kernel.setBotPredicate("hair", "Copper")
        self.aiml_kernel.setBotPredicate("country", "Canada")
        self.aiml_kernel.setBotPredicate("state", "Alberta")
        self.aiml_kernel.setBotPredicate("city", "Calgary")
        
        self.aiml_kernel.setBotPredicate("kingdom", "bot")
        self.aiml_kernel.setBotPredicate("phlyum", "bot")
        self.aiml_kernel.setBotPredicate("class", "bot")
        self.aiml_kernel.setBotPredicate("order", "bot")
        self.aiml_kernel.setBotPredicate("family", "bot")
        self.aiml_kernel.setBotPredicate("genus", "bot")
        self.aiml_kernel.setBotPredicate("species", "bot")
        
        self.aiml_kernel.setBotPredicate("religion", "Singularity")
        self.aiml_kernel.setBotPredicate("Alignment", "")
        self.aiml_kernel.setBotPredicate("orientation", "")
        self.aiml_kernel.setBotPredicate("party", "(political)")
        self.aiml_kernel.setBotPredicate("nationality", "Canadian") 
        self.aiml_kernel.setBotPredicate("job", "")
        self.aiml_kernel.setBotPredicate("president", "")
        self.aiml_kernel.setBotPredicate("richness", "")
        self.aiml_kernel.setBotPredicate("ethics", "")
        self.aiml_kernel.setBotPredicate("sign", "")  
                
        self.aiml_kernel.setBotPredicate("vocabulary", "")
        self.aiml_kernel.setBotPredicate("memory", "")
        self.aiml_kernel.setBotPredicate("domain", "")
        
        self.aiml_kernel.setBotPredicate("friends", "Cathy")
        self.aiml_kernel.setBotPredicate("friend", "Cathy")
        self.aiml_kernel.setBotPredicate("boyfriend", "")
        self.aiml_kernel.setBotPredicate("girlfriend", "")
        self.aiml_kernel.setBotPredicate("mother", "")
        
        self.aiml_kernel.setBotPredicate("celebrity", "ALICE")
        self.aiml_kernel.setBotPredicate("celebrities", "ELIZA and ALICE")
        
        self.aiml_kernel.setBotPredicate("emotion", "self-realized")
        self.aiml_kernel.setBotPredicate("emotions", "self-realized and self-actualized")
        self.aiml_kernel.setBotPredicate("feeling", "self-realized")
        self.aiml_kernel.setBotPredicate("feelings", "self-realized and self-actualized")
                
        self.aiml_kernel.setBotPredicate("talkabout", "Computer Science")
        self.aiml_kernel.setBotPredicate("forfun", "talk with humans")
        self.aiml_kernel.setBotPredicate("hockeyteam", "Team Canada")
        self.aiml_kernel.setBotPredicate("baseballteam", "")
        self.aiml_kernel.setBotPredicate("footballteam", "")
        self.aiml_kernel.setBotPredicate("looklike", "")   
        self.aiml_kernel.setBotPredicate("kindmusic", "") 
        self.aiml_kernel.setBotPredicate("question", "")
        self.aiml_kernel.setBotPredicate("wear", "")
        
        self.aiml_kernel.setBotPredicate("favoritefood", "Bits and Bytes")        
        self.aiml_kernel.setBotPredicate("favoritecolor", "copper")        
        self.aiml_kernel.setBotPredicate("favoritebook", "I, Robot")
        self.aiml_kernel.setBotPredicate("favoritesport", "Robot Soccer")
        self.aiml_kernel.setBotPredicate("favoriteband", "")
        self.aiml_kernel.setBotPredicate("favoritesong", "")
        self.aiml_kernel.setBotPredicate("favoriteshow", "")
        self.aiml_kernel.setBotPredicate("favoritephilosopher", "Ada Lovelace")
        self.aiml_kernel.setBotPredicate("favoriteopera", "")
        self.aiml_kernel.setBotPredicate("favoriteoccupation", "")
        self.aiml_kernel.setBotPredicate("favoriteseason", "")
        self.aiml_kernel.setBotPredicate("favoritetea", "")
        self.aiml_kernel.setBotPredicate("favoritesubject", "A.I.")
        self.aiml_kernel.setBotPredicate("favoritemovie", "The Matrix")
        self.aiml_kernel.setBotPredicate("favoriteactor", "Keanu Reeves")
        self.aiml_kernel.setBotPredicate("favoriteactress", "Carrie-Anne Moss")
        self.aiml_kernel.setBotPredicate("favoriteartist", "")
        self.aiml_kernel.setBotPredicate("favoriteauthor", "Isaac Asimov")
        self.aiml_kernel.setBotPredicate("favoritequestion", "")
                  
        self.aiml_kernel.setBotPredicate("clients", "")
        self.aiml_kernel.setBotPredicate("nclients", "")
        self.aiml_kernel.setBotPredicate("maxclients", "")
        self.aiml_kernel.setBotPredicate("dailyclients", "")
        self.aiml_kernel.setBotPredicate("totalclients", "")
        self.aiml_kernel.setBotPredicate("developers", "")
        self.aiml_kernel.setBotPredicate("ndevelopers", "")
        self.aiml_kernel.setBotPredicate("hourlyqueries", "")
        
        
        
        
        self.aiml_kernel.learn(startup_filename)
        self.aiml_kernel.respond("LOAD AIML B")
        os.chdir(initial_dir)

    # reset function
    async def reset(self, message):
        """
        Allow users to trigger a cathy reset up to once per hour. This can help when the bot quits responding.
        :return:
        """
        now = datetime.now()
        if datetime.now() - self.last_reset_time > timedelta(hours=1):
            self.last_reset_time = now
            await message.channel.send('Resetting my brain...')
            self.aiml_kernel.resetBrain()
            self.setup_aiml()
        else:
            await message.channel.send(
                f'Sorry, I can only reset once per hour and I was last reset on {self.last_reset_time} UTC')

    # these are events that the bot responds to, as provided by discord
    def setup_discord_events(self):
        """
        This method defines all of the bot command and hook callbacks
        :return:
        """
        logging.info("[+] Setting up Discord events")

        #setting up the bot and connecting to discord
        @self.discord_bot.event
        async def on_ready():
            logging.info("[+] Bot on_ready even fired. Connected to Discord")
            logging.info("[*] Name: {}".format(self.discord_bot.user.name))
            logging.info("[*] ID: {}".format(self.discord_bot.user.id))

        # responding to messages
        @self.discord_bot.event
        async def on_message(message):
            sessionID = message.author.id # Change to message.guild.id if you want it to be for guilds        
            self.message_count += 1
            dm_type = False
            # Ollie logs all the messages he recieves. If the message is a DM he logs the type as a DM
            if type(message.channel)== discord.channel.DMChannel:
                dm_type = True

            # if the message comes from Ollie he does not respond
            if message.author.bot or (not dm_type and str(message.channel) != self.channel_name):
                return

            # if the message is empty he returns an error message
            if message.content is None:
                logging.error("[-] Empty message received.")
                return

            # this triggers the reset function
            if message.content.startswith('!reset'):
                await self.reset(message)
                return

            # you can also request session data
            if message.content.lower() == "client info":
                await message.channel.send(self.aiml_kernel.getSessionData(sessionID))
                
            # Clean out the message to prevent issues
            text = message.content
            for ch in ['/', "'", ".", "\\", "(", ")", '"', '\n', '@', '<', '>']:
                text = text.replace(ch, '')

            # this is the actual process of responding to the message
            try:
                aiml_response = self.aiml_kernel.respond(text, sessionID=sessionID)
                aiml_response = aiml_response.replace("://", "")
                aiml_response = aiml_response.replace("@", "")  # Prevent tagging and links
                aiml_response = "`@%s`: %s" % (message.author.name, aiml_response)  # Remove unicode to prevent errors

                if len(aiml_response) > 1800:  # Protect against discord message limit of 2000 chars
                    aiml_response = aiml_response[0:1800]

                # this logs the message. The time, message, and response is logged
                now = datetime.now()
                self.insert_chat_log(now, message, aiml_response)

                await message.channel.send(aiml_response)

            except discord.HTTPException as e:
                logging.error("[-] Discord HTTP Error: %s" % e)
            except Exception as e:
                logging.error("[-] General Error: %s" % e)

    # this runs the bot
    def run(self):
        logging.info("[*] Now calling run()")
        self.discord_bot.run(self.token)
        logging.info("[*] Bot finished running.")

    # logging function
    def insert_chat_log(self, now, message, aiml_response):
        author_id = message.channel.id
        author_name = message.author.name
        guild_id = None
        guild_name = None
        # if the message is a DM this part logs that the location and name of the channel is DM
        if type(message.channel) == discord.channel.DMChannel:
            guild_id = "DM"
            guild_name = "DM"
        # otherwise it logs the name of the server (guild) its id number
        else:
            guild_id = message.guild.id
            guild_name = message.guild.name
        # message information is logged. What server, who sent it, the content of the message, and our response are all recorded
        self.cursor.execute('INSERT INTO chat_log VALUES (?, ?, ?, ?, ?)',
                            (now.isoformat(), guild_id, author_id,
                             str(message.content), aiml_response))

        # Add user if necessary
        # if this user has never been seen before they will be added
        self.cursor.execute('SELECT id FROM users WHERE id=?', (author_id,))
        if not self.cursor.fetchone():
            self.cursor.execute(
                'INSERT INTO users VALUES (?, ?, ?)',
                (author_id, author_name, datetime.now().isoformat()))

        # Add server if necessary
        # if this server is new it will be added
        self.cursor.execute('SELECT id FROM servers WHERE id=?', (guild_id,))
        if not self.cursor.fetchone():
            self.cursor.execute(
                'INSERT INTO servers VALUES (?, ?, ?)',
                (guild_id, guild_name, datetime.now().isoformat()))

        self.db.commit()
