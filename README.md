# My linux configurations (or Dotfiles)

These are used on Mint XFCE 19.1, Ubuntu and Cygwin.

These are settings for bash, vim, etc.


### To install them

First backup your settings, clone this repository using this command:
```
git clone --recursive https://github.com/evandrocoan/MyLinuxSettings.git ~/Downloads/MyLinuxSettings
```

And move them to your main's user folder replacing your own settings:
```
rsync -r -t -v -s ~/Downloads/MyLinuxSettings/ ~/
```

After installing, reload the `XFCE` components, so the settings does not get overridden.

This should reload the `XFCE` panel components:
```
xfce4-panel -r
```

For other components, research how it could be done, or just install the settings by using another
user account or desktop environment as KDE Plasma, Mate, Cinnamon, etc.


### Manual installation

Add `GRUB_CMDLINE_LINUX="i915.enable_rc6=0"` to `/etc/default/grub`:
1. https://unix.stackexchange.com/questions/401746/drm-i915-resetting-chip-after-gpu-hang
1. https://askubuntu.com/questions/857123/how-to-tweak-intel-hd-graphics-on-ubuntu-16-04
```
GRUB_CMDLINE_LINUX="i915.enable_rc6=0 i915.semaphores=0"
# after changing this, run
# sudo update-grub; sudo update-grub2
```

Enable super user account login with `su`:
```
sudo passwd root
```


### To list all programs using a given port

```
sudo netstat -tulpn | grep 5060
```
1. https://www.cyberciti.biz/faq/what-process-has-open-linux-port/


### Install Sublime Text

1. https://www.sublimetext.com/3
1. Install StudioChannel:
   * `https://raw.githubusercontent.com/evandrocoan/StudioChannel/master/channel.json`
1. https://forum.sublimetext.com/t/multiple-sublime-processes-with-different-environment/34575

Setup it to start maximized with:
1. [.local/bin/open_maximized.sh](.local/bin/open_maximized.sh)


### Enable hibernation

1. Set swap file size to 20GG on the next step tutorial
1. https://forums.linuxmint.com/viewtopic.php?f=42&t=284100 [GUIDE] How to hibernate to a swap file in Linux Mint 19.x
1. https://forums.linuxmint.com/viewtopic.php?t=273202 How to enable hibernation with swap partion on Linux Mint 19


### ksuperkey

1. Clone and install https://github.com/hanschen/ksuperkey with `make` and `sudo make install`
1. Remove the `Super+L` to `xfce4-popup-whiskermenu` on `All Settings -> Keyboard -> Applications Shortcuts` and add it to `Super_L|m`
1. Then, run the command: `ksuperkey -e 'Super_L=Super_L|m'`


### Ksysguard & others

Add ppa repositories:
```
sudo add-apt-repository ppa:sporkwitch/autokey &&
sudo add-apt-repository ppa:hluk/copyq &&
sudo apt update
```

Install stuff:
```
sudo apt install -y autokey-gtk copyq mtp-tools gmtp imwheel openssh-server &&
sudo apt-get install -y flameshot nethogs python3 python-pip python3-pip &&
sudo apt-get install -y audacity gnome-gmail ksysguard wmctrl &&
sudo apt-get install -y xdotool grsync unison-gtk indicator-multiload &&
sudo apt-get install -y vim vim-gtk3 ncdu nemo glogg qps nemo-fileroller &&
pip install setuptools &&
pip3 install setuptools &&
pip install wheel &&
pip3 install wheel python-language-server
```

1. `qps`
1. `glogg`
1. `ncdu`
1. `nethogs`
1. Open `Preferred Applications` and set mailto as `gnome-gmail`
1. Open `Preferred Applications` and set File Manger as `nemo`
1. Open `KSysGuard` & `System Monitor` and Install KSysGuard System Monitor Tabs:
   * Hard Disk Totals - https://store.kde.org/p/1198291
   * System Load and Temps - https://store.kde.org/p/1198291
