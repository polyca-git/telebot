import os
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from sources import SourceFunctions
#Buraya Telegram Tokeni girin
telegram_token = os.environ['TELE-TOKEN']
###################################################################
source_classes = SourceFunctions()

#Otomatik calisan ana fonksiyon
def main():
  #Telegram Updater objesini token degeriyle olustur
  updater = Updater(telegram_token, use_context=True)
  # Handler lari kaydetmek icin dispatcher i getir
  dp = updater.dispatcher
  # Komutlari fonksiyonlarla eslestir
  dp.add_handler(CommandHandler("start", source_classes.start))
  dp.add_handler(CommandHandler("yardim", source_classes.yardim))
  dp.add_handler(CommandHandler("help", source_classes.yardim))
  dp.add_handler(CommandHandler("mp3", source_classes.mp3))
  dp.add_handler(CommandHandler("mahrem", source_classes.mahrem))
  dp.add_handler(CommandHandler("wiki", source_classes.wiki))
  dp.add_handler(CommandHandler("ask", source_classes.ask))
  dp.add_handler(CommandHandler("ymp3", source_classes.ymp3))
  #Komut disi fonksiyonlari handle etmek icin kullanilacak fonksiyonu belirt
  dp.add_handler(MessageHandler(Filters.text, source_classes.otherMessages))
  #Hatalarin paslanacagi fonksiyonu belirt
  dp.add_error_handler(source_classes.error)
  #Botu baslat
  updater.start_polling()
  updater.idle()


if __name__ == '__main__':
    main()