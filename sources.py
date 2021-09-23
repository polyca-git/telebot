#Import ettigim kutuphaneler.
import os, re, string, requests, random, time, telegram, logging, json
import youtube_dl, wikipedia, wolframalpha
import urllib.request
from difflib import SequenceMatcher
from replit import db
###############Importlar bitti####################

#Burada Telegram Key, Wolfram Key ve Youtube API keylerini girin
telegram_token = os.environ['TELE-TOKEN']
wolfram_token = os.environ['WOLFRAM']
yt_key = os.environ['YT_KEY']
##################################################################
#Wolfram Client ve Telegram bot objeleri olusturuluyor.
wolf_client = wolframalpha.Client(wolfram_token)
bot = telegram.Bot(telegram_token)
##################################################################

#Indirilecek Youtube videolari icin maximum dakika.
max_download_min=20
#Botun muhabbetlerinde yakinlik orani 0.4-0.7 arasi ideal.
similar_rate=0.4
#Her bir mahrem arasinda beklenecek süre
mahrem_sleep_second=0.5
#Bot cevap verirken en yüksek ihtimalde benzesenler arasinda rastgele secim yapacagi örnek küme boyutu.
random_take=5
#Maximum tek seferde izin verilen mahrem indirme sayisi
max_mahrem=20
####################################################################

