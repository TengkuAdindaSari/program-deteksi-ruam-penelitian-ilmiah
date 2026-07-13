import os
import pandas as pd
import numpy as np
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(root_dir, 'data', 'symptoms_augmented.csv')
    model_path = os.path.join(root_dir, 'model', 'rf_model.pkl')

    print(f"Membaca dataset gejala: {input_path}")
    df = pd.read_csv(input_path)

    # Pisahkan fitur dan label, serta hapus fitur yang tidak dipakai
    X = df.drop(columns=['label', 'durasi_demam', 'pilek'], errors='ignore')
    y = df['label']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print(f"Data latih: {len(X_train)} baris, Data uji: {len(X_test)} baris.")
    print("Melatih model Random Forest Classifier...")
    
    # Inisialisasi model
    rf = RandomForestClassifier(n_estimators=200, random_state=42, max_depth=15)
    rf.fit(X_train, y_train)

    print("Mengevaluasi model pada Test Set...")
    y_pred = rf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    
    print(f"\nAkurasi Random Forest: {acc*100:.2f}%\n")
    print(classification_report(y_test, y_pred))

    with open(model_path, 'wb') as f:
        pickle.dump(rf, f)
        
    print(f"Model berhasil disimpan di: {model_path}")

if __name__ == '__main__':
    main()
