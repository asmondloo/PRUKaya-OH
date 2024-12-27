import json
from supabase import create_client
from bot.config import SUPABASE_URL, SUPABASE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

categories_response = supabase.table("insurance_categories").select("*").execute()
insurance_categories = categories_response.data

products_response = supabase.table("insurance_products").select("*").execute()
insurance_products = products_response.data


agents = supabase.table("agent").select("*").execute().data


def getAgentPicture(picURL):
    return supabase.storage.from_('FA').get_public_url(picURL)
