import jwt
import bcrypt
import uuid
import os
import string
import random
from datetime import datetime, timezone, timedelta
from fastapi import Request, HTTPException
from database import get_db

JWT_SECRET = os.environ.get('JWT_SECRET', 'garment_erp_jwt_secret_2025')

def generate_password(length=10):
    chars = 'ABCDEFGHJKMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789@#!'
    return ''.join(random.choice(chars) for _ in range(length))

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(10)).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_data: dict) -> str:
    payload = {
        'id': user_data['id'],
        'email': user_data['email'],
        'role': user_data['role'],
        'name': user_data['name'],
        'vendor_id': user_data.get('vendor_id'),
        'buyer_id': user_data.get('buyer_id'),
        'customer_name': user_data.get('customer_name', user_data.get('buyer_company', '')),
        'exp': datetime.now(timezone.utc) + timedelta(hours=24)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def verify_token(request: Request):
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    try:
        token = auth_header.split(' ')[1]
        return jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
    except Exception:
        return None

def require_auth(request: Request):
    user = verify_token(request)
    if not user:
        raise HTTPException(status_code=401, detail='Unauthorized')
    return user

def check_role(user: dict, allowed_roles: list) -> bool:
    if user.get('role') == 'superadmin':
        return True
    return user.get('role') in allowed_roles

async def log_activity(user_id, user_name, action, module, details=''):
    db = get_db()
    await db.activity_logs.insert_one({
        'id': str(uuid.uuid4()),
        'user_id': user_id,
        'user_name': user_name,
        'action': action,
        'module': module,
        'details': details,
        'timestamp': datetime.now(timezone.utc)
    })

async def seed_initial_data():
    db = get_db()
    # Check for old schema migration
    first_product = await db.products.find_one({})
    if first_product and first_product.get('selling_price') is None and first_product.get('product_name'):
        collections_to_clear = ['products', 'garments', 'production_pos', 'po_items',
            'work_orders', 'production_progress', 'invoices', 'payments',
            'product_variants', 'vendor_shipments', 'vendor_shipment_items',
            'buyer_shipments', 'buyer_shipment_items']
        for col in collections_to_clear:
            await db[col].delete_many({})
        print('Migration v2: cleared old schema data')
    
    # Ensure superadmin
    admin = await db.users.find_one({'email': 'admin@garment.com'})
    if not admin:
        hashed = hash_password('Admin@123')
        await db.users.insert_one({
            'id': str(uuid.uuid4()),
            'name': 'Super Admin',
            'email': 'admin@garment.com',
            'password': hashed,
            'role': 'superadmin',
            'status': 'active',
            'created_at': datetime.now(timezone.utc),
            'updated_at': datetime.now(timezone.utc)
        })
        print('Superadmin seeded: admin@garment.com / Admin@123')

def serialize_doc(doc):
    """Convert MongoDB document to JSON-serializable dict"""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(d) for d in doc]
    if isinstance(doc, dict):
        result = {}
        for k, v in doc.items():
            if k == '_id':
                continue
            result[k] = serialize_doc(v)
        return result
    if isinstance(doc, datetime):
        return doc.isoformat()
    return doc
