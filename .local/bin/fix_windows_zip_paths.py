#! /usr/bin/env python3
import os

# already created directories, walk works topdown, so a child dir
# never creates a directory if there is a parent dir with a file.
made_dirs = set()

for root, dir_names, file_names in os.walk('.'):
    for file_name in dir_names + file_names:
        # print( 'file_name', repr(file_name) )
        continue_now = 0
        bad_chars = ('\uf05c', '\\')
        for bad in bad_chars:
            if bad not in file_name:
                continue_now += 1
                break
        if continue_now >= len(bad_chars):
            continue

        alt_file_name = file_name
        for bad in bad_chars:
            alt_file_name = alt_file_name.replace(bad, '/')
        if alt_file_name.startswith('/'):
            alt_file_name = alt_file_name[1:]  # cut of starting dir separator

        if alt_file_name.find('/') < 0:
            continue
        alt_dir_name, alt_base_name = alt_file_name.rsplit('/', 1)
        print( 'alt_dir', alt_dir_name )
        full_dir_name = os.path.join(root, alt_dir_name)
        if full_dir_name not in made_dirs:
            os.makedirs(full_dir_name, exist_ok=True)  # only create if not done yet
            made_dirs.add(full_dir_name)
        os.rename(os.path.join(root, file_name),
                  os.path.join(root, alt_file_name))
