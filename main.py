"""
Pipeline: Áudio -> Whisper (transcrição) -> Ollama (pontos-chave)
Melhorias opcionais: descrição de imagem (modelo multimodal) e saída em áudio (TTS).

Uso rápido:
    python main.py audio audio.mp3
    python main.py imagem foto.jpg
    python main.py audio audio.mp3 --falar
"""
import argparse
import os
import sys

import ollama
import whisper

EXTENSOES_AUDIO = (".wav", ".mp3")
EXTENSOES_IMAGEM = (".jpg", ".jpeg", ".png")
PASTA_AUDIOS = "coloque_audio_aqui"  # pasta de onde os áudios são lidos
PASTA_IMAGENS = "coloque_imagem_aqui"  # pasta de onde as imagens são lidas
NUM_CTX = 8192  # janela de contexto (tokens) do LLM; o padrão do Ollama é 4096
PASTA_SAIDAS = "Transcrições (saídas)"  # onde textos e áudios gerados são salvos
MODELO_TEXTO = "llama3.2"          # LLM para o resumo
MODELO_VISAO = "llava"             # modelo multimodal para imagens


# ---------------------------------------------------------------- Validação
def validar_arquivo(caminho: str, extensoes: tuple) -> None:
    """Confere se o arquivo existe e tem uma extensão aceita."""
    if not os.path.isfile(caminho):
        sys.exit(f"Erro: arquivo não encontrado: {caminho}")
    if not caminho.lower().endswith(extensoes):
        sys.exit(f"Erro: formato inválido. Use: {', '.join(extensoes)}")


# ------------------------------------------------- Passo 1: Whisper (STT)
def transcrever_audio(caminho_audio: str, modelo_whisper: str = "base") -> str:
    """Transcreve o áudio para texto usando o Whisper (requer ffmpeg)."""
    print(f"[1/2] Carregando Whisper '{modelo_whisper}' e transcrevendo...")
    modelo = whisper.load_model(modelo_whisper)
    # language="pt" evita erro de detecção; fp16=False remove warning em CPU
    resultado = modelo.transcribe(caminho_audio, language="pt", fp16=False)
    return resultado["text"].strip()


# ------------------------------------------- Passo 2: Ollama (pontos-chave)
def montar_prompt_pontos_chave(texto: str) -> str:
    """Cria o prompt (template) que instrui o LLM a extrair pontos-chave."""
    return (
        "Você é um assistente que resume textos. Com base SOMENTE na "
        "transcrição abaixo, escreva em português do Brasil um resumo curto "
        "seguido de uma lista de pontos-chave em tópicos (bullets).\n\n"
        f"Transcrição:\n\"\"\"\n{texto}\n\"\"\""
    )


def extrair_pontos_chave(texto: str, modelo: str = MODELO_TEXTO) -> str:
    """Envia o texto transcrito ao Ollama e retorna o resumo com pontos-chave."""
    print(f"[2/2] Gerando pontos-chave com Ollama ({modelo})...")
    try:
        resposta = ollama.chat(
            model=modelo,
            messages=[{"role": "user", "content": montar_prompt_pontos_chave(texto)}],
            options={"num_ctx": NUM_CTX},
        )
    except Exception as erro:  # Ollama fora do ar ou modelo não baixado
        sys.exit(f"Erro ao chamar o Ollama: {erro}\n"
                 f"Verifique se ele está rodando e se executou: ollama pull {modelo}")
    return resposta["message"]["content"].strip()


# ------------------------------------------ Melhoria 1: descrever imagem
def descrever_imagem(caminho_imagem: str, modelo: str = MODELO_VISAO) -> str:
    """Envia uma imagem a um modelo multimodal do Ollama e retorna a descrição."""
    print(f"Descrevendo imagem com {modelo}...")
    try:
        resposta = ollama.chat(
            model=modelo,
            messages=[{
                "role": "user",
                "content": "Descreva esta imagem em detalhes, em português do Brasil.",
                "images": [caminho_imagem],
            }],
        )
    except Exception as erro:
        sys.exit(f"Erro ao chamar o Ollama: {erro}\n"
                 f"Verifique se executou: ollama pull {modelo}")
    return resposta["message"]["content"].strip()


# ------------------------------------------- Melhoria 2: saída em áudio
def falar_texto(texto: str, arquivo_saida: str = "saida.mp3") -> None:
    """Converte o texto em fala (gTTS, requer internet) e salva em um .mp3."""
    from gtts import gTTS  # import local: só é necessário se usar --falar
    os.makedirs(os.path.dirname(arquivo_saida) or ".", exist_ok=True)
    print(f"Gerando áudio em '{arquivo_saida}'...")
    gTTS(text=texto, lang="pt-br").save(arquivo_saida)
    print("Áudio salvo. Abra o arquivo para ouvir.")


