import discord
import yaml
import re
import cv2
import pytesseract
from urllib.request import Request, urlopen
import numpy as np
import time
import asyncio
from waiting import wait
import random
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import threading

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

with open("config.yaml", 'r') as stream:
	try:
		config = yaml.safe_load(stream)
	except yaml.YAMLError as exc:
		print(exc)


def create_opencv_image_from_url(url, cv2_img_flag=0):
	request = urlopen(Request(url, headers={
		'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
		'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
		'Accept-Encoding': 'none',
		'Accept-Language': 'en-US,en;q=0.8',
		'Connection': 'keep-alive'
	}));
	img_array = np.asarray(bytearray(request.read()), dtype=np.uint8)
	return cv2.imdecode(img_array, cv2_img_flag)


emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣']
min_wishlist = 25

drop_time = time.time()
grab_time = time.time()
def has_grab(): return True if grab_time < time.time() else False
	
daily_time = time.time()
krm_time = time.time()

started = False
class MyClient(discord.Client):

	async def on_ready(self):
		global started
		print('Logged on as', self.user)
		if not started:
			started = True
			await self.task_loop()


	async def on_message(self, message):
		global grab_time, drop_time, daily_time, krm_time
		#if message.author == self.user: return

		if message.content.startswith("t1"):
			return await message.channel.send(content=f"<@!{config['account']['id']}> is dropping 3 cards!", file=discord.File(r'card.jpg'))
		elif message.content.startswith("t2"):
			return await message.channel.send(content="I'm dropping 3 cards since this server is currently active!", file=discord.File(r'card2.jpg'))
		elif message.content.startswith("trm"):
			dropt = str(datetime.timedelta(seconds=int(drop_time-time.time()))) if (drop_time-time.time()) > 0 else "is ready"
			grabt = str(datetime.timedelta(seconds=int(grab_time-time.time()))) if (grab_time-time.time()) > 0 else "is ready"
			dailyt = str(datetime.timedelta(seconds=int(daily_time-time.time()))) if (daily_time-time.time()) > 0 else "is ready"
			return await message.channel.send(f"```Drop: {dropt}\nGrab: {grabt}\nDaily: {dailyt}```")

		if message.channel.id not in config["karuta"]["watch_channels"]: return

		if not has_grab(): return

		user_drop = re.search('([0-9]+)> is dropping ([0-9]) cards!', message.content)
		server_drop = re.search("I'm dropping ([0-9]) cards since this server is currently active!", message.content)
		if ((user_drop or server_drop) and len(message.attachments) > 0):

			if(user_drop):
				dropper_id = int(user_drop.group(1))
				card_count = int(user_drop.group(2))
			else:
				card_count = int(server_drop.group(1))

			print(f"Attempting to grab {'user' if user_drop else 'server'} drop")

			image = create_opencv_image_from_url(message.attachments[0].url, cv2.IMREAD_GRAYSCALE)
			thresh = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
			
			#cv2.imshow('thresh', thresh)
			#cv2.imshow('thinned', thinned)
			#cv2.waitKey()

			names = []
			series = []
			for y in [55, 307]:
				for x in range(46, ((card_count-1) * 277 + 47), 277):
					x,y,w,h = x, y, 180, 53
					ROI = thresh[y:y+h,x:x+w]
					
					stri = pytesseract.image_to_string(ROI, lang='eng',config='--psm 6')
					stri = stri.replace("\n", " ")
					stri = re.sub(r'[^a-zA-Z ]+', ' ', stri)
					#stri = re.sub(r'(\B\s+|\s+\B)', '', stri) # trailing whitespace
					
					'''cv2.imshow('ROI', ROI)
					cv2.waitKey()
					print(stri)'''
					
					if y < 300:
						names.append(stri)
					else:
						series.append(stri)

			best_wishlist = [random.randint(1, card_count), -1] # idx, wl

			card_idxs = list(range(card_count))
			#random.shuffle(card_idxs)
			a = 0
			for i in card_idxs:
				await client.get_channel(config["karuta"]["klu_channel"]).send(f"k!lu {series[i]} {names[i]}") # klu check

				try:
					msg = await client.wait_for('message', timeout=5.0, check=lambda m: m.channel.id == config["karuta"]["klu_channel"] and len(m.embeds) > 0)
				except asyncio.TimeoutError:
					msg = None
					pass
				
				if msg == None:
					if(card_count-1 != a): await asyncio.sleep(21)
					a += 1
					continue
				
				if msg.embeds[0].title == "Character Lookup":
					wishlist_raw = re.search('Wishlisted · \*\*(.*)\*\*', msg.embeds[0].description)
					if wishlist_raw == None: wishlist = -1
					else: wishlist = int((wishlist_raw).group(1).replace(',', ''))
				elif msg.embeds[0].title == "Character Results":
					wishlist = int(re.search('1\..*\♡([0-9]+)', msg.embeds[0].fields[0].value).group(1).replace(',', ''))
				else: wishlist = -1
				
				await client.get_channel(config["karuta"]["klu_channel"]).send(f"{series[i]} - {names[i]} has **{wishlist}** wishlist")
				
				if(wishlist > best_wishlist[1]):
					best_wishlist = [i, wishlist]
					#if(wishlist > 200):
					#	print("Above 200 wishlist, grabbing")
					#	break

				if(card_count-1 != a): await asyncio.sleep(21)
				a += 1
				
			if best_wishlist[1] < min_wishlist and (server_drop or dropper_id != config['account']['id']): 
				print("Wishlist too low, ignoring...")
				return
			
			target_r = emojis[best_wishlist[0]]
			if any(r.emoji == target_r for r in message.reactions):
				await message.add_reaction(target_r)
			else:
				try:
					await client.wait_for('reaction_add', timeout = 900, check=lambda r, u: r.message == message and r.emoji == target_r)
				except asyncio.TimeoutError:
					return
				await message.add_reaction(target_r)

			print("Added target reaction")

			try:
				msg = await client.wait_for('message', timeout=15, check=lambda m: m.channel.id == config["karuta"]["drop_channel"] and f"<@{config['account']['id']}> took the" in m.content)
			except asyncio.TimeoutError:
				print(f"Missed grab of card '{series[best_wishlist[0]]} - {names[best_wishlist[0]]}' ({best_wishlist[1]} wl)")
				grab_time = time.time() + 60
				return

			print(f"Grabbed card '{series[best_wishlist[0]]} - {names[best_wishlist[0]]}' ({best_wishlist[1]} wl)")
			
			grab_time = time.time() + 600

	async def task_loop(self):
		global grab_time, drop_time, daily_time, krm_time
		while(True):
			if drop_time <= time.time():
				if not has_grab(): await asyncio.sleep(grab_time + 15)
				await client.get_channel(config["karuta"]["drop_channel"]).send("k!d")
				drop_time = time.time() + 1815
			if daily_time <= time.time():
				await client.get_channel(config["karuta"]["drop_channel"]).send("k!daily")
				daily_time = time.time() + 86415
			if krm_time <= time.time():
				await client.get_channel(config["karuta"]["drop_channel"]).send("k!rm")
				krm_time = time.time() + 120
				await client.get_channel(config["karuta"]["drop_channel"]).send("yup yessuh")
			await asyncio.sleep(30)



client = MyClient()
client.run(config['account']['token'])