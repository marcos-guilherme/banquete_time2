import dotenv
import os
from supabase import create_client, Client
dotenv.load_dotenv()

url = os.getenv('SUPABASE_URL')
key = os.getenv('SERVICE_KEY_SUPABASE')
supabase = create_client(url, key)

TABLE = "tabela_embeddings_grupo_02_04"
FUNC_NAME = "match_procedimentos"


supabase: Client = create_client(url, key)

query_embedding =   "procedimento de cirurgia"
match_count = 10

# Chamada à função via RPC
response = supabase.rpc('match_procedimentos', {
    'query_embedding': query_embedding,
    'match_count': match_count
}).execute()