# ------------------------------------------------------------- Utilitários
def salvar_texto(texto: str, caminho: str) -> None:
    """Salva um texto em arquivo UTF-8 (cria a pasta de destino se preciso)."""
    os.makedirs(os.path.dirname(caminho) or ".", exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(texto)


# -------------------------------------------------------------- Fluxos CLI
def listar_arquivos(pasta: str, extensoes: tuple) -> list:
    """Lista os arquivos com as extensões dadas em uma pasta (cria se não existir)."""
    if not os.path.isdir(pasta):
        os.makedirs(pasta)
        sys.exit(f"Pasta '{pasta}' criada. Coloque seus arquivos nela e rode de novo.")
    arquivos = sorted(
        os.path.join(pasta, nome) for nome in os.listdir(pasta)
        if nome.lower().endswith(extensoes)
    )
    if not arquivos:
        sys.exit(f"Nenhum arquivo {extensoes} encontrado em '{pasta}'.")
    return arquivos


def listar_audios(pasta: str = PASTA_AUDIOS) -> list:
    """Lista os .wav/.mp3 da pasta de áudios."""
    return listar_arquivos(pasta, EXTENSOES_AUDIO)


def listar_imagens(pasta: str = PASTA_IMAGENS) -> list:
    """Lista os .jpg/.jpeg/.png da pasta de imagens."""
    return listar_arquivos(pasta, EXTENSOES_IMAGEM)


def processar_audio(caminho: str, args) -> None:
    """Pipeline de um áudio: valida -> transcreve -> resume -> (opcional) fala."""
    validar_arquivo(caminho, EXTENSOES_AUDIO)
    nome = os.path.splitext(os.path.basename(caminho))[0]
    print(f"\n##### {os.path.basename(caminho)} #####")

    transcricao = transcrever_audio(caminho, args.whisper)
    print("\n=== TRANSCRIÇÃO ===\n" + transcricao)
    salvar_texto(transcricao, os.path.join(PASTA_SAIDAS, f"transcricao_{nome}.txt"))

    pontos = extrair_pontos_chave(transcricao, args.modelo)
    print("\n=== PONTOS-CHAVE ===\n" + pontos)
    salvar_texto(pontos, os.path.join(PASTA_SAIDAS, f"pontos_chave_{nome}.txt"))

    if args.falar:
        falar_texto(pontos, os.path.join(PASTA_SAIDAS, f"saida_{nome}.mp3"))


def fluxo_audio(args) -> None:
    """Processa o arquivo informado ou, sem argumento, todos da pasta de áudios."""
    arquivos = [args.arquivo] if args.arquivo else listar_audios()
    print(f"{len(arquivos)} áudio(s) a processar.")
    for caminho in arquivos:
        processar_audio(caminho, args)


def fluxo_imagem(args) -> None:
    """Descreve o arquivo informado ou, sem argumento, todas as imagens da pasta."""
    arquivos = [args.arquivo] if args.arquivo else listar_imagens()
    print(f"{len(arquivos)} imagem(ns) a processar.")
    for caminho in arquivos:
        validar_arquivo(caminho, EXTENSOES_IMAGEM)
        nome = os.path.splitext(os.path.basename(caminho))[0]
        print(f"\n##### {os.path.basename(caminho)} #####")
        descricao = descrever_imagem(caminho)
        print("\n=== DESCRIÇÃO ===\n" + descricao)
        salvar_texto(descricao, os.path.join(PASTA_SAIDAS, f"descricao_{nome}.txt"))
        if args.falar:
            falar_texto(descricao, os.path.join(PASTA_SAIDAS, f"saida_{nome}.mp3"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Whisper + Ollama")
    sub = parser.add_subparsers(dest="comando", required=True)

    p_audio = sub.add_parser("audio", help="Transcreve áudio e extrai pontos-chave")
    p_audio.add_argument("arquivo", nargs="?", default=None,
                         help=f"Arquivo .wav/.mp3 (opcional; sem ele, usa a pasta '{PASTA_AUDIOS}')")
    p_audio.add_argument("--whisper", default="base",
                         help="Modelo Whisper: tiny, base, small, medium, large")
    p_audio.add_argument("--modelo", default=MODELO_TEXTO, help="Modelo do Ollama")
    p_audio.add_argument("--falar", action="store_true", help="Gera saida.mp3")
    p_audio.set_defaults(func=fluxo_audio)

    p_img = sub.add_parser("imagem", help="Descreve uma imagem")
    p_img.add_argument("arquivo", nargs="?", default=None,
                       help=f"Arquivo de imagem (opcional; sem ele, usa a pasta '{PASTA_IMAGENS}')")
    p_img.add_argument("--falar", action="store_true", help="Gera saida.mp3")
    p_img.set_defaults(func=fluxo_imagem)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
