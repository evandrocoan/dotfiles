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
shopt -s dotglob; mv -v ~/Downloads/MyLinuxSettings/* ~
```
The `dotglob` option forces the bash to include filenames beginning with a '.' in the results of
pathname expansion. Hence, allowing us to move hidden files with `mv`.




