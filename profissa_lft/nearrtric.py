# Copyright (C) 2026 Alexandre Mitsuru Kaihara
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

from .node import Node
from .constants import *


class NearRTRIC(Node):
    def __init__(self, name: str, flexricConfigPath="/etc/flexric/flexric.conf"):
        super().__init__(name)
        self.defaultFlexricConfigPath = flexricConfigPath
        self.ricBinPath = "/usr/local/bin/nearRT-RIC"
        self.xappDir = "/usr/local/flexric/xApp"
        self.xappDir = "/usr/local/flexric/xApp/c/kpm_rc"
        self.xappKpmBinPath = "/usr/local/flexric/xApp/xapp_kpm_moni"
        self.xappKpmBinPath = "/usr/local/flexric/xApp/c/kpm_rc/xapp_kpm_rc"
        self.config = None

    def instantiate(
        self,
        dockerImage="pekrio/lft:nearrtric",
        dockerCommand="tail -f /dev/null",
        dns="8.8.8.8",
        runCommand="",
    ) -> None:
        """
        Instancia o container Docker do nearRT-RIC e carrega a configuração inicial.
        """
        cmd = f"docker run -d --network=none --privileged --name={self.getNodeName()} --dns={dns} {dockerImage} tail -f /dev/null"
        super().instantiate(
            dockerImage=dockerImage,
            dockerCommand=cmd,
            dns=dns,
            runCommand=runCommand,
        )
        self.config = self.readConfigFile(self.defaultFlexricConfigPath)

    def start(self, logPath="/var/log/nearrtric.log") -> None:
        """
        Inicia o serviço principal do nearRT-RIC (FlexRIC) em segundo plano.
        """
        super().run(
            f"stdbuf -oL -eL {self.ricBinPath} -c {self.defaultFlexricConfigPath} > {logPath} 2>&1 &"
        )

    def stop(self) -> None:
        """
        Encerra a execução do nearRT-RIC e de xApps associados no container.
        """
        self.stopKpmXApp()
        super().run("pkill -f -9 nearRT-RIC")

    def startKpmXApp(self, logPath="/var/log/xapp_kpm.log") -> None:
        """
        Inicia o xApp de monitoramento KPM para coletar métricas E2 do srsRAN 25.10.0.
        """
        self.run(
            f"{self.xappKpmBinPath} -c {self.defaultFlexricConfigPath} > {logPath} 2>&1 &"
        )

    def stopKpmXApp(self) -> None:
        """
        Encerra a execução do xApp KPM.
        """
        self.run("pkill -f -9 xapp_kpm_moni")

    def setDefaultFlexricConfigPath(self, path: str) -> None:
        self.defaultFlexricConfigPath = path

    def getDefaultFlexricConfigPath(self) -> str:
        return self.defaultFlexricConfigPath


    def configureFlexric(
    self, ric_ip="10.0.0.4", ric_port=36421, e2_node_ip="10.0.0.3", xapp_port=36422
) -> None:
        """Configura o flexric.conf em uma única operação atômica e limpa."""
        path = self.defaultFlexricConfigPath

    # Note o EOF sem aspas simples para permitir a substituição das f-strings
    # e sem indentação nas linhas do arquivo para não gerar espaços indesejados.
        cmd = f"""cat << EOF > {path}
[NEAR-RIC]
NEAR_RIC_IP = {ric_ip}
RIC_PORT = {ric_port}
SM_DIR = /usr/local/lib/flexric/

[XAPP]
RIC_IP = {ric_ip}
XAPP_PORT = {xapp_port}
E2_NODE_IP = {e2_node_ip}
DB_DIR = /tmp/
EOF"""

        self.run(cmd)
