My linux configurations used on Mint XFCE 17.3, Ubuntu and Cygwin
===============
Bash, ... vim.




### To install them

First backup your settings, clone this repo using this commmand:
```
git clone --recursive https://github.com/evandrocoan/MyLinuxSettings.git ~/Downloads/MyLinuxSettings
```

And move them to your main's user folder replacing your own settings:
```
rsync -r -t -v -s ~/Downloads/MyLinuxSettings ~/
```

After installing, reload the `XFCE` components, so the settings does not get overridden.

This should reload the `XFCE` panel components:
```
xfce4-panel -r
xfce4-terminal -r
xfce4-session -r
xfce4-notifyd -r
xfce4-power-manager -r
```

For other components, research how it could be done, or just install the settings by using another
user account or desktop environment as KDE Plasma, Mate, Cinnamon, etc.


