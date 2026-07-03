"""
Supabase Database Models for Authentication
This file contains the database models and client setup for Supabase integration.
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

class SupabaseClient:
    """Singleton Supabase client for database operations"""
    
    _instance = None
    _client: Client = None
    _admin_client: Client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_client()
        return cls._instance
    
    def _initialize_client(self):
        """Initialize Supabase client from environment variables"""
        url = os.getenv("SUPABASE_URL")
        anon_key = os.getenv("SUPABASE_ANON_KEY")
        service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not url or not anon_key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env file")
        
        self._client = create_client(url, anon_key)
        
        # Admin client with service role key for privileged operations
        if service_key:
            self._admin_client = create_client(url, service_key)
        
        self._client.auth.url = url
    
    @property
    def client(self) -> Client:
        """Get the regular Supabase client instance (anon key)"""
        return self._client
    
    @property
    def admin_client(self) -> Client:
        """Get the admin Supabase client instance (service role key)"""
        return self._admin_client
    
    def get_table(self, table_name: str, use_admin: bool = False):
        """Get a reference to a Supabase table"""
        client = self._admin_client if use_admin else self._client
        return client.table(table_name)


# User model structure (for reference - actual data stored in Supabase)
class User:
    """
    User model for authentication (stored in Supabase)
    - id: UUID (Supabase auto-generated)
    - email: User's email address (unique)
    - role: User role ('admin' or 'evaluator')
    - created_at: Account creation timestamp
    """
    
    def __init__(self, id: str, email: str, role: str, created_at: str = None):
        self.id = id
        self.email = email
        self.role = role
        self.created_at = created_at
    
    def __repr__(self):
        return f"<User(email='{self.email}', role='{self.role}')>"
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create User instance from Supabase response dictionary"""
        return cls(
            id=data.get('id'),
            email=data.get('email'),
            role=data.get('role'),
            created_at=data.get('created_at')
        )


# Global Supabase client instance
supabase_client = SupabaseClient()
supabase = supabase_client.client
supabase_admin = supabase_client.admin_client
