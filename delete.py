
import os
folder = 'data/images/rubella/training'
deleted = 0
for f in os.listdir(folder):
    if f.startswith('aug_'):
        os.remove(os.path.join(folder, f))
        deleted += 1
print(f'Hapus {deleted} file augmentasi')