set -x;
defaultremmina="${HOME}/.local/share/remmina"
destinedir="${HOME}/.local/share/applications";
sourcedir="${HOME}/snap/remmina/5237/.local/share/remmina";

cp --verbose --no-clobber "$defaultremmina"/* "$sourcedir"

# clean up old desktop entries
rm "$destinedir"/remmina-script-*.desktop

xfceapplications="[";
for remmina in "$sourcedir"/*; do
  name="$(grep -oP '^name=.*$' "$remmina" | cut -c 6-)";
  if [[ "w$name" == 'w' ]]; then
    printf 'Error, missing name from "%s"' "$remmina";
    break;
  fi;
  basenamefile="$(basename "$remmina")";
  desktopfilename="remmina-script-${basenamefile}.desktop";
  xfceapplications="${xfceapplications} '${desktopfilename}',";
  printf '[Desktop Entry]
Version=1.1
Type=Application
Name=%s
Comment=Connect to remote desktops
Icon=org.remmina.Remmina
Exec=env BAMF_DESKTOP_FILE_HINT=/var/lib/snapd/desktop/applications/remmina_remmina.desktop /snap/bin/remmina "%s"
Actions=
Categories=X-XFCE;X-Xfce-Toplevel;menulibre-remminadesktops;
' "$name" "$remmina" > "${destinedir}/${desktopfilename}";
done && set +x && printf 'Include:\n%s' "${xfceapplications}";

xfceapplications="${xfceapplications}]";
xfceapplicationsmenu="$HOME/.config/menus/xfce-applications.menu";

python3 <<PYTHON3
import ast
import xml.etree.ElementTree

print("Parsing '$xfceapplicationsmenu'...")
originalxml = xml.etree.ElementTree.parse('$xfceapplicationsmenu')

found_menu = False;
found_rootmenu = False;
last_layout = None
last_menu = None

for elem in originalxml.getroot() or []:
  # print('looking', elem.tag)

  if elem.tag == "Layout":
    last_layout=elem

    for menu in elem:
      if menu.text == "menulibre-remminadesktops":
        print('Found element menulibre-remminadesktops')
        found_rootmenu = True;
        break

  elif elem.tag == "Menu":
    for menu in elem:
      if menu.tag == "Name" and menu.text == "menulibre-remminadesktops":
        print('Found menu menulibre-remminadesktops')
        found_menu = True;
        last_menu = elem
        break

if not found_rootmenu:
  new_tag = xml.etree.ElementTree.SubElement(last_layout, 'Menuname')
  new_tag.text = 'menulibre-remminadesktops'

if found_menu:
  originalxml.getroot().remove(last_menu)

new_menu = xml.etree.ElementTree.SubElement(originalxml.getroot(), 'Menu')
menu_name = xml.etree.ElementTree.SubElement(new_menu, 'Name')
menu_name.text = "menulibre-remminadesktops"

directory_name = xml.etree.ElementTree.SubElement(new_menu, 'Directory')
directory_name.text = "menulibre-remminadesktops.directory"

directory_dir = xml.etree.ElementTree.SubElement(new_menu, 'DirectoryDir')
directory_dir.text = "~/.local/share/desktop-directories"

include_dir = xml.etree.ElementTree.SubElement(new_menu, 'Include')
for item in ast.literal_eval("$xfceapplications"):
  filename_dir = xml.etree.ElementTree.SubElement(include_dir, 'Filename')
  filename_dir.text = item

Layout_dir = xml.etree.ElementTree.SubElement(new_menu, 'Layout')
merge_type = xml.etree.ElementTree.SubElement(Layout_dir, 'Merge')
merge_type.attrib["type"] = "menus"

for item in ast.literal_eval("$xfceapplications"):
  filename_dir = xml.etree.ElementTree.SubElement(Layout_dir, 'Filename')
  filename_dir.text = item

merge_files = xml.etree.ElementTree.SubElement(Layout_dir, 'Merge')
merge_files.attrib["type"] = "files"

originalxml.write('$xfceapplicationsmenu')
PYTHON3
