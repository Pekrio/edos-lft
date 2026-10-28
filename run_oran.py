#!/usr/bin/env python3
import cmd
import os
import subprocess
import sys

# Mapeamento de imagens e nomes exatos dos containers
IMG_RIC = "pekrio/lft:nearrtric"
IMG_SRSRAN = "pekrio/lft:srsran"

CONTAINERS = {
    "ric": IMG_RIC,
    "epc": IMG_SRSRAN,
    "enb": IMG_SRSRAN,
    "ue": IMG_SRSRAN,
}


def run_cmd(command, capture=False):
    """Executa um comando de shell no host."""
    try:
        if capture:
            return subprocess.check_output(command, shell=True, text=True).strip()
        else:
            subprocess.run(command, shell=True, check=True)
            return True
    except subprocess.CalledProcessError as e:
        print(f"\n[ERRO]: Falha ao executar o comando no host: {e}")
        return False


class LFTOranHostCLI(cmd.Cmd):
    intro = (
        "\n======================================================\n"
        "   LFT Multi-Container CLI Shell (RIC, EPC, ENB, UE)  \n"
        "   Digite /help para listar os comandos disponiveis.   \n"
        "======================================================\n"
    )
    prompt = "edos-lft> "

    def default(self, line):
        if line.startswith("/"):
            parts = line[1:].split()
            cmd_name = parts[0]
            arg = " ".join(parts[1:]) if len(parts) > 1 else ""
            try:
                func = getattr(self, "do_" + cmd_name)
                return func(arg)
            except AttributeError:
                print(
                    f"[!] Comando desconhecido: '{line}'. Digite /help para ver a lista."
                )
        else:
            print(
                "[!] Os comandos devem iniciar com '/'."
            )

    # --- COMANDOS DA CLI ---

    def do_ddos(self, arg):
        # Executa um ataque de inundação UDP a partir do container UE para o gateway do EPC (172.16.0.1)
        # -u: Usa o protocolo UDP (sem controle de fluxo/congestionamento)
        # -b 0: Banda ilimitada (envia na taxa máxima suportada pela CPU)
        # -P 4: Abre 4 conexões/threads paralelas simultâneas
        # -t 40: Mantém o estresse contínuo por 40 segundos
        # -l 1400: Pacotes com tamanho de payload de 1400 bytes (próximo do MTU)
        print("\n[CLI Host]: Disparando ataque de inundação UDP (EDoS) a partir do UE...")
        run_cmd("docker exec -it ue iperf3 -c 172.16.0.1 -u -b 0 -P 4 -t 40 -l 1400")

    def do_hello_world(self, arg):
        # Inicia o xApp básico de teste (HelloWorld) compilado em C dentro do Near-RT RIC
        # -c: Especifica o arquivo de configuração da interface E2/E42 do FlexRIC
        print("\n[CLI Host]: Iniciando xApp HelloWorld no Near-RT RIC...")
        run_cmd("sudo docker exec -it ric /usr/local/flexric/xApp/c/helloworld/xapp_hw -c /etc/flexric/flexric.conf")

    def do_kpm(self, arg):
        # Inicia o xApp de monitoramento de métricas KPM (E2SM-KPM v2/v3) em C
        # Conecta ao Near-RT RIC e imprime em tempo real a latência E2 e os indicadores de rádio (CQI/PRB)
        print("\n[CLI Host]: Iniciando xApp KPM Monitor no Near-RT RIC...")
        run_cmd("sudo docker exec -it ric /usr/local/flexric/xApp/c/monitor/xapp_kpm_moni -c /etc/flexric/flexric.conf")

    def do_enb_log(self, arg):
        # Exibe as primeiras 100 linhas do log de execução do eNodeB/gNodeB para depurar a inicialização ou a conexão E2
        print("\n[CLI Host]: Lendo as primeiras 100 linhas do log do eNB...")
        run_cmd("sudo docker exec -it enb head -n 100 /tmp/enb.log")

    def do_ric_log(self, arg):
        # Exibe as primeiras 100 linhas do log do Near-RT RIC (FlexRIC)
        # Útil para verificar o status das conexões E2AP e o registro dos xApps
        print("\n[CLI Host]: Lendo as primeiras 100 linhas do log do Near-RT RIC...")
        run_cmd("sudo docker exec -it ric head -n 100 /var/log/nearrtric.log")

    def do_epc_log(self, arg):
        # Exibe as primeiras 100 linhas do log de execução do EPC (Evolved Packet Core)
        # Permite inspecionar eventos de controle MME, associação S1 e interfaces SGi/SPGW
        print("\n[CLI Host]: Lendo as primeiras 100 linhas do log da EPC...")
        run_cmd("sudo docker exec -it epc head -n 100 /srsRAN/build/epc.out")

    def do_ue_log(self, arg):
        # Exibe as primeiras 100 linhas do log do User Equipment (srsUE)
        # Útil para verificar o procedimento de Attach, sincronização PHY/MAC e ativação da interface tun_srsue
        print("\n[CLI Host]: Lendo as primeiras 100 linhas do log do UE...")
        run_cmd("sudo docker exec -it ue head -n 100 /srsRAN/build/ue.out")

    def do_start_topology(self, arg):
        """/start_topology - Inicia a topologia completa em ordem: ric -> epc -> enb -> ue."""
        # Executa o script em Python responsável por instanciar a topologia O-RAN no LFT
        # Sobe os containers na ordem de dependência adequada (RIC -> EPC -> eNB -> UE) e configura o roteamento de rede
        print("\n[CLI Host]: Iniciando toda a topologia LFT...")
        run_cmd("sudo python3 -m examples.simpleORANTopology")
        print("\n[+] Todos os containers da topologia foram iniciados!")

    def do_restart_topology(self, arg):
        """/stop_all - Encerra e remove todos os 4 containers."""
        # Executa o script shell responsável por limpar e reiniciar o ambiente
        # Para a execução dos processos, remove as pontes/interfaces virtuais e re-inicializa os containers zerados
        print("\n[CLI Host]: Reiniciando a topologia LFT...")
        run_cmd("./restart.sh")
        print("[+] Topologia encerrada.")

    def do_clear(self, arg):
        """/clear - Limpa a tela."""
        os.system("clear")

    def do_exit(self, arg):
        """/exit - Encerra a CLI."""
        print("\nSaindo da CLI do Host. Ate logo!")
        return True

    def do_help(self, arg):
        """/help - Lista os comandos disponiveis."""
        print("\n===========================================================")
        print("                COMANDOS DISPONIVEIS NA CLI LFT            ")
        print("===========================================================")
        print("\n  [ Gerenciamento da Topologia ]")
        print("    /start_topology    - Sobe toda a topologia em sequencia (ric -> epc -> enb -> ue)")
        print("    /restart_topology  - Executa o script restart.sh para limpar e reiniciar o ambiente")

        print("  [ Testes de Carga e Ataque ]")
        print("    /ddos              - Dispara ataque de inundacao UDP (EDoS) de 40s a partir do UE")

        print("  [ xApps do Near-RT RIC ]")
        print("    /hello_world       - Executa o xApp de teste HelloWorld no FlexRIC")
        print("    /kpm               - Inicia o monitoramento de metricas E2SM-KPM em tempo real")

        print("  [ Depuracao e Logs dos Containers ]")
        print("    /ric_log           - Exibe as primeiras 100 linhas do log do Near-RT RIC")
        print("    /epc_log           - Exibe as primeiras 100 linhas do log do EPC")
        print("    /enb_log           - Exibe as primeiras 100 linhas do log do eNodeB")
        print("    /ue_log            - Exibe as primeiras 100 linhas do log do UE")

        print("  [ Utilitarios da CLI ]")
        print("    /clear             - Limpa a tela do terminal")
        print("    /exit              - Encerra a CLI")
        print("===========================================================\n")

    do_quit = do_exit


if __name__ == "__main__":
    try:
        LFTOranHostCLI().cmdloop()
    except KeyboardInterrupt:
        print("\n\nSaindo da CLI...")
