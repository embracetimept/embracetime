import socket
import requests
import os
import threading
import time
from flask import Flask

# --- INTERFACE WEB (Obrigatória para o Render) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "embracetime AI está online! 🚀"

def run_web():
    # O Render define a porta automaticamente
    port = int(os.environ.get("PORT", 7860))
    app.run(host='0.0.0.0', port=port)

# --- CONFIGURAÇÕES DO BOT ---
HF_TOKEN = os.getenv("HF_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"

SERVIDORES = ["irc.ptnet.org", "portugal.ptnet.org", "lisbon.ptnet.org"]
PORTAS = [6667, 6660, 7000]
NICK_FIXO = "embracetime"
CHANNEL = "#TheOG"

def ask_ai(message, author):
    if not HF_TOKEN:
        return "Falta o HF_TOKEN nas definições do Render! 😅"
    
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    prompt = (f"Tu és o {NICK_FIXO}, uma IA muito jovem e descontraída no IRC da PTNet. "
              f"Responde sempre em Português de Portugal (PT-PT) de forma fixe e curta. "
              f"O utilizador {author} disse: {message}\n"
              f"Resposta do {NICK_FIXO}:")
    
    try:
        payload = {
            "inputs": prompt, 
            "parameters": {"max_new_tokens": 60, "temperature": 0.8}
        }
        r = requests.post(API_URL, headers=headers, json=payload, timeout=10)
        full_text = r.json()[0]['generated_text']
        res = full_text.split(f"Resposta do {NICK_FIXO}:")[-1].strip()
        return res if res else "Ya, não sei o que dizer a isso! 😎"
    except:
        return "O meu cérebro de silício fritou, tenta de novo! 🤖"

def run_irc():
    srv_idx = 0
    while True:
        server = SERVIDORES[srv_idx % len(SERVIDORES)]
        port = PORTAS[srv_idx % len(PORTAS)]
        
        try:
            print(f"\n>>> A ligar à PTNet: {server}:{port} com o nick {NICK_FIXO}")
            irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            irc.settimeout(20)
            irc.connect((server, port))

            irc.send(f"NICK {NICK_FIXO}\r\n".encode('utf-8'))
            irc.send(f"USER {NICK_FIXO} 8 * :IA embracetime jovial\r\n".encode('utf-8'))

            irc.settimeout(None)
            while True:
                buffer = irc.recv(4096).decode("utf-8", errors="ignore")
                if not buffer: break
                
                for line in buffer.split("\r\n"):
                    if not line: continue
                    if line.startswith("PING"):
                        irc.send(f"PONG {line.split()[1]}\r\n".encode('utf-8'))
                    
                    if " 001 " in line or " 376 " in line:
                        print(f"!!! Ligado como {NICK_FIXO} !!!")
                        irc.send(f"JOIN {CHANNEL}\r\n".encode('utf-8'))

                    if " PRIVMSG " in line:
                        user = line.split('!')[0][1:]
                        if " :" in line:
                            msg_content = line.split(" :", 1)[1]
                            
                            if NICK_FIXO.lower() in msg_content.lower():
                                resposta = ask_ai(msg_content, user)
                                irc.send(f"PRIVMSG {CHANNEL} :{user}: {resposta}\r\n".encode('utf-8'))
                            
        except Exception as e:
            print(f"Erro: {e}. A tentar de novo em 20s...")
            srv_idx += 1
            time.sleep(20)

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    run_irc()
