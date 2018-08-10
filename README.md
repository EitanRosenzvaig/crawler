# Crawlers

This project manages the Crawling infrustructure of EsMio.


## Install
```
sudo apt-get update
sudo apt-get install python3-pip
pip3 install --upgrade pip
pip3 install --user virtualenv
python3 -m virtualenv /opt/esmio
source /opt/esmio/bin/activate

pip install selenium
pip install Scrapy
pip install functools32
pip install pymongo

pip install pathlib
pip install money-parser
pip install bs4
```
## Instalar chrome driver:

#### Opcion automatica: (No funciona por ahora)
`sudo apt-get install libarchive-tools`
#platform options: linux32, linux64, mac64, win32
```
PLATFORM=linux64
VERSION=$(curl http://chromedriver.storage.googleapis.com/LATEST_RELEASE)
curl http://chromedriver.storage.googleapis.com/$VERSION/chromedriver_$PLATFORM.zip | sudo bsdtar -xvf - -C /usr/local/bin/
```

#### Opcion manual: Descargar y colocar en el path
```
curl -o ./chromedriver_linux64.zip https://chromedriver.storage.googleapis.com/2.41/chromedriver_linux64.zip
mv chromedriver_linux64.zip /usr/local/bin/
unzip /usr/local/bin/chromedriver_linux64.zip
rm /usr/local/bin/chromedriver_linux64.zip
```

### Instalar Mongo DB
Follow these instructins:
https://medium.com/mongoaudit/how-to-upgrade-mongodb-to-latest-stable-version-9607266834cf


## Instalar Chrome
```
export CHROME_BIN=/usr/bin/google-chrome
export DISPLAY=:99.0
sudo apt-get install xvfb
```
Put content of https://gist.github.com/dmitriy-kiriyenko/974392 `xvfb` file in `/etc/init.d/xvfb`
```
sh -e /etc/init.d/xvfb start
sudo apt-get update
sudo apt-get install -y libappindicator1 fonts-liberation libasound2 libgconf-2-4 libnspr4 libxss1 libnss3 xdg-utils
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome*.deb
```

## Mongo DB setup
Type `mongo` in shell
```
db.createUser({
    user: 'app',
    pwd: '[SOMEPASSWORD]',
    roles: [{ role: 'dbOwner', db:'esmio'}]
})
```
now enable access for outside:
`sudo vim /etc/mongod.conf`
 Apply this:
 ```
# network interfaces
net:
  port: 27017
#  bindIp: 127.0.0.1  <- comment out this line
  .............
security:
  authorization: 'enabled'
```
## Running all crawlers from command line
from ropa directory execute:
```
scrapy list|xargs -n 1 scrapy crawl
```

Or to run an specific crawler:
```
scrapy crawl xl
```