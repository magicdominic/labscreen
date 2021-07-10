sudo apt-get install omxplayer
python3 -m pip install -U curses
python3 -m pip install -U thread 
python3 -m pip install -U signal
python3 -m pip install -U curses
python3 -m pip install -U pygame
sudo cp labscreen_audio.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable labscreen_audio.service
sudo systemctl restart labscreen_audio.service
#set desktop
export DISPLAY=:0.0
pcmanfm --wallpaper-mode=fit --set-wallpaper /home/pi/labscreen/Gefaessnamen_bildschirm.png
