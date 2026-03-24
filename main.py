import socket
import requests
import os
import threading
import time
from flask import Flask

# --- INTERFACE WEB (Para manter o Render ativo) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "embracetime AI está online! 🚀"

def run_web():
    # O Render usa a porta da variável de ambiente PORT
    port = int(os.environ.get("PORT", 7860))
    app.run(host='0.0.0.0', port=port)

# --- CONFIGURAÇÕES DO BOT ---
HF_TOKEN = os.getenv("HF_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"

# SERVIDORES DA PTNET
SERVIDORES = ["irc.ptnet.org", "portugal.ptnet.org", "lisbon.ptnet.org"]
PORTAS = [6667, 6660, 7000]
NICK_FIXO = "embracetime" # Nick em minúsculas como solicitado [cite: 21]
CHANNEL = "#TheOG" # Canal definido [cite: 22]

def ask_ai(message, author):
    if not HF_TOKEN:
        return "Puto, falta o meu HF_TOKEN nas definições! 😅"
    
    headers = {"Authorization": f"Bearer {HF_TOKEN}"} [cite: 24]
    # Prompt jovial em PT-PT
    prompt = (f"Tu és o {NICK_FIXO}, uma IA muito jovem e descontraída que adora o IRC da PTNet. "
              f"Responde sempre em Português de Portugal (PT-PT) de forma fixe e curta. "
              f"O utilizador {author} disse: {message}\n"
              f"Resposta do {NICK_FIXO}:") [cite: 25]
    
    try:
        payload = {
            "inputs": prompt, 
            "parameters": {
                "max_new_tokens": 60,
                "temperature": 0.8
            }
        }
        r = requests.post(API_URL, headers=headers, json=payload, timeout=10) [cite: 27]
        full_text = r.json()[0]['generated_text']
        # Isolar a resposta da IA
        res = full_text.split(f"Resposta do {NICK_FIXO}:")[-1].strip() [cite: 28]
        return res if res else "Ya, não sei o que dizer a isso! 😎"
    except:
        return "O meu sistema está a dar um nó, tenta outra vez! 🤖" [cite: 30]

def run_irc():
    srv_idx = 0
    while True: [cite: 33]
        server = SERVIDORES[srv_idx % len(SERVIDORES)] [cite: 34]
        port = PORTAS[srv_idx % len(PORTAS)] [cite: 35]
        
        try:
            print(f"\n>>> A ligar à PTNet: {server}:{port} com o nick {NICK_FIXO}") [cite: 38]
            irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM) [cite: 39]
            irc.settimeout(20) [cite: 40]
            irc.connect((server, port)) [cite: 41]

            # Login no IRC
            irc.send(f"NICK {NICK_FIXO}\r\n".encode('utf-8')) [cite: 42]
            irc.send(f"USER {NICK_FIXO} 8 * :IA embracetime jovial\r\n".encode('utf-8')) [cite: 43]

            irc.settimeout(None) [cite: 44]
            while True: [cite: 45]
                buffer = irc.recv(4096).decode("utf-8", errors="ignore") [cite: 46]
                if not buffer: break [cite: 47]
                
                for line in buffer.split("\r\n"):
                    if not line: continue
                    
                    # Manter a ligação viva
                    if line.startswith("PING"): [cite: 48]
                        irc.send(f"PONG {line.split()[1]}\r\n".encode('utf-8')) [cite: 49]
                    
                    # Entrar no canal após estar ligado
                    if " 001 " in line or " 376 " in line: [cite: 50]
                        print(f"!!! Ligado como {NICK_FIXO} !!!") [cite: 51]
                        irc.send(f"JOIN {CHANNEL}\r\n".encode('utf-8')) [cite: 52]

                    # Responder a mensagens que mencionem o bot
                    if " PRIVMSG " in line: [cite: 53]
                        user = line.split('!')[0][1:] [cite: 54]
                        msg_content = line.split(" :", 1)[1] [cite: 55]
                        
                        if NICK_FIXO.lower() in msg_content.lower(): [cite: 56]
                            print(f"Mensagem de {user}: {msg_content}")
                            resposta = ask_ai(msg_content, user) [cite: 57]
                            irc.send(f"PRIVMSG {CHANNEL} :{user}: {resposta}\r\n".encode('utf-8')) [cite: 58]
                            
        except Exception as e:
            print(f"Erro: {e}. A tentar outro servidor em 20 segundos...") [cite: 60]
            srv_idx += 1 [cite: 61]
            time.sleep(20) [cite: 62]

if __name__ == "__main__":
    # Thread para a Web App (Flask)
    threading.Thread(target=run_web, daemon=True).start() [cite: 64]
    # Loop do IRC
    run_irc() [cite: 65]
