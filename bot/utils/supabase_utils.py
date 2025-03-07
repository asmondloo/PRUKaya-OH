import json
from supabase import create_client
from bot.config import SUPABASE_URL, SUPABASE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

categories_response = supabase.table("insurance_categories").select("*").execute()
insurance_categories = categories_response.data

products_response = supabase.table("insurance_products").select("*").execute()
insurance_products = products_response.data

provider_response = supabase.table("insurance_providers").select("*").execute()
insurance_providers = provider_response.data


financial_categories = supabase.table("financial_products_category").select("*").execute().data
financial_products = supabase.table("financial_products").select("*").execute().data
banks = supabase.table("banks").select("*").execute().data

all_users = supabase.table("telegram_users").select("*").execute().data


agents = supabase.table("agent").select("*").execute().data


def getAgentPicture(picURL):
    return supabase.storage.from_('FA').get_public_url(picURL)


def add_user_todb(username):
    res = supabase.table("telegram_users").insert([{"user_id": username}]).execute()
    
    
