import os
import json
import requests
from peewee import *
import vk_api
import vk_api.longpoll
from vk_api import VkUpload
from vk_api.longpoll import VkLongPoll , VkEventType , Event
from yandex_translate import YandexTranslate
from urllib.request import urlopen
from PIL import Image
import urllib.request
import cloudconvert

# ключ YandexTranslate
translate = YandexTranslate('API KEY')

# ключ vk api
token_vk = 'API KEY'

# ключ для конвертации через api cloudconvert
api = cloudconvert.Api('API KEY')  

# мой переводчик
my_translate = {   
	'столица':'capital',
	'население':'population', 
	'домен':'topLevelDomain',  
	'континент':'region',
	'подконтинент':'subregion',
	'регион':'subregion',
	'площадь':'area',
	'территория':'area',
	'время':'timezones',
	'валюта':'currencies',
	'координаты':'latlng',
	'местоположение':'latlng',
	'житель':'demonym',
	'народ':'demonym',
	'человек':'demonym',
	'джини':'gini',
	'границы':'borders',
	'оригинал':'nativeName',
	'страна':'nativeName',
	'название':'nativeName',
	'код':'numericCode',
	'язык':'languages',
	'флаг':'flag'
	}

db = SqliteDatabase('database.db')   # база данных состояний пользователей
class User(Model): 
	vk_id = IntegerField() 
	state = IntegerField(default=0) 
	class Meta: 
		database = db 
table = db.create_tables([User])

# инициализация бота
vk_session = vk_api.VkApi(token=token_vk)
vk = vk_session.get_api()

upload = VkUpload(vk_session)      # для загрузки изображений
longpoll = VkLongPoll(vk_session)  # инициализация лонгполлинга

def perevod(text,direction):  # text - что перевести , direction - направление перевода
	try:
		perevod = ('Translate:', translate.translate(text, direction))  # or just 'en'
		perevod = (perevod[1])
		perevod = perevod["text"]
		country = ''.join(perevod)
	except:
		print('Ошибка при переводе !')
		country = "error"
	return country

def state0(message: Event):
	text = message.text
	hello = text.lower()
	
	if hello == 'привет':
		text = 'Привет! Я справочник по странам . Напиши мне, например "Столица Франции" или "Население США" . Чтобы узнать полный список команд напиши "что ты умеешь" .'
	elif hello == 'что ты умеешь' or hello == 'что ты умеешь?':
		text = 'Как пользоваться ботом : \n"команда страна"\n\nНапример : Флаг США , Народ Аргентины и тд. \n\nПолный список команд : \n\n' 
		for key in my_translate.keys():
			text+= key + ' , '
		text = text[0:-2]
		text+=' .'
	else:
		try:
			a = text.split()
			find_ru = a[0]
			find_en = my_translate[find_ru.lower()]

			print('------------------------------------------------')
			print('Что найти :',find_en)

			# извините, здесь костыль из-за неправильного перевода YandexTranslate
			if a[1] == "Того":  
				country="Togo"
			else:
				try:
					country = perevod(a[1]+' '+a[2], 'en')
				except IndexError:
					country = perevod(a[1], 'en')

			print('Страна :',country)

		    #https://restcountries.eu/rest/v2/name/russia/?fields=name;capital;currencies  # пример запроса по отдельным полям

			url = 'https://restcountries.eu/rest/v2/name/' + country + '/?fields=' + find_en + ';'
			response = requests.get(url)
			list = (response.json()[0])					   # получаем список
			print(list)

			if find_en == 'currencies':
				dict = list[find_en]
				otvet = dict[0]
				print('Валюта :', otvet)
				otvet = perevod(otvet['name'],'en-ru')		# переводим
				text = text + " - " + str(otvet)

			elif find_en == 'numericCode' or find_en == 'nativeName':

				otvet = list[find_en]
				text = text + " - " + str(otvet)

			elif find_en == 'timezones' or find_en == 'borders':

				otvet = list[find_en]
				text = text + " - "

				for i in otvet:
					text+= i + ' , '
				text = text[0:-2]
				text+=' .'

			elif find_en == 'population':
				otvet = list[find_en]

				source = "{:,d}"
				otvet = source.format(otvet)   # форматирования для удобного чтения больших чисел
				text = text + " - " + str(otvet)

			elif find_en == 'area':

				otvet = list[find_en]
				source = "{:,d} км²"
				otvet = source.format(int(otvet))   # форматирования для удобного чтения больших чисел
				text = text + " - " + str(otvet)

			elif find_en == 'topLevelDomain':
				
				otvet = list[find_en]
				text = text + " - " + str(otvet[0])

			elif find_en == 'flag':

				path_to_jpg = 'C:/Main/Programming/PythonProjects/CountryInfoBot_VK/Photos/'+country+'.jpg'
				path_to_svg = 'C:/Main/Programming/PythonProjects/CountryInfoBot_VK/Photos/'+country+'.svg'

				if os.path.exists(path_to_jpg):
					print('Картинка уже есть')
				else:
					print('Файл не существует')

					url = str(list[find_en])
					print(url)
					img = urllib.request.urlopen(url).read()
					out = open(path_to_svg, "wb")   # скачиваем картинку
					out.write(img)
					out.close()

					print("скачали SVG картинку")

					process = api.convert({
						'inputformat': 'svg',  # исходный формат
						'outputformat': 'jpg',  # формат в который нужно конвертировать 
						'input': 'upload',
						'file': open(path_to_svg, 'rb'),   # картинка для конвертации
						"converteroptions": {
							"resize": "500x500",   # обрезаем картинку до 500х500
						}
					})
					process.wait() # wait until conversion finished
					process.download(path_to_jpg) # download output file
					os.remove(path_to_svg)  #delete svg file - удаляем svg фото после конвертации

					print("конвертировали SVG картинку в JPEG")

				photo = upload.photo_messages(photos=path_to_jpg)[0]

			else:
				otvet = perevod(list[find_en],'en-ru')        # переводим
				text = text + " - " + str(otvet)
		except:

			print("Ошибка!")
			text = 'Такой команды нет ! Чтобы узнать список команд напиши : "что ты умеешь" '

	try:
		# отправляем сообщение
		vk.messages.send(
		user_id = message.user_id,				 # кому
		message = text,							 # сообщение хранится в переменной 'text'
		attachment = 'photo{}_{}'.format(photo['owner_id'], photo['id'])
		)
	except:
		# отправляем сообщение
		vk.messages.send(
		user_id = message.user_id,				# кому
		message = text							# сообщение хранится в переменной 'text'
		)

# ожидаем события
for event in longpoll.listen():
	# если новое сообщение
	if event.type == VkEventType.MESSAGE_NEW and event.to_me:
		# получаем или создаём id пользователя в базе данных
		user, _ = User.get_or_create(vk_id=event.user_id) 
		if user.state == 0:
			state0(event)