import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def criar_tabela_se_nao_existir():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS cifras (
                        id SERIAL PRIMARY KEY,
                        titulo TEXT,
                        autor TEXT,
                        cifra TEXT,
                        data_insercao TIMESTAMP DEFAULT NOW()
                    )
                """)
                conn.commit()
        print("✅ Tabela 'cifras' verificada/criada com sucesso.")
    except Exception as e:
        print("❌ Erro ao criar/verificar tabela:", e)

def salvar_cifra(titulo, autor, cifra):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO cifras (titulo, autor, cifra) VALUES (%s, %s, %s)",
                    (titulo, autor, cifra)
                )
                conn.commit()
    except Exception as e:
        print("❌ Erro ao salvar cifra no banco:", e)

def listar_cifras():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, titulo, autor FROM cifras ORDER BY id DESC")
                return cur.fetchall()
    except Exception as e:
        print("❌ Erro ao listar cifras:", e)
        return []
    


def buscar_cifra_por_titulo(titulo):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, titulo, autor, cifra FROM cifras WHERE titulo = %s", (titulo,))
                row = cur.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "titulo": row[1],
                        "autor": row[2],
                        "cifra": row[3]
                    }
    except Exception as e:
        print("❌ Erro ao buscar cifra por título:", e)
    return None


def buscar_cifra_por_id(id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, titulo, autor, cifra FROM cifras WHERE id = %s", (id,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            return row  # retorna como tupla (id, titulo, autor, cifra)
        return None
    except Exception as e:
        print("❌ Erro ao buscar cifra por ID:", e)
        return None




def criar_tabelas_usuario_e_musica():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Tabela de usuários
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS usuarios (
                        id SERIAL PRIMARY KEY,
                        email TEXT UNIQUE NOT NULL,
                        senha_hash TEXT NOT NULL
                    );
                """)

                # Tabela de músicas com vínculo ao usuário
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS musicas (
                        id SERIAL PRIMARY KEY,
                        usuario_id INTEGER REFERENCES usuarios(id),
                        titulo TEXT NOT NULL,
                        autor TEXT,
                        conteudo JSONB NOT NULL,
                        data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                conn.commit()
        print("✅ Tabelas 'usuarios' e 'musicas' criadas/verificadas com sucesso.")
    except Exception as e:
        print("❌ Erro ao criar/verificar tabelas de usuário e música:", e)
