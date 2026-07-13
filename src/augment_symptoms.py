import os
import pandas as pd
import numpy as np

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(root_dir, 'data', 'symptoms.csv')
    output_path = os.path.join(root_dir, 'data', 'symptoms_augmented.csv')

    df = pd.read_csv(input_path)
    
    # Normalisasi pola_ruam karena frontend hanya bisa boolean (0/1)
    df['pola_ruam'] = 1
    
    # Target 30 variations per row to make it highly robust (180 * 30 = 5400 rows)
    VARIATIONS = 30
    
    new_rows = []
    
    for idx, row in df.iterrows():
        # Keep the original
        new_rows.append(row.to_dict())
        
        # Tentukan fitur patognomonis (core feature) yang TIDAK BOLEH diubah menjadi 0
        core_feature = None
        if row['label'] == 'cacar':
            core_feature = 'vesikel'
        elif row['label'] == 'campak':
            core_feature = 'koplik_spot'
        elif row['label'] == 'rubella':
            core_feature = 'kelenjar_bengkak'
        
        for _ in range(VARIATIONS - 1):
            aug_row = row.copy()
            
            # Perturb duration of fever by -1, 0, or 1 days
            durasi = aug_row['durasi_demam'] + np.random.randint(-1, 2)
            aug_row['durasi_demam'] = max(1, min(14, durasi))  # clamp 1-14 days
            
            # Randomly flip 1 or 2 binary features to simulate noisy/incomplete real-world symptoms
            if np.random.rand() > 0.5:
                binary_cols = ['demam_tinggi', 'demam_ringan', 'koplik_spot', 'kelenjar_bengkak',
                               'vesikel', 'konjungtivitis', 'nyeri_sendi', 'sakit_tenggorokan',
                               'pilek', 'lemas_malaise']
                
                # Jangan pernah memilih core feature untuk dibalik
                if core_feature in binary_cols:
                    binary_cols.remove(core_feature)
                    
                flip_col = np.random.choice(binary_cols)
                
                # Jangan pernah matikan (0) core feature secara tidak sengaja walau dari kombinasi lain
                aug_row[flip_col] = 1 - aug_row[flip_col]
                
                # Safety check: paksa core feature tetap 1 (kalau aslinya 1)
                if core_feature and row[core_feature] == 1:
                    aug_row[core_feature] = 1
            
            new_rows.append(aug_row.to_dict())
            
    aug_df = pd.DataFrame(new_rows)
    
    # Shuffle the dataset
    aug_df = aug_df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    aug_df.to_csv(output_path, index=False)
    print(f"Symptom augmentation complete! Saved {len(aug_df)} rows to {output_path}")

if __name__ == '__main__':
    main()
