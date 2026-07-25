import uuid
from backend.db import get_db
from backend.services.auth_service import hash_password

def seed_data():
    user_id = "user-12345"
    caregiver_id = "caregiver-12345"
    
    password_hash = hash_password(" ")
    
    with get_db() as conn:
        # Clear existing data to avoid conflicts
        conn.execute("DELETE FROM credentials")
        conn.execute("DELETE FROM users")
        conn.execute("DELETE FROM logs")
        conn.execute("DELETE FROM emergencies")
        
        # Insert User Credentials
        conn.execute(
            "INSERT INTO credentials (id, email, hashed_password, role) VALUES (?, ?, ?, ?)",
            [user_id, "user@recover.com", password_hash, "user"]
        )
        # Insert User Profile
        conn.execute(
            "INSERT INTO users (id, name, substance_history, triggers, support_network) VALUES (?, ?, ?, ?, ?)",
            [user_id, "Sam", "Alcohol", "Stress, Isolation", "Alex (Caregiver)"]
        )
        
        # Insert Caregiver Credentials
        conn.execute(
            "INSERT INTO credentials (id, email, hashed_password, role) VALUES (?, ?, ?, ?)",
            [caregiver_id, "caregiver@recover.com", password_hash, "caregiver"]
        )
        # Insert Caregiver Profile
        conn.execute(
            "INSERT INTO users (id, name) VALUES (?, ?)",
            [caregiver_id, "Alex"]
        )
        
        print("Database successfully seeded with demo accounts!")

if __name__ == "__main__":
    seed_data()
