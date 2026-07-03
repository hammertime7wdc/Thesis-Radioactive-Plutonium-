import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_supabase_client: Client = None

def get_supabase_client() -> Client:
    """
    Get or create the Supabase client singleton.
    Initialize with SUPABASE_URL and SUPABASE_ANON_KEY from environment variables.
    """
    global _supabase_client
    
    if _supabase_client is None:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_anon_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables. "
                "Please check your .env file."
            )
        
        _supabase_client = create_client(supabase_url, supabase_anon_key)
    
    return _supabase_client


def get_supabase_service_client() -> Client:
    """
    Get a Supabase client with service role key for admin operations.
    Use with caution - this bypasses RLS policies.
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_service_key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment variables."
        )
    
    return create_client(supabase_url, supabase_service_key)
