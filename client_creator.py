from dotenv import load_dotenv
load_dotenv()

import os

from supabase import create_client
url=os.environ.get("SUPABASE_URL")
key=os.environ.get("SUPABASE_SERVICE_KEY")

client=create_client(url,key)

if client:
    print ("client created successfully")
else:
    print ("client not created")