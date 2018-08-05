# Crawlers

This project contains all the scrapy crawlers


## Install

sudo apt-get update
sudo apt-get install python-scrapy
sudo apt-get install python-pip

pip install selenium
pip install Scrapy
pip install functools32
pip install pymongo

pip install pathlib
pip install money-parser
pip install bs4

###Instalar chrome driver:

#TODO: Arreglar la opcion automatica. Se copia el file pero sin modo ejecion

sudo apt install libarchive-tools
# platform options: linux32, linux64, mac64, win32
PLATFORM=linux64
VERSION=$(curl http://chromedriver.storage.googleapis.com/LATEST_RELEASE)
curl http://chromedriver.storage.googleapis.com/$VERSION/chromedriver_$PLATFORM.zip | sudo bsdtar -xvf - -C /usr/local/bin/

Opcion manual: Descargar y colocar en el path https://chromedriver.storage.googleapis.com/2.41/chromedriver_linux64.zip

### Instalar Mongo DB
sudo apt install -y mongodb


### Instalar Chrome
export CHROME_BIN=/usr/bin/google-chrome
export DISPLAY=:99.0
sh -e /etc/init.d/xvfb start
sudo apt-get update
sudo apt-get install -y libappindicator1 fonts-liberation libasound2 libgconf-2-4 libnspr4 libxss1 libnss3 xdg-utils
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome*.deb

## Running all crawlers from command line
from ropa directory execute:
```
scrapy list|xargs -n 1 scrapy crawl
```

Or to run an specific crawler:
```
scrapy crawl xl
```