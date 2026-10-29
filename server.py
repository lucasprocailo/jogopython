
from ursinanetworking import UrsinaNetworkingServer
import math
import random
import time


# config
HOST = "localhost"
PORTA = 25565
MAX_JOGADORES = 5
TEMPO_ESPERA = 10
COOLDOWN_ATAQUE = 3
DISTANCIA_ACERTO = 4.0
GRAVIDADE = 6
INTERVALO_ENVIO = 0.05
ESTADO_NORMAL = "normal"
ESTADO_CAIDO = "caido"
ESTADO_DIRETORIA = "diretoria"
ESTADO_ELIMINADO = "eliminado"
ultimo_envio_projeteis = None

Server = UrsinaNetworkingServer(HOST, PORTA)

#partida
estados_jogadores = {}
clientes = {}
proximo_id = 0
posicao = {}
roles = {}
dano = {}
dying = {}
projeteis = []
assassino = None
ultimoataque = None
inicio_espera = None
partida_iniciada = False
proximo_id_projet = 0
pallets = {
    0:False,
    1:False
}
tasks = {
    0:False,
    1:False,
    2:False
}
idcaidos = []
positpallet = {
    0:(30, 0.6, 30),
    1:(34, 0.6, 45)
}
def sortear_papeis():
    global assassino

    if len(clientes) < 2 or roles:
        return False

    assassino = random.choice(list(clientes.values()))

    for jogador_id in clientes.values():
        if jogador_id == assassino:
            roles[jogador_id] = "professor"
        else:
            roles[jogador_id] = "estudante"
            dano[jogador_id] = 0
            dying[jogador_id] = False
    Server.broadcast("criarmodelo", assassino)
    for conexao, jogador_id in clientes.items():
        
        conexao.send_message("papel", roles[jogador_id])

    Server.broadcast("partida", True)
    
    return True
    

@Server.event
def onClientConnected(Client):
    global proximo_id

    if len(clientes) >= MAX_JOGADORES:
        print("Servidor cheio!")
        return

    jogador_id = proximo_id
    proximo_id += 1
    clientes[Client] = jogador_id
    Client.send_message("seuid", jogador_id)

    print(f"Jogador {jogador_id} conectado.")
    print(f"Jogadores conectados: {len(clientes)}/{MAX_JOGADORES}")


@Server.event
def onClientDisconnected(Client):
    if Client not in clientes:
        return

    jogador_id = clientes.pop(Client)
    posicao.pop(jogador_id, None)
    roles.pop(jogador_id, None)
    dano.pop(jogador_id, None)
    dying.pop(jogador_id, None)
    Server.broadcast("jogador_saiu", jogador_id)
    print(f"Jogador {jogador_id} desconectado.")


@Server.event
def jogador(Client, Content):
    jogador_id = clientes.get(Client)
    if jogador_id is None or dying.get(jogador_id, False):
        return

    posicao[jogador_id] = Content
    Server.broadcast("position", posicao)   


@Server.event
def atacar(Client, Content):
    global ultimoataque, proximo_id_projet

    jogador_id = clientes.get(Client)
    if jogador_id is None:
        return
    if jogador_id != assassino or not partida_iniciada:
        return

    agora = time.time()
    if ultimoataque is not None and agora - ultimoataque < COOLDOWN_ATAQUE:
        return

    try:
        posicaoinicial, direcaoinicial, velocidade_recebida = Content
        x, y, z = posicaoinicial
        dx, dy, dz = direcaoinicial
        velocidade = float(velocidade_recebida)
    except (TypeError, ValueError):
        return

    if velocidade <= 0 or not all(math.isfinite(v) for v in (x, y, z, dx, dy, dz, velocidade)):
        return

    ultimoataque = agora
    projetil = {
        "posicao": (x, y, z),
        "direcao": (dx, dy, dz),
        "velocidade": velocidade,
        "velocidade_y": dy * velocidade,
    }
    projetil["ide"] = proximo_id_projet
    proximo_id_projet += 1
    projeteis.append(projetil)
    
@Server.event
def derrubar(Client, Content):
    
    jogador_id = clientes.get(Client)
    if jogador_id not in posicao:
        return
    if jogador_id is None or dying.get(jogador_id, True):
        return
    (x,y,z,_) = posicao[jogador_id]
    if jogador_id == assassino or not partida_iniciada:
        return
    if roles.get(jogador_id) == "estudante":
        if math.dist((x,y,z), positpallet[0]) <= 3:
            if pallets[0] == False:

                Server.broadcast("derrubada", 0)
                pallets[0] = True
            else: 
                return
        
        if math.dist((x,y,z), positpallet[1]) <= 3:
            if pallets[1] == False:
                Server.broadcast("derrubada", 1)
                pallets[1] = True
            else:
                return

