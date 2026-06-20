import os
import sys
from app import create_app
from extensions import db
# pyrefly: ignore [missing-import]
from sqlalchemy import text

app = create_app()

def update_database():
    print("Checking database columns in 'diagnoses' table...")
    
    # 7 new symptom columns to add
    new_columns = {
        'demam_tinggi': 'TINYINT(1) DEFAULT 0',
        'pilek': 'TINYINT(1) DEFAULT 0',
        'sakit_tenggorokan': 'TINYINT(1) DEFAULT 0',
        'koplik_spot': 'TINYINT(1) DEFAULT 0',
        'nyeri_sendi': 'TINYINT(1) DEFAULT 0',
        'hilang_nafsu_makan': 'TINYINT(1) DEFAULT 0',
        'lemas': 'TINYINT(1) DEFAULT 0'
    }

    with app.app_context():
        # Get existing columns
        try:
            result = db.session.execute(text("SHOW COLUMNS FROM diagnoses"))
            existing_columns = [row[0] for row in result.fetchall()]
            print(f"Existing columns: {existing_columns}")
        except Exception as e:
            print(f"Error querying database columns: {e}")
            print("Assuming database is not initialized yet. create_all() will handle it.")
            return

        for col, col_type in new_columns.items():
            if col not in existing_columns:
                print(f"Adding column '{col}' to 'diagnoses' table...")
                try:
                    db.session.execute(text(f"ALTER TABLE diagnoses ADD COLUMN {col} {col_type}"))
                    db.session.commit()
                    print(f"Column '{col}' successfully added.")
                except Exception as e:
                    db.session.rollback()
                    print(f"Error adding column '{col}': {e}")
            else:
                print(f"Column '{col}' already exists.")
                
    print("Database check and update completed!")

if __name__ == '__main__':
    update_database()