1. Open `Unisson` & `Grsync`
1. Add `System Load Monitor` widget to the main panel
1. Create keybind `,` (numpad comma), `autokey-run -p insert_dot`
   * https://github.com/autokey/autokey
1. Run `utokey-gtk --verbose &` for debugging it
1. https://unix.stackexchange.com/questions/192048/mount-mtp-android-device-in-linux-mint-17-1
1. https://unix.stackexchange.com/questions/389952/how-to-get-the-samsung-galaxy-s5-to-work-with-mtp-on-debian-9
1. Run `imwheel -b "4 5"`on system start up
   1. Create `~/.imwheelrc` with:
      * [.imwheelrc](.imwheelrc)
   1. https://wiki.archlinux.org/index.php/IMWheel
      * Use `imwheel -d --debug --kill` to list windows
   1. https://askubuntu.com/questions/285689/increase-mouse-wheel-scroll-speed
   1. https://mintguide.org/other/643-setup-the-mouse-scroll-wheel-speed.html#sel=13:4,13:14


### Optionally install KDE

1. 1 GB to install
   * `sudo apt-get install kde-standard kwin-addons`
1. 28 MB to install
   * `sudo apt install budgie-desktop-environment`
1. 128 MB to install
   * http://ubuntuhandbook.org/index.php/2018/11/install-cinnamon-desktop-4-0-ubuntu-18-04/
   * `sudo apt-get install cinnamon-desktop-environment`
   * Install applets:
     1. Cinnamenu
     1. Show desktop ++
     1. Collapsible Systray
     1. System Monitor


### Hide user account from login screen

Open **/var/lib/AccountsService/users/XXX** and add:
```
[User]
SystemAccount=true
```
1. https://forums.linuxmint.com/viewtopic.php?t=212990


### Install wine & others

1. Software Manager -> Twinkle -> Install
1. https://wiki.winehq.org/Ubuntu
1. https://www.cockos.com/licecap/
1. https://askubuntu.com/questions/785657/i-cant-install-gnome-schedule-on-ubuntu-16-04
1. https://askubuntu.com/questions/779946/how-do-i-install-lastfm-scrobblernewbie-at-ubuntu-stuff
1. http://www.aimp2.us/aimp3-download.php (install inside wine)
1. https://www.last.fm/about/trackmymusic?platform=windows (install inside wine)
1. https://askubuntu.com/questions/138908/how-to-execute-a-script-just-by-double-clicking-like-exe-files-in-windows
1. https://www.teamviewer.com/pt-br/download/linux/
1. https://askubuntu.com/questions/700712/how-to-install-wireshark
1. https://www.syntevo.com/smartgit/download/
   Sometimes ignored directories are containing tracked files in which case changes to these files might not show up automatically. If this is the case for you, you may disable this optimization by setting system property 'fileMonitor.excludeIgnoredDirectories=false'.


### Remove Default Keybinds

1. All Settings -> Window Manger -> Keyboard ->
   * Raise Window, `Alt+Shift+PgUp`
   * Lower Window, `Alt+Shift+PgDown`


### Create Default Keybinds

1. `Ctrl+Alt+J`, subl -n
1. `Ctrl+Alt+O`, gnome-calculator
1. `Ctrl+Alt+H`, gnome-system-monitor
1. `Ctrl+Print`, flameshot gui
1. [.local/bin/play_stop_music.sh](.local/bin/play_stop_music.sh)
   1. `Pause`, play_stop_music.sh space
   1. `Alt+Super+Up`, play_stop_music.sh Up
   1. `Alt+Super+Down`, play_stop_music.sh Down
   1. `Alt+Super+Left`, play_stop_music.sh F1
   1. `Alt+Super+Right`, play_stop_music.sh F2
1. `Alt+Super+0`, wmctrl -x -a aimp.exe.Wine
1. `Alt+Super+1`, wmctrl -x -a minilyrics.exe.Wine
   * To list active windows use `wmctrl -lx`

