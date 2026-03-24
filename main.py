import socket
import requests
import os
import threading
import time
from flask import Flask

# --- INTERFACE WEB ---
app = Flask(__name__)

@app.route('/')
def home():
    return "embracetime AI está online! 🚀"

def run_web():
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
    """Função para imprimir logs bonitos no painel do Render"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")

def ask_ai(message, author):
    if not HF_TOKEN:
        return "Falta o HF_TOKEN no Render! 😅"
    
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    prompt = (f"Tu és o {NICK_FIXO}, uma IA jovem e descontraída no IRC da PTNet. "
              f"Responde em PT-PT de forma curta e jovial. "
              f"O {author} disse: {message}\nResposta:")
    
    try:
        payload = {"inputs": prompt, "parameters": {"max_new_tokens": 60, "temperature": 0.8}}
        r = requests.post(API_URL, headers=headers, json=payload, timeout=10)
        res = r.json()[0]['generated_text'].split("Resposta:")[-1].strip()
        return res if res else "Tive um branco agora! 😂"
    except:
        return "O meu cérebro de silício fritou um bocadinho... 🤖"

def run_irc():
    srv_idx = 0
    while True:
        server = SERVIDORES[srv_idx % len(SERVIDORES)]
        port = PORTAS[srv_idx % len(PORTAS)]
        
        try:
            log_event(f"A tentar ligar a {server}:{port}...")
            irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            irc.settimeout(20)
            irc.connect((server, port))

            irc.send(f"NICK {NICK_FIXO}\r\n".encode('utf-8'))
            irc.send(f"USER {NICK_FIXO} 8 * :IA embracetime\r\n".encode('utf-8'))

            irc.settimeout(None)
            while True:
                buffer = irc.recv(4096).decode("utf-8", errors="ignore")
                if not buffer: break
                
                for line in buffer.split("\r\n"):
                    if not line: continue
                    
                    # Manter vivo
                    if line.startswith("PING"):
                        irc.send(f"PONG {line.split()[1]}\r\n".encode('utf-8'))
                    
                    # Identificar no NickServ ao ligar (001 é o sinal de sucesso)
                    if " 001 " in line:
                        log_event(f"!!! Ligado como {NICK_FIXO}. A identificar... !!!")
                        irc.send(f"PRIVMSG NickServ :IDENTIFY {PASS_IRC}\r\n".encode('utf-8'))
                        time.sleep(2) # Esperar um pouco para a autenticação processar
                        irc.send(f"JOIN {CHANNEL}\r\n".encode('utf-8'))
                        log_event(f"Comando JOIN enviado para {CHANNEL}")

                    # Logs de Conversas e Interações
                    if " PRIVMSG " in line:
                        parts = line.split("!")
                        user = parts[0][1:]
                        msg_content = line.split(" :", 1)[1]
                        
                        # LOG DA CONVERSA (Verás isto no Render)
                        log_event(f"CHAT [{user}]: {msg_content}")
                        
                        # Resposta da IA
                        if NICK_FIXO.lower() in msg_content.lower():
                            resposta = ask_ai(msg_content, user)
                            irc.send(f"PRIVMSG {CHANNEL} :{user}: {resposta}\r\n".encode('utf-8'))
                            log_event(f"RESPOSTA [embracetime]: {resposta}")
                            
        except Exception as e:
            log_event(f"Erro: {e}. A saltar de servidor em 20s...")
            srv_idx += 1
            time.sleep(20)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    run_irc()
