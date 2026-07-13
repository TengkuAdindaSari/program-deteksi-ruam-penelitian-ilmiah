import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set style
sns.set_theme(style="whitegrid")
plt.rcParams['font.sans-serif'] = 'Arial'
plt.rcParams['font.family'] = 'sans-serif'

# 1. Count images in data/images/
classes = ['campak', 'rubella', 'cacar']
splits = ['train', 'test']
image_counts = {}

# We check lowercase names as defined in preprocessing.py CLASSES
for c in classes:
    image_counts[c] = {}
    for s in splits:
        folder = os.path.join('data', 'images', c, s)
        if os.path.exists(folder):
            files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
            image_counts[c][s] = len(files)
        else:
            image_counts[c][s] = 0

# 2. Count symptoms in symptoms.csv
symptom_counts = {'campak': 0, 'rubella': 0, 'cacar': 0}
symptoms_csv = os.path.join('data', 'symptoms.csv')
if os.path.exists(symptoms_csv):
    df = pd.read_csv(symptoms_csv)
    counts = df['label'].value_counts()
    for c in classes:
        symptom_counts[c] = int(counts.get(c, 0))

print("Image Counts:", image_counts)
print("Symptom Counts:", symptom_counts)

# Generate Plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
fig.patch.set_facecolor('#FFFFFF')

# Color palette
colors_train = '#4a90e2'
colors_test = '#f5a623'
colors_sym = '#2ca02c'

# Plot 1: Image Distribution
categories = [c.capitalize() for c in classes]
train_vals = [image_counts[c]['train'] for c in classes]
test_vals = [image_counts[c]['test'] for c in classes]

x = np.arange(len(categories))
width = 0.35

rects1 = ax1.bar(x - width/2, train_vals, width, label='Train Set (80%)', color=colors_train)
rects2 = ax1.bar(x + width/2, test_vals, width, label='Test Set (20%)', color=colors_test)

ax1.set_title('Distribusi Dataset Citra (Images)', fontsize=14, fontweight='bold', pad=15)
ax1.set_xticks(x)
ax1.set_xticklabels(categories, fontsize=12)
ax1.set_ylabel('Jumlah Gambar', fontsize=12)
ax1.legend(fontsize=10)

# Add values on top of bars
def autolabel(rects, ax):
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{int(height)}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

autolabel(rects1, ax1)
autolabel(rects2, ax1)

# Plot 2: Symptoms Distribution
sym_vals = [symptom_counts[c] for c in classes]
rects3 = ax2.bar(categories, sym_vals, width*1.5, color=colors_sym, label='Gejala Klinis')
ax2.set_title('Distribusi Dataset Gejala Klinis (CSV)', fontsize=14, fontweight='bold', pad=15)
ax2.set_ylabel('Jumlah Baris Data', fontsize=12)
ax2.set_xticklabels(categories, fontsize=12)

for rect in rects3:
    height = rect.get_height()
    ax2.annotate(f'{int(height)}',
                xy=(rect.get_x() + rect.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=10, fontweight='bold')

plt.suptitle('Distribusi Kelas Dataset - DermDetect', fontsize=18, fontweight='bold', y=0.98, color='#1a1a2e')
plt.tight_layout()

# Ensure model directory exists
os.makedirs('model', exist_ok=True)
plt.savefig('model/dataset_distribution.png', dpi=150, bbox_inches='tight')
print("Saved distribution plot to model/dataset_distribution.png")