**`/home/evandro/.local/share/applications/lastfm.desktop`**
```
[Desktop Entry]
Version=1.1
Type=Application
Name=Last.fm
Comment=Listen to Last.fm radio
Icon=lastfm
Exec=wine "/home/evandro/.wine/dosdevices/c:/Program Files (x86)/Last.fm/Last.fm Scrobbler.exe"
Actions=
Categories=Audio;AudioVideo;Qt;
StartupNotify=true
```

**`/home/evandro/.local/share/applications/menulibre-aimp3.desktop`**
```
[Desktop Entry]
Version=1.1
Type=Application
Name=AIMP3
Comment=Music Player running on Wine
Icon=applications-other
Exec=wine "/home/evandro/Programs/AIMP3/AIMP.exe"
Actions=
Categories=AudioVideo;
```

**`/home/evandro/.local/share/applications/menulibre-minilyrics-wine.desktop`**
```
[Desktop Entry]
Version=1.1
Type=Application
Name=Minilyrics Wine
Comment=A small descriptive blurb about this application.
Icon=applications-other
Exec=wine "/home/evandro/.wine/dosdevices/c:/Program Files (x86)/MiniLyrics/MiniLyrics.exe"
Actions=
Categories=AudioVideo;
```


### Linux system information
```
inxi -Fxz

System:    Host: evandro-pc Kernel: 4.15.0-45-generic x86_64 bits: 64 compiler: gcc v: 7.3.0 Desktop: Xfce 4.12.3
           Distro: Linux Mint 19.1 Tessa base: Ubuntu 18.04 bionic
Machine:   Type: Desktop System: Gigabyte product: H110M-S2PH v: N/A serial: <filter>
           Mobo: Gigabyte model: H110M-S2PH-CF v: x.x serial: <filter> UEFI: American Megatrends v: F21 date: 06/09/2017
CPU:       Topology: Quad Core model: Intel Core i5-7400 bits: 64 type: MCP arch: Kaby Lake rev: 9 L2 cache: 6144 KiB
           flags: lm nx pae sse sse2 sse3 sse4_1 sse4_2 ssse3 vmx bogomips: 24000
           Speed: 800 MHz min/max: 800/3500 MHz Core speeds (MHz): 1: 800 2: 800 3: 800 4: 800
Graphics:  Device-1: Intel HD Graphics 630 vendor: Gigabyte driver: i915 v: kernel bus ID: 00:02.0
           Display: x11 server: X.Org 1.19.6 driver: modesetting unloaded: fbdev,vesa resolution: 1920x1080~60Hz
           OpenGL: renderer: Mesa DRI Intel HD Graphics 630 (Kaby Lake GT2) v: 4.5 Mesa 18.2.2 direct render: Yes
Audio:     Device-1: Intel 100 Series/C230 Series Family HD Audio vendor: Gigabyte Sunrise Point-H driver: snd_hda_intel
           v: kernel bus ID: 00:1f.3
           Sound Server: ALSA v: k4.15.0-45-generic
Network:   Device-1: Realtek RTL8111/8168/8411 PCI Express Gigabit Ethernet vendor: Gigabyte driver: r8169 v: 2.3LK-NAPI
           port: e000 bus ID: 01:00.0
           IF: enp1s0 state: up speed: 1000 Mbps duplex: full mac: <filter>
Drives:    Local Storage: total: 931.51 GiB used: 47.82 GiB (5.1%)
           ID-1: /dev/sda vendor: Western Digital model: WD10EZEX-00WN4A0 size: 931.51 GiB
Partition: ID-1: / size: 907.63 GiB used: 47.81 GiB (5.3%) fs: ext4 dev: /dev/dm-0
Sensors:   System Temperatures: cpu: 29.8 C mobo: 27.8 C
           Fan Speeds (RPM): N/A
Info:      Processes: 236 Uptime: 1h 13m Memory: 7.68 GiB used: 4.39 GiB (57.2%) Init: systemd runlevel: 5 Compilers:
           gcc: 7.3.0 Shell: bash v: 4.4.19 inxi: 3.0.27
```



