from openai import OpenAI, APIError, APIConnectionError, RateLimitError
import os
import json

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def formatar_com_gpt(texto: str) -> dict:
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você é um assistente que transforma letras de músicas gospel em JSON. Se não for uma música gospel, responda educadamente que só processa músicas do gênero gospel/cristão. "
                        "Não inclua tablaturas, nem explicações, nem formatação extra. "
                        "A resposta DEVE conter apenas um JSON puro com as chaves: 'titulo', 'autor' e 'cifra'.\n\n"
                        "Exemplo:\n"
                        "{\n"
                        "  \"titulo\": \"Porque Ele Vive\",\n"
                        "  \"autor\": \"Desconhecido\",\n"
                        "  \"cifra\": \"[D] Deus enviou Seu Filho a[G]mado\\n[Em] Pra me salvar e per[A]doar\\n...\"\n"
                        "}"
                    )
                },
                {"role": "user", "content": texto}
            ],
            temperature=0.3
        )

        conteudo = response.choices[0].message.content.strip()

        # Garantir que a resposta seja JSON puro (extração se houver lixo antes/depois)
        try:
            # Caso venha algo antes do JSON (ex: "Claro! Aqui está:\n{...}")
            inicio = conteudo.find('{')
            fim = conteudo.rfind('}')
            json_puro = conteudo[inicio:fim+1]

            return json.loads(json_puro)
        except json.JSONDecodeError as e:
            print("❌ Erro ao decodificar JSON retornado pela API.")
            print("Conteúdo recebido:\n", conteudo)
            print("Erro:", e)

    except APIError as e:
        print(f"❌ Erro da API OpenAI: {e}")
    except APIConnectionError as e:
        print(f"❌ Erro de conexão com a OpenAI: {e}")
    except RateLimitError as e:
        print(f"⏱️ Rate limit excedido: {e}")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

    # Retorno padrão em caso de erro
    return {"titulo": "Erro", "autor": "Desconhecido", "cifra": "Não foi possível processar o conteúdo."}
