import os
import sys
from app import create_app
from extensions import db
from models import User
from flask_jwt_extended import create_access_token
from io import BytesIO

app = create_app()

def run_test():
    print("Starting prediction pipeline test...")
    with app.app_context():
        # Get or create admin user
        user = User.query.filter_by(email='admin@dermdetect.com').first()
        if not user:
            print("Admin user not found. Creating a temporary test user...")
            from extensions import bcrypt
            hashed = bcrypt.generate_password_hash('admin123').decode('utf-8')
            user = User(nama='Administrator', email='admin@dermdetect.com', password=hashed, role='admin')
            db.session.add(user)
            db.session.commit()

        # Generate JWT token
        token = create_access_token(
            identity=str(user.id),
            additional_claims={
                'email': user.email,
                'role' : user.role,
            }
        )

        client = app.test_client()
        
        # Prepare a mock image file
        mock_image = BytesIO(b"dummy image data")
        
        # Test symptoms data (all 13 symptoms)
        data = {
            'foto': (mock_image, 'test.jpg'),
            'durasi_demam': '3',
            'demam_tinggi': '1',
            'batuk': '1',
            'pilek': '0',
            'sakit_tenggorokan': '1',
            'mata_merah': '1',
            'koplik_spot': '0',
            'kelenjar_bengkak': '0',
            'pola_ruam': '1',
            'nyeri_sendi': '0',
            'vesikel': '0',
            'hilang_nafsu_makan': '1',
            'lemas': '1'
        }
        
        print("Sending prediction request to /api/diagnose/predict...")
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        # Mock preprocess_image to return dummy array since "dummy image data" is not a valid JPEG
        import routes.diagnose as diagnose_route
        old_preprocess = diagnose_route.preprocess_image
        import numpy as np
        diagnose_route.preprocess_image = lambda filepath: np.random.rand(1, 224, 224, 3).astype('float32')
        
        try:
            response = client.post(
                '/api/diagnose/predict',
                data=data,
                headers=headers,
                content_type='multipart/form-data'
            )
            
            print(f"Status Code: {response.status_code}")
            res_json = response.get_json()
            print(f"Response: {res_json}")
            
            if response.status_code == 200 and res_json.get('success'):
                print("✅ Test passed! Prediction pipeline is working perfectly with 13 symptoms.")
            else:
                print("❌ Test failed!")
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
        finally:
            diagnose_route.preprocess_image = old_preprocess

if __name__ == '__main__':
    run_test()
