import socket
import requests
import os
import threading
import time
import sys
from flask import Flask

# --- INTERFACE WEB ---
app = Flask(__name__)

@app.route('/')
def home():
    return "embracetime AI está online! 🚀"

def run_web():
    # O Render usa a porta 10000 por defeito
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- CONFIGURAÇÕES ---
HF_TOKEN = os.getenv("HF_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"

SERVIDORES = ["irc.ptnet.org", "portugal.ptnet.org", "lisbon.ptnet.org"]
PORTAS = [6667, 6660, 7000]
NICK_FIXO = "embracetime"
PASS_IRC = "Nasomet112#"
CHANNEL = "#TheOG"

def log_event(msg):
    """Força o log a aparecer imediatamente no Render"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)
    sys.stdout.flush()

def ask_ai(message, author):
    if not HF_TOKEN:
        return "Falta o HF_TOKEN nas definições do Render! 😅"
    
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    prompt = (f"Tu és o {NICK_FIXO}, uma IA jovem e descontraída no IRC da PTNet. "
              f"Responde sempre em PT-PT de forma curta e jovial. "
              f"O {author} disse: {message}\nResposta:")
    
    try:
        payload = {"inputs": prompt, "parameters": {"max_new_tokens": 60, "temperature": 0.8}}
        r = requests.post(API_URL, headers=headers, json=payload, timeout=10)
        res = r.json()[0]['generated_text'].split("Resposta:")[-1].strip()
        return res if res else "Tive um branco... 😎"
    except:
        return "O meu cérebro fritou... tenta de novo! 🤖"

def run_irc():
    srv_idx = 0
    while True:
        server = SERVIDORES[srv_idx % len(SERVIDORES)]
        port = PORTAS[srv_idx % len(PORTAS)]
        
        try:
            log_event(f"INICIANDO: A tentar {server}:{port}...")
            irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            irc.settimeout(20)
            irc.connect((server, port))

            irc.send(f"NICK {NICK_FIXO}\r\n".encode('utf-8'))
            irc.send(f"USER {NICK_FIXO} 8 * :IA {NICK_FIXO} jovial\r\n".encode('utf-8'))

            irc.settimeout(None)
            while True:
                buffer = irc.recv(4096).decode("utf-8", errors="ignore")
                if not buffer: break
                
                for line in buffer.split("\r\n"):
                    if not line: continue
                    
                    # Log de tudo o que o servidor envia (DEBUG)
                    if "PING" not in line: # Não encher o log com PINGs
                        log_event(f"IRC: {line}")

                    if line.startswith("PING"):
                        irc.send(f"PONG {line.split()[1]}\r\n".encode('utf-8'))
                    
                    # Ao ligar com sucesso
                    if " 001 " in line:
                        log_event("!!! LIGADO !!! A identificar no NickServ...")
                        irc.send(f"PRIVMSG NickServ :IDENTIFY {PASS_IRC}\r\n".encode('utf-8'))
                        time.sleep(5) 
                        irc.send(f"JOIN {CHANNEL}\r\n".encode('utf-8'))
                        log_event(f"Tentei entrar no canal {CHANNEL}")

                    # Capturar mensagens do Canal
                    if " PRIVMSG " in line:
                        user = line.split('!')[0][1:]
                        if " :" in line:
                            msg_content = line.split(" :", 1)[1]
                            log_event(f"CHAT [{user}]: {msg_content}")
                            
                            if NICK_FIXO.lower() in msg_content.lower():
                                resposta = ask_ai(msg_content, user)
                                irc.send(f"PRIVMSG {CHANNEL} :{user}: {resposta}\r\n".encode('utf-8'))
                                log_event(f"RESPOSTA: {resposta}")
                            
        except Exception as e:
            log_event(f"ERRO: {e}. A saltar de servidor em 20s...")
            srv_idx += 1
            time.sleep(20)

if __name__ == "__main__":
    # Inicia a thread Web
    t = threading.Thread(target=run_web, daemon=True)
    t.start()
    # Inicia o IRC
    run_irc()
