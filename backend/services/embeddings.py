from sentence_transformers import SentenceTransformer
import sqlite_vec

from database.db import DBManager


model = SentenceTransformer("all-MiniLM-L6-v2")


def generate_embeddings(text: str) -> list[float]:
    embedding = model.encode(text)
    return embedding.tolist()


def test_sqlite_vec():                                                                                                                                                                                                 
    db = DBManager()                                                                                                                                                                                                   
    conn = db.connect()                                                                                                                                                                                                
    conn.enable_load_extension(True)                                                                                                                                                                                   
    sqlite_vec.load(conn)                                                                                                                                                                                              
                                                                                                                                                                                                                        
    version = conn.execute("select vec_version()").fetchone()                                                                                                                                                          
    print(version[0])                                                                                                                                                                                                     
                                                                                                                                                                                                                        
    conn.close()  
