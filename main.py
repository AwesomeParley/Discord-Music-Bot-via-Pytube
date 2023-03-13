#import discord.py and some extras under discord.py
import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
#import pytube to download video audio and the search function
from pytube import YouTube
from pytube import Search
#import ability to timeout (person didn't respond in a timely mannor)
import asyncio
#import for shuffle
import random

#I am actually not sure what these do...
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
queue = []
#when the bot gets an event
@bot.event
#get message
async def on_message(message):
#bot help command
    if message.content == 'bot help':
        await message.channel.send("Commands:\nbot play - This command can play any song on YouTube. You can also add the URL or search term to the end of the command for easier access.\nbot join - Makes the bot join the VC you are in.\nbot leave - Makes the bot leave the VC you are in.\nbot stop - Stops any music playing from the bot.")

#bot join command
    elif message.content == 'bot join':
        #if the user isn't in any vc
        if message.author.voice is None:
            await message.channel.send("You are not in a voice channel.")
            return

        voice_channel = message.author.voice.channel
        vc = message.guild.voice_client

        #if the user is in vc
        if vc is not None:
            #if bot is already connected
            if vc.channel == voice_channel:
                await message.channel.send("I am already connected to your voice channel.")
            else:
                #move to user's channel
                try:
                    await message.add_reaction('✅')
                except:
                    pass
                await vc.move_to(voice_channel)
        else:
            #connect
            try:
                await message.add_reaction('✅')
            except:
                pass
            vc = await voice_channel.connect()
            #checks if there is music playing or not and if no music is played after 2 minutes, the bot leaves.
        bot.loop.create_task(check_for_idle(vc, 120))

#bot leave command
    elif message.content == 'bot leave':
        vc = message.guild.voice_client

        #If not in voice channel
        if vc is None:
            await message.channel.send("I am not currently in a voice channel.")
            return

        # Stop playing the audio file
        vc.stop()

        #leaves vc
        try:
            await message.add_reaction('👋')
        except:
            pass
        await vc.disconnect()
        return

#bot play command
    elif message.content.startswith('bot play') or message.content.startswith('bot p'):
        if message.author.voice is None:
            await message.channel.send("You are not in a voice channel.")
            return
        #makes a list of words Ex: bot, play, <URL>
        words = message.content.split()

        vc = message.guild.voice_client
        global queue
        
        #if the amount of words is bigger than 2 and word 0 is bot and word 1 is play
        if len(words) > 2:
            try:
                await message.add_reaction('⏳')
            except:
                pass
            url = await urlOrSearch(words, 2, message)
        else:
            #store the URL as None because there was no 3rd word.
            url = None

        #if the URL is None
        if url is None:
            vc = message.guild.voice_client
            #ask for the URL and store it. 
            url = await askURL(message)
            if url is None:
                return

        if not(url.startswith('https://www.youtube.com/') or url.startswith('https://youtu.be/') or url.startswith('youtu.be/') or url.startswith('youtube.com/') or url.startswith('https://youtube.com/')):
            await message.channel.send("Please provide a valid YouTube URL.")
            print("DIS URL NO WORK: " + url)
            return
        
        if  (not(vc is None)) and vc.is_playing():
            queue.append(url)
            url = str(queue[len(queue)-1])
            try:
                await message.add_reaction('➕')
            except:
                pass
            i=0
            while i <= 10:
                try:
                    yt = YouTube(url)
                    await message.channel.send(f"Added {yt.title} to the queue")
                    try:
                        await message.remove_reaction('⏳', bot.user)
                    except:
                        pass
                    try:
                        await message.remove_reaction('🔎', bot.user)
                    except:
                        pass
                    return
                except:
                    i+=1
                    yt = None
            if yt is None:
                await message.channel.send(f"Added to the queue. (Couldn't get the title at this moment)")
                return
        voice_channel = message.author.voice.channel
        vc = message.guild.voice_client

        #connect to vc if already not in it
        if vc is None:
            vc = await voice_channel.connect()

        #checks if there is music playing or not and if no music is played after 2 minutes, the bot leaves.
        bot.loop.create_task(check_for_idle(vc, 120))

        #If already playing audio, tell the user.
        
        await playAudio(message, vc, url)

#bot stop command
    elif message.content == 'bot stop':
        vc = message.guild.voice_client
        if vc is None or not vc.is_playing():
            await message.channel.send("Not Playing anything.")
            return
        else:
            queue = []
            vc.stop()
            try:
                await message.add_reaction('🛑')
            except:
                pass
            return

#bot skip command
    elif message.content == 'bot skip':
        vc = message.guild.voice_client
        if vc is None or not vc.is_playing():
            await message.channel.send("Not Playing anything.")
            return
        else:
            await skip(message, vc)
            try:
                await message.add_reaction('⏭️')
            except:
                pass
            return

#askURL def
async def askURL(message):
    await message.channel.send("What do you want me to play?")
    
    def check(m):
        return m.author == message.author and m.channel == message.channel

    try:
        response = await bot.wait_for('message', check=check, timeout=30.0)
    except asyncio.TimeoutError:
        await message.channel.send("You took too long to respond.")
        return None

    url = response.content
    words = url.split()
    url = await urlOrSearch(words, 0, message)
    return url

#playAudio def
async def playAudio(message, vc, url):
    try:
        # Download the audio using pytube
        try:
            await message.add_reaction('📥')
        except:
            pass
        yt = YouTube(url)
        audio_stream = yt.streams.filter(only_audio=True).first()
        audio_path = 'audio.mp3'
        audio_stream.download(output_path='./', filename=audio_path)

        # Play the audio in the voice channel
        source = FFmpegPCMAudio(audio_path)
        try:
            await message.add_reaction('🎶')
        except:
            pass
        sentM = await message.channel.send(f"Now playing: {yt.title}")
        try:
            await message.remove_reaction('⏳', bot.user)
        except:
            pass
        try:
            await message.remove_reaction('🔎', bot.user)
        except:
            pass
        try:
            await message.remove_reaction('📥', bot.user)
        except:
            pass
        vc.play(source, after=lambda e: print(f'Player error: {e}') if e else bot.loop.create_task(afterPlay(sentM, message, vc)))
        

    except Exception as e:
        print(f"Error: {e}")
        await message.channel.send(f"Sorry, I could not play that due to an error.. Please Try Again.\n{e}")

#urlOrSearch def
async def urlOrSearch(words, n, message):
    if '/' in str(words[n]) and '.' in str(words[n]):
        url = str(words[n]) 
        
    else:
        searchTerm = ' '.join(words[n:],)
        #search for video
        try:
            await message.add_reaction('🔎')
        except:
            pass
        search_results = Search(searchTerm)
        url = search_results.results[0].watch_url
        i=1
        while not await checkIfUnder30min(url, message):
            i = i+1
            search_results = Search(searchTerm)
            url = search_results.results[i].watch_url
    return url

#checkIfUnder30min def
async def checkIfUnder30min(url, message):
    # create a YouTube object from the URL
    yt = YouTube(url)
    # get the duration of the video in seconds had to put it in this because it keeps wanting to break.
    i = 0
    while i <= 10: 
        try:
            duration = yt.length
            break  # break out of the loop if the duration is successfully obtained
        except:
            i += 1  # increment the value of i to prevent an infinite loop
            duration = None
        if i == 5:
            await message.channel.send("Sorry, it's taking extra long to get video length...")
    if duration is None:
        await message.channel.send("Sorry, I could not play it due to video length data being Null... Please Try Again.")
        return


    # check if the duration is under 15 minutes (900 seconds)
    if duration < 900:
        return True
    else:
        return False

#afterPlay def
async def afterPlay(sentM, message, vc):
    # Add a thumbs up reaction to the bot's message
    try:
        await sentM.add_reaction('🏁')
    except:
        pass
    global queue
    if len(queue) > 0 and not vc.is_playing(): 
        await playAudio(message, vc, (await nextQ()))
        return

#check_for_idle def
async def check_for_idle(voice_client, timeout):
    #Check if the bot has been idle for the specified number of seconds,
    #if it has, disconnect from the voice channel.
    while voice_client.is_playing():
        await asyncio.sleep(1)

    idle_time = 0
    while idle_time < timeout:
        await asyncio.sleep(1)
        if voice_client.is_playing():
            idle_time = 0
        else:
            idle_time += 1

    if idle_time >= timeout:
        await voice_client.disconnect()

#nextQ def
async def nextQ():
    global queue
    q = str(queue[0])
    queue.pop(0)
    return q

#skip def
async def skip(message, vc):
    global queue
    if not (queue[0] is None):
        vc.stop()
        await playAudio(message, vc, (await nextQ()))
        return
    else:
        await message.channel.send("That's the end of the queue!")
        return


@bot.event
async def on_voice_state_update(member, before, after):
    if member == bot.user and after.channel is None:
        await before.channel.guild.change_voice_state(channel=None)
    if member.id == bot.user.id and before.deaf and not after.deaf:
        # If the bot was undeafened by someone, re-deafen it
        await member.edit(deafen=True)



#Bot Username + Password
bot.run('NzU5NDc3NjU3NDM1MzczNTk5.GjLhwc.yMaZBdXmPGTvKyNxCtqJ-kIJ9K1WKyxhwZuR7Q')