@Server.event
def sendsepae(Client, Content):
    global idcaidos
    jogador_id = clientes.get(Client)
    (x,y,z,_) = posicao[jogador_id]
    if roles.get(jogador_id) == "estudante":
        return
    if roles.get(jogador_id) == "professor":
        for ide in idcaidos:
            if ide not in posicao:
                continue

            px, py, pz, _ = posicao[ide]

            if math.dist((x, y, z), (px, py, pz)) <= 4:
                estados_jogadores[ide] = ESTADO_DIRETORIA
                idcaidos.remove(ide)
                posicao[ide] = (100, 0.1, 150, 0)
                Server.broadcast("captura", ide)
                Server.broadcast("position", posicao)
@Server.event
def resgatar(Client, Content):
    jogador_id = clientes.get(Client)

    if jogador_id is None or jogador_id not in posicao:
        return

    if roles.get(jogador_id) != "estudante":
        return

    x, y, z, _ = posicao[jogador_id]
    for p, estado in estados_jogadores.items():
        if estado != ESTADO_DIRETORIA or p not in posicao:
            continue

        a, b, c, _ = posicao[p]

        if math.dist((x, y, z), (a, b, c)) <= 4:
            Server.broadcast("libertar", p)
            estados_jogadores[p] = ESTADO_NORMAL
            dying[p] = False
@Server.event
def fazertask(Client, Content):
    jogador_id = clientes.get(Client)
    if tasks[Content] == False and partida_iniciada:
        Server.broadcast("podetask", True)
    else:
        Server.broadcast("podetask", False)
ultimo_tempo = time.time()

while True:
    Server.process_net_events()

    tempo_atual = time.time()
    dt = tempo_atual - ultimo_tempo
    ultimo_tempo = tempo_atual

    for projetil in projeteis.copy():
        x, y, z = projetil["posicao"]
        dx, dy, dz = projetil["direcao"]

        velocidade_y = projetil["velocidade_y"]
        novo_y = y + velocidade_y * dt
        velocidade_y -= GRAVIDADE * dt
        projetil["velocidade_y"] = velocidade_y

        novo_x = x + dx * projetil["velocidade"] * dt
        novo_z = z + dz * projetil["velocidade"] * dt
        projetil["posicao"] = (novo_x, novo_y, novo_z)

        acertou = False
        for jogador_id, coordenadas in list(posicao.items()):
            if roles.get(jogador_id) != "estudante" or dying.get(jogador_id, False):
                continue

            playerx, playery, playerz, _ = coordenadas
            distancia = math.sqrt(
                (novo_x - playerx) ** 2
                + (novo_y - playery) ** 2
                + (novo_z - playerz) ** 2
            )

            if distancia < DISTANCIA_ACERTO:
                dano[jogador_id] = dano.get(jogador_id, 0) + 50

                if dano[jogador_id] >= 100 and not dying.get(jogador_id, False):
                    estados_jogadores[jogador_id] = ESTADO_CAIDO
                    Server.broadcast("jogador_caiu", jogador_id)
                    idcaidos.append(jogador_id)
                    dying[jogador_id] = True
                acertou = True
                break

        if acertou or novo_y <= 0:
            if projetil in projeteis:
                projeteis.remove(projetil)
    if ultimo_envio_projeteis is None:
        Server.broadcast("attprojetil", projeteis)
        ultimo_envio_projeteis = time.time()
    elif tempo_atual - ultimo_envio_projeteis >= INTERVALO_ENVIO:
        Server.broadcast("attprojetil", projeteis)
        ultimo_envio_projeteis = time.time()

    if len(clientes) >= 2 and not partida_iniciada:
        if inicio_espera is None:
            inicio_espera = time.time()

        tempo_passado = time.time() - inicio_espera
        tempo_restante = max(0, TEMPO_ESPERA - tempo_passado)
        Server.broadcast("contador", int(tempo_restante))

        if len(clientes) >= MAX_JOGADORES or tempo_passado >= TEMPO_ESPERA:
            if sortear_papeis():
                partida_iniciada = True
