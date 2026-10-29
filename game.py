from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursinanetworking import UrsinaNetworkingClient
from ataque import dicionario
from ursina.shaders import basic_lighting_shader


Client = UrsinaNetworkingClient("localhost", 25565)
meuid = None


@Client.event
def onConnectionEstablished():
    print("Conectado ao servidor!")


@Client.event
def onConnectionError(Reason):
    print(f"Erro de conexão: {Reason}")


@Client.event
def seuid(jogador_id):
    global meuid
    meuid = jogador_id
    print(f"meu ID é {meuid}")



app = Ursina()


player = FirstPersonController(position=(random.randint(0, 10), 0.6, 0))
pivot = Entity(
    parent=scene,
    position=player.position
)
player.enabled = False



numganchos = {player: 0}

sepae = Entity(model="the_japanese_school_corridor.glb", scale=3, position=(100, 0.1, 150), shader=basic_lighting_shader)
player.speed *= 1.20
player.jump_height = 0
ground = Entity(model="plane", scale=700, color=color.dark_gray ,collider="box",shader=basic_lighting_shader)
mapa = Entity(model="umamusume_tracen_academy_school_field.glb", scale=10, position=(0, -0.1, 0),shader=basic_lighting_shader)




pal = [
    Entity(model="cube", scale=(0.3, 7, 3), position=(30, 0.6, 30), color=color.brown, collider="box", palletstate=False, shader=basic_lighting_shader),
    Entity(model="cube", scale=(0.3, 7, 3), position=(34, 0.6, 45), color=color.brown, collider="box", palletstate=False, shader=basic_lighting_shader),
]

loop1 = [
    Entity(model="cube", scale=(4, 6, 4), position=(30 + 4, 0.6, 30), color=color.gray, collider="box", shader=basic_lighting_shader),
    Entity(model="cube", scale=(4, 6, 4), position=(34 + 4, 0.6, 45), color=color.gray, collider="box", shader=basic_lighting_shader),
]
loop2 = [
    Entity(model="cube", scale=(4, 6, 4), position=(30 - 2.1, 0.6, 30), color=color.gray, collider="box", shader=basic_lighting_shader),
    Entity(model="cube", scale=(4, 6, 4), position=(34 - 2.1, 0.6, 45), color=color.gray, collider="box", shader=basic_lighting_shader),
]



cooldown = False
podediretoria = False
role = None
tasks = [Entity(model="cube", color=color.black, scale=1.5, collider="box", position=(10,0,20)),Entity(model="cube", color=color.black, scale=1.5, collider="box", position=(30,0,29)), Entity(model="cube", color=color.black, scale=1.5, collider="box", position=(0,0,50)) ]
clientes_remotos = {}
partida_iniciada = False
tempo_restante = 0
intervalo_envio = 0.05
tempo_envio = 0
projeteisid = {}
contador_texto = Text(text="Aguardando partida...", position=(-0.85, 0.45), scale=2)
hud = Entity(parent=camera.ui)
objhud = Text(
    text="Objetivo: Matar aula sem ser pego pelo professor",
    parent=hud,
    position=(-0.1, 0.43),
    scale=1.3,
    color=color.brown
)
hudprof = Entity(model="quad", parent=hud, scale=1.5, position=(0.6, -0.29), texture="models/hud.png", enabled=False)
modelo = Entity(model="models/female_fighter_01.glb", scale=1.5, rotation_y=-180, parent=player, shader=basic_lighting_shader,enabled=True)
eduarda = Entity(
    model="quad",
    texture="eduarda.png",
    scale=(7, 8),
    parent=player,
    billboard=False,
    enabled=False,
    origin_y=-0.5
)
idcaidos = []
professor = None
@Client.event
def contador(tempo):
    global tempo_restante
    tempo_restante = tempo
    contador_texto.text = f"Aguardando partida... {tempo_restante}"


@Client.event
def partida(estado):
    global partida_iniciada
    partida_iniciada = estado
    print("A partida começou!")
    player.enabled = True
    destroy(contador_texto)

@Client.event
def criarmodelo(papelp):
    global professor
    professor = papelp

    if professor in clientes_remotos:
        entidade = clientes_remotos[professor]
        pos = entidade.position
        destroy(entidade)

        
        clientes_remotos[professor] = Entity(
            model="quad",
            texture="eduarda.png",
            scale=(6, 6),
            billboard=True,
            origin_y=-0.5,
            position=pos,

        )
        
@Client.event
def position(posicoes):
    global professor
    for jogador_id, valor in posicoes.items():
        if jogador_id == meuid:
            continue

        x, y, z, rotacao = valor
        if jogador_id in clientes_remotos:
            clientes_remotos[jogador_id].position = (x, y, z)
            if jogador_id != professor:
                clientes_remotos[jogador_id].rotation_y = rotacao
        else:
                clientes_remotos[jogador_id] = Entity(model="models/female_fighter_01.glb", scale=1.5, rotation_y=180)
                if jogador_id != professor:
                    clientes_remotos[jogador_id].position = (x, y, z)
                
@Client.event
def derrubada(indice):
    pallet = pal[indice]
    if pallet.palletstate == False:
        pallet.rotation_z = 35
        pallet.palletstate = True

@Client.event
def papel(papel_recebido):
    global role
    role = papel_recebido
    Text(f"Seu papel é {role}", scale=2, color=color.white, position=(0, 10))

    if role == "professor":
        player.jump_height = 0
        player.speed = 7 * 1.35
        eduarda.enabled = False
        modelo.enabled = False
        hudprof.enabled = True
        player.position = (150, 0.1, 150)
    else:
        player.jump_height = 2
        player.speed = 7
        eduarda.enabled = True
        modelo.enabled = False

    print(f"Seu papel é {role}")


@Client.event
def jogador_saiu(jogador_id):
    if jogador_id in clientes_remotos:
        destroy(clientes_remotos[jogador_id])
        clientes_remotos.pop(jogador_id)



@Client.event
def jogador_caiu(jogador_id):
    global podediretoria
    if jogador_id == meuid:
        player.speed = 0.8
        player.jump_height = 0
        player.height = 0.5
        player.rotation_z = 0
        player.enabled = True
        podediretoria = True
        modelo.rotation_x = -90
        modelo.position = (0, -0.4, 0)
        
    if jogador_id in clientes_remotos:
        clientes_remotos[jogador_id].rotation_x = -90
@Client.event
def captura(idcapturado):
    if idcapturado == meuid:
        player.position = (100, 0.1, 150)
        player.speed = 0
        player.jump_height = 0
        modelo.rotation_x = 0
        modelo.position = (0, 1, 0)
    if idcapturado in clientes_remotos:
        clientes_remotos[idcapturado].position = (100, 0.1, 150)
        clientes_remotos[idcapturado].rotation_x = 0
def input(key):
    if key == "f" and role == "professor":
        Client.send_message("sendsepae", None)

    if key == "right mouse down":
        direcao = camera.forward + Vec3(0, 0.3, 0)
        posicao_inicial = player.position + player.forward + Vec3(0, 2, 0)
        Client.send_message("atacar", (posicao_inicial, direcao, 15))

    if key == "f" and role == "estudante":
        Client.send_message("resgatar", None)
    for task in tasks:
        if key == "e" and role == "estudante" and distance(task, player) <= 3:
            Client.send_message("fazertask", tasks.index(task))
@Client.event
def attprojetil(projeteis):
    novo_conjunto = {pro["ide"] for pro in projeteis}
    for projetil in projeteis:
        if projetil["ide"] in projeteisid:
            projeteisid[projetil["ide"]].position = projetil["posicao"]
        else:
            projeteisid[projetil["ide"]] = dicionario(direction=projetil["direcao"], position=projetil["posicao"], speed=projetil["velocidade"])
    for chave in list(projeteisid.keys()):
        if chave not in novo_conjunto:
            destroy(projeteisid[chave])
            
            projeteisid.pop(chave)
       
@Client.event
def libertar(p):
    global podediretoria
    if p == meuid:
        player.speed = 7
        player.jump_height = 2
        player.height = 2
        player.rotation_z = 0
        modelo.rotation_x = 0
        modelo.position = (0, 1, 0)
        podediretoria = False
    if p in clientes_remotos:
        clientes_remotos[p].rotation_x = 0

def update():
    global tempo_envio



    Client.process_net_events()
    tempo_envio += time.dt

    if meuid is not None and tempo_envio >= intervalo_envio:
        Client.send_message(
            "jogador",
            (player.position.x, player.position.y, player.position.z, player.rotation_y),
        )
        tempo_envio = 0


app.run()