class SourceFunctions:
  #YoutubeAPI ile video süresini dakika cinsinden kontrol ettigimiz fonksiyon.
  def checkTime(id):
    #Video bulunuyor
    search_url = f'https://www.googleapis.com/youtube/v3/videos?id={id}&key={yt_key}&part=contentDetails'
    #Adresten response cekiliyor
    req = urllib.request.Request(search_url)
    response = urllib.request.urlopen(req).read().decode('utf-8')
    #json a parse ediliyor
    data = json.loads(response)
    #gelen veride items node una gidiliyor
    all_data = data['items']
    #items altindan duration cekiliyor gelen veri PT2H43M6S, saat yoksa PT25M13S gibi de gelebiliyor, asagida bu veriyi parse ediyorum
    duration = all_data[0]['contentDetails']['duration']
    hours = 0
    mins = 0
    secs = 0
    if "H" in duration:
      vid_time= duration.split("PT")
      op = vid_time[1].split("H")
      hours=int(op[0])
      if "M" in op[1]:
        op = op[1].split("M")
        mins = int(op[0])
      if "S" in op[1]:
        op = op[1].split("S")
        secs=int(op[0])
    elif "M" in duration:
      vid_time= duration.split("PT")
      op=vid_time[1].split("M")
      mins=int(op[0])
      if "S" in op[1]:
        op = op[1].split("S")
        secs=int(op[0])
    elif "S" in duration:
      vid_time = duration.split("PT")
      op = vid_time[1].split("S")
      secs= int(op[0])
    #dakika cinsinden verinin son halini aliyorum
    total_mins=(hours*60)+mins+(secs/60)
    print(str(total_mins)+" dakika uzunlugunda video talep edildi.")
    return total_mins
  #############################################################

  #Iki string arasindaki benzerlik oranini bulan fonksiyon.
  def similar(a, b):
      return SequenceMatcher(None, a, b).ratio()
  #########################################################

  #Mp3 ler icin youtube ayarlari
  ydl_opts_mp3 = {
      'format': 'bestaudio/best',
      'outtmpl': "./%(id)s.%(ext)s",
      'postprocessors': [{
          'key': 'FFmpegExtractAudio',
          'preferredcodec': 'mp3',
          'preferredquality': '192',
      }],
  }  
  #Mp4 ler icin youtube ayarlari
  ydl_opts_video = {
    'format': 'mp4',
    'outtmpl': "./%(id)s.%(ext)s",
  }
  ###################################

  #Indirilen dosyalari yolladiktan sonra silmek icin bir fonksiyon
  def removeFile(path):
      os.remove(path)   
  ###############################################


  #Loglama konfigurasyonu
  logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
  logger = logging.getLogger(__name__)


  #/start komutu, öylesine merhaba diye cevap veriyor
  def start(update, context):
      update.message.reply_text('Merhaba!')
  ###################################################

  #/mp3 komutu yanina konulan metni youtube da aratip videoyu mp3 olarak geri yolluyor.
  def mp3(update, context):
    #Metinde /mp3 kismini ayir
    quest=str(update.message.text).split("/mp3")
    #metnin geri kalaninin bosluk karakterlerini + ile degistir. Ascii karakterleri ignore et.
    quest[1]=quest[1].replace(" ","+").encode("ascii", "ignore").decode()
    #Olusturulan adrese git ve html veriyi cek
    html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + quest[1])
    #Regex kullanarak Youtube video kodlarini bul
    video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
    #Videonun izin verilen max süreden uzun olup olmadigini kontrol et.
    if checkTime(video_ids[0])<=max_download_min:
      #Ilk video kodunun linkini olustur
      url="https://www.youtube.com/watch?v=" + video_ids[0]
      update.message.reply_text('Lütfen bekle patron, buldum sanirim...')
      #tam haliyle düyeltilmis video URL'imiz
      _id = url.strip()
      #YoutubeDL ile indirme ve convert islemini baslat ve meta bilgisini bu degiskene kaydet.
      meta = youtube_dl.YoutubeDL(ydl_opts_mp3).extract_info(_id)
      #Zaten indirilmis olan dosyanin ayni ismini generate et
      save_location = meta['id'] + ".mp3"
      #Ses dosyasini chate geri yükle
      bot.send_audio( chat_id=update.message.chat.id, audio=open(save_location, 'rb'))
      update.message.reply_text('Görev tamamlandi patron!')
      #Ses dosyasini sil
      removeFile(save_location)
    else:
      update.message.reply_text(str(max_download_min)+" dakikadan uzun videolari indirmiyorum.")
  #####################################################################

  #/yardim komutu
  def yardim(update, context):
      #Ayni klasördeki yardim isimli dosyanin icerigini chat e yolla
      with open('./yardim', 'r') as f:
        update.message.reply_text(f.read())
  ################

  #/wiki komutu
  def wiki(update, context):
    #wikipedia modülünün objesinin dil ayari
    wikipedia.set_lang("tr") 
    #/wiki den itibaren mesaji böl
    quest=str(update.message.text).split("/wiki")
    #Bosluk karakterlerini + ile degistir
    quest[1]=quest[1].replace(" ","+")
    #wikipediadan sonucu al sentences de ik kac cümlenin gelecegi.
    wiki_res = wikipedia.summary(quest[1], sentences=5)
    #wikipedi sonucunu geri yükle
    update.message.reply_text(wiki_res)
  ################

  #/ask komutu
  def ask(update, context):
    try:
      #/ask tan itibaren gelen mesaji böl
      quest=str(update.message.text).split("/ask ")
      #metni Wolfram Alpha da arat.
      wolfram_res = next(wolf_client.query(quest[1]).results).text
      #Sonucu chat e geri yolla
      update.message.reply_text(wolfram_res)
    except:
      update.message.reply_text("Anlayamadim.")
  #############

  #/ymp3 komutu
  def ymp3(update, context):
    #Metindeki bosluklari yok et ve metni /ymp3 ten itibaren böl 
    url=str(update.message.text).replace(" ","").split("/ymp3")
    update.message.reply_text('Lütfen bekle patron, ariyorum...')
    #eger metin böyle basliyorsa
    if "https://www.youtube.com/results?search_query=" in url[1]:
      #Youtube video kodunu bulmak icin böl
      quest=url[1].split("https://www.youtube.com/results?search_query=")
    #eger metin böyle basliyorsa
    elif "https://youtu.be/" in url[1]:
      #Youtube video kodunu bulmak icin böl
      quest=url[1].split("https://youtu.be/")
    else:
      #Metin böyle baslamiyorsa indiremeyecegini söyle.
      update.message.reply_text('Bu videoyu indiremem...')
      return
    #######Buradan sonrasini anlamak icin mp3 fonksiyonuna bakin, ayni cünkü
    if checkTime(quest[1])<=max_download_min:
      _id = url[1].strip()
      meta = youtube_dl.YoutubeDL(ydl_opts_mp3).extract_info(_id)
      save_location = meta['id'] + ".mp3"
      bot.send_audio( chat_id=update.message.chat.id, audio=open(save_location, 'rb'))
      removeFile(save_location)
      update.message.reply_text('Görev tamamlandi patron!')
    else:
      update.message.reply_text(str(max_download_min)+" dakikadan uzun videolari indirmiyorum.")
  ########################################################################


  #/mahrem komutu, resim yükleme sitesinden rastgele resim getirir
  def mahrem(update, context):
    #while döngüsünü basarili denemeler bitince bitirmek icin
    run=True
    #kac basarili deneme oldugunu bulmak icin
    count=0
    #/mahrem den itibaren metni böl
    quest=str(update.message.text).replace(" ","").split("/mahrem")
    try:
      #kullanicinin sayi girip girmedigini dene
      total=int(quest[1])
      #eger talep edilen mahrem izin verilem max mahrem sayisindan fazlaysa uyar
      if total>max_mahrem:
        update.message.reply_text(str(max_mahrem)+' den fazla mahrem getiremem.')
        #fonksiyonu bu noktada bitir
        return
      else:
        update.message.reply_text(str(total)+' adet mahrem getiriliyor...')
    except:
      #kisi sayi belirtmediyse 1 tane mahrem getir.
      total=1
      update.message.reply_text('Bir tane mahrem getiriliyor...')
    #0 dan fazla ve max mahrem sayisina esit veya az mahrem istenmisse 
    if total>0 and total<=max_mahrem: 
      #döngü burada basliyor
      while run:
        #rastgele yazi ve rakam barindiran 5-6 karakter arasi bir kod olustur
        code = ''.join(random.choice(string.ascii_lowercase + string.digits) for e in range(random.randint(5, 6)))
        #URL i olustur
        url = 'https://prnt.sc/' + code
        #bu header larla site icerigini getir
        r = requests.get(url, headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'})
        #Regex ile resimleri bul
        a = re.findall("\"image\-container.*\<img\sclass\=\".*\"\ssrc\=(.*)\"", r.text)
        #resim adresi yoksa döngüyü kir
        if not a:
          continue
        #resim adresi 2 karakterden azsa döngüyü kir
        if len(a[0].split('"')) < 2:
          continue
        #stringi " karakterlerinden itibaren böl ve birinci dizi elemanini al(resim adresi)
        img = a[0].split('"')[1]
        #yedek degisken olustur
        img_addr = img
        #yerel adres gelmisse döngüyü kir(//ile basliyorsa)
        if img.startswith('//'):
          continue
        #adresin son olarak bos olup olmadigini kontrol et, bossa döngüyü kir
        if not img:
          continue
        #resmin yüklenecegi adresi olustur
        img_addr = './ms-images/' + img.split('/')[-1]
        #eger ms-images isimli bir klasör yoksa olustur
        if not os.path.exists('./ms-images'):
          os.mkdir('ms-images')
        #resim verisini adresten su headerlarla cek
        img_data = requests.get(img, headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}).content
        #olusturmus oldugumuz adrese resim icerigini kaydet
        with open(img_addr, 'wb') as handler:
          handler.write(img_data)
        #basarili sonuclarin sayisini 1 arttir
        count+=1
        #belirtilen süre kadar bekle
        time.sleep(mahrem_sleep_second)
        #maximum basarili denemeye ulasilip ulasilmadigini dene, ulasilmissa ana döngüyü bitir
        if count>=total:
          run=False
        #olusan soyayi chat'e yükle
        bot.send_photo( chat_id=update.message.chat.id, photo=open(img_addr, 'rb'))
        #yereldeki dosyayi sil
        removeFile(img_addr)
    update.message.reply_text('Mahremler getirildi.')
  #########################################################################

  #Geri kalan tüm mesajlar icin icerik kontrolü yapan fonksiyon
  def otherMessages(update, context):
    #url diye bir degisken olustur ve bosluklari sil(direkt Youtube linki yapistirildiginda kontrol etmek icin)
    url=str(update.message.text).replace(" ","")
    #gelen verinin su sekilde baslayip baslamadigini kontrol et
    if url.startswith("https://youtu.be/") or url.startswith("https://www.youtube.com/"):
      update.message.reply_text('Lütfen bekle patron, ariyorum...')
      #Buradan sonrasinin aciklamasi icin ypm3 fonksiyonuna bak
      if "https://www.youtube.com/results?search_query=" in url:
        quest=url.split("https://www.youtube.com/results?search_query=")
      elif "https://youtu.be/" in url:
        quest=url.split("https://youtu.be/")
      else:
        update.message.reply_text('Bu videoyu indiremem...')
        return
      if checkTime(quest[1])<=max_download_min:
        _id = url.strip()
        #ilk mp3 ayariyla indiriyorum
        meta = youtube_dl.YoutubeDL(ydl_opts_mp3).extract_info(_id)
        save_location = meta['id'] + ".mp3"
        #mp3 ü yüklüyorum ve
        bot.send_audio( chat_id=update.message.chat.id, audio=open(save_location, 'rb'))
        removeFile(save_location)
        update.message.reply_text('Müzik geldi, simdi video geliyor!')
        #sonra da mp4 ayariyla indiriyorum
        meta = youtube_dl.YoutubeDL(ydl_opts_video).extract_info(_id)
        save_location = meta['id'] + ".mp4"
        #ve videoyu chate yüklüyorum
        bot.send_video( chat_id=update.message.chat.id, video=open(save_location, 'rb'), supports_streaming=True)
        removeFile(save_location)
        update.message.reply_text('Görev tamamlandi patron!')
      else:
        print("else")
        update.message.reply_text(str(max_download_min)+" dakikadan uzun videolari indirmiyorum.")
        return
    #####################################################################
    #Eger herhangi bir mesajda bot kelimesi gecmisse, botun muhabbeti buradan ayarlaniyor
    elif "bot" in str(update.message.text).lower():
      #kücük karakter olarak bot kelimesini sil
      msg=str(update.message.text).lower().replace("bot", "").strip().encode("ascii", "ignore").decode()
      #veri tabanindaki(replit vt, dictionary mantiginda tutar) keylerle, value'leri bos olan bir dictionary olustur
      keys = dict.fromkeys(db)
      #verilecek cevap stringi
      response=""
      #bos value lu keylerimiz arasinda dolaniyoruz(key ler sorulari iceriyor)
      for key in keys:
        #benzerlik bulup bu gecici degiskene atiyorum
        new_rate=similar(msg.lower(),key.lower())
        #keyin value sini bulunan benzerlik rate i yapiyorum
        keys[key]=new_rate
      #bu lazim olacak
      temp_keys= keys
      #benzerliklere göre dictionary mi yüksekten aza siraliyorum
      keys = sorted(keys.items(), key=lambda x: x[1], reverse=True)
      #Belirtilen karaktere kadat(1 ile o karakter arasinda rastgele) ilk bir veya birkac girdiyi aliyorum
      keys = list(keys)[:random.randint(1,random_take)]
      #son kalan keylerden rastgele bir tanesini seciyorum
      random_key = random.choice(list(keys))
      if float(temp_keys[random_key[0]])>=similar_rate:
        #olusan tek karakterli dictonary deki key'in value'sini veri tabaninda aratiyorum
        response = db[next(iter(random_key))]
        #eger böyle bir deger varsa chat'e value'sini yolluyorum
        if response:
          update.message.reply_text(response)
      #Yeterince güvenmedigimiz sonucu geri yollamiyoruz
      else:
        update.message.reply_text("Valla ne desem bilemedim.")
    #Üstteki durumlar disindaki tüm durumlarda
    else:
      try:
        #eger gelen mesaj bir baska mesaja cevap olarak gelmisse, yani reply_to_message.text diye bir deger gelen veride varsa
        if update.message.reply_to_message.text:
          #mesaja verilen cevap dolu ise
          if update.message.text:
            #veri tabanina yükleyecegimiz key alintilanan metin olacak
            key=update.message.reply_to_message.text
            #value ise verilen cevap olacak
            value=update.message.text
            #veri tabanina girdi yapilirken olanlarin kaydini tutmak icin yerel doya ac
            with open("feeded_log", "a") as myfile:
              #dosyada kaydedilecek soru ve cevaplari logla
              myfile.write(key+" : "+value)
              myfile.write("\n")
            #kaydedilecek key ve value'da / karakteri  varsa sil
            key = key.replace("/","")
            value = value.replace("/","")
            #veri tabanina veriyi kaydet
            db[key]=value
            print("db_registered")
      except:
        pass
      pass
  #########################################################################  

  #Hatalari loglama fonksiyonu
  def error(update, context):
      logger.warning('Güncelleme "%s" hataya sebebiyet verdi "%s"', update, context.error)
  ############################