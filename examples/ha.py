from experiment.constants import *
import subprocess
import time
from time import sleep

from profissa_lft.enb import EnB
from profissa_lft.epc import EPC
from profissa_lft.nearrtric import NearRTRIC  # Importa a classe do NearRTRIC
from profissa_lft.ue import UE


class EmuEmuWireless:

  def __init__(self):
    self.epc = EPC("epc")
    self.enb = EnB("enb")
    self.ue = UE("ue")
    self.ric = NearRTRIC("ric")  # 1. Instancia o objeto do NearRTRIC

  def setup(self):
    self.epc.instantiate(
        dockerImage="pekrio/perfsonar_srsran:noillegalinstruction", runCommand=USR_SBIN_INIT_COMMAND
    )
    self.enb.instantiate(dockerImage="pekrio/perfsonar_srsran:noillegalinstruction")
    self.ue.instantiate(
        dockerImage="pekrio/perfsonar_srsran:noillegalinstruction", runCommand=USR_SBIN_INIT_COMMAND
    )

    # 2. Instancia o container Docker do NearRTRIC
    self.ric.instantiate(
        dockerImage="pekrio/lft:nearrtric", runCommand=USR_SBIN_INIT_COMMAND
    )
    time.sleep(3)

    # 3. Conexões de Interface L2 entre os containers
    self.enb.connect(self.epc, "enbepc", "epcenb")
    self.ue.connect(self.enb, "ueenb", "enbue")
    self.enb.connect(
        self.ric, "enbric", "ricenb"
    )  # Interface para comunicação E2/SCTP

    # Conexões com a rede do Host / Internet
    self.epc.connectToInternet("9.0.0.2", 24, "epchost", "hostepc")
    self.ue.connectToInternet("12.0.0.2", 24, "uehost", "hostue")

    # 4. Configuração de IPs
    self.epc.setIp("9.0.0.1", 24, "epchost")
    self.epc.setIp("10.0.0.1", 24, "epcenb")
    self.enb.setIp("10.0.0.2", 24, "enbepc")
    self.enb.setIp(
        "10.0.0.3", 24, "enbric"
    )  # IP do eNodeB na subnet do RIC/Control
    self.ric.setIp("10.0.0.4", 24, "ricenb")  # IP atribuído ao NearRTRIC
    self.enb.setIp("11.0.0.1", 30, "enbue")
    self.ue.setIp("12.0.0.1", 24, "uehost")
    self.ue.setIp("11.0.0.2", 29, "ueenb")

    # Gateways padrão
    self.epc.setDefaultGateway("9.0.0.2", "epchost")
    self.enb.setDefaultGateway("9.0.0.2", "enbepc")
    self.ue.setDefaultGateway("12.0.0.2", "ueenb")

    self.enb.acceptPacketsFromInterface("enbue")

    # Define EPC config
    self.epc.setEPCAddress("10.0.0.1")
    self.epc.addNewUE(
        self.ue.getNodeName(), "001010123456780", EMU_EMU_WIRELESS_UE_IP_ADDR
    )

    # Define ENB Config
    self.enb.setEPCAddress("10.0.0.1")
    self.enb.setEnBAddress("10.0.0.2")
    self.enb.setSingleUEEnBAddr("11.0.0.1", 2101, "11.0.0.1", 2100)
    self.enb.setSingleUEUEAddr("11.0.0.2", 2001, "11.0.0.1", 2000)

    # 5. Configuração do FlexRIC no NearRTRIC
    self.ric.setRicBindAddress(ip="10.0.0.4", port=36421)
    self.ric.setE2NodeAddress("10.0.0.3")

    # Define UE Config
    self.ue.setUEID("001010123456780")
    self.ue.setCorrectSyncError(True)

    # --- Sequência de Inicialização dos Serviços ---

    # Step 1: EPC
    self.epc.start()
    time.sleep(3)

    # Step 2: Near-RT RIC (deve subir antes do eNodeB tentar conectar a interface E2)
    self.ric.start()
    time.sleep(3)

    # Step 3: Broker GNU Radio ZMQ
    # Método limpo via pipe para manter o Broker rodando em background sem travar no input()
    self.enb.run(
        f"tail -f /dev/null | python3 {self.enb.defaultSingleUEPath} >"
        " /srsRAN/build/gnuradio.log 2>&1 &"
    )
    time.sleep(3)

    # Step 4: eNodeB
    self.enb.start("11.0.0.1", 2101, "11.0.0.1", 2100)
    time.sleep(5)

    # Step 5: UE
    self.ue.start(
        "--rf.device_name=zmq"
        ' --rf.device_args="tx_port=tcp://11.0.0.2:2001,rx_port=tcp://11.0.0.1:2000,id=ue,base_srate=11.52e6"'
    )

    self.ue.setHost(EMU_EMU_WIRELESS_UE_IP_ADDR)
    self.epc.setHost(EMU_EMU_WIRELESS_EPC_IP_ADDR)

    self.epc.enableForwarding("epchost", "srs_spgw_sgi")
    self.ue.enableForwarding("uehost", "tun_srsue")

    subprocess.run(
        f"ip route add {EMU_EMU_WIRELESS_UE_IP_ADDR}/32 via 12.0.0.1 dev hostue",
        shell=True,
    )
    subprocess.run(
        f"ip route add {EMU_EMU_WIRELESS_EPC_IP_ADDR}/32 via 9.0.0.1 dev"
        " hostepc",
        shell=True,
    )

    self.__startPerfsonarServices()

  def __startPerfsonarServices(self):
    self.epc.run(
        "service pscheduler-runner start && service pscheduler-ticker start &&"
        " service pscheduler-scheduler start && service pscheduler-archiver"
        " start"
    )
    sleep(5)
    self.ue.run(
        "service pscheduler-runner start && service pscheduler-ticker start &&"
        " service pscheduler-scheduler start && service pscheduler-archiver"
        " start"
    )

  def tearDown(self):
    self.ric.stop()
    self.ric.delete()
    self.epc.delete()
    self.enb.delete()
    self.ue.delete()


EmuEmuWireless().setup()
