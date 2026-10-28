#!/bin/bash

# 1. Parar e remover todos os containers Docker
docker rm -f $(docker ps -aq) 2>/dev/null || true

# 2. Remover explicitamente as interfaces de rede virtuais veth/host criadas pelo LFT
sudo ip link del hostepc 2>/dev/null || true
sudo ip link del epchost 2>/dev/null || true
sudo ip link del hostue 2>/dev/null || true
sudo ip link del uehost 2>/dev/null || true

# Limpar qualquer par veth residual restante
for dev in $(ip link show | grep -E 'veth|host' | cut -d':' -f2 | cut -d'@' -f1); do
    sudo ip link del $dev 2>/dev/null || true
done

# 3. Limpar namespaces de rede
sudo rm -rf /var/run/netns/*

# 4. Limpar pontes do Open vSwitch
sudo ovs-vsctl list-br | xargs -r -n 1 sudo ovs-vsctl del-br

# 5. Flush total no iptables (NAT, Filter e Mangle)
sudo iptables -t nat -F
sudo iptables -F
sudo iptables -X

# 6. Reiniciar o Firewalld para limpar zonas e associações órfãs (se estiver em uso)
if systemctl is-active --quiet firewalld; then
    sudo systemctl restart firewalld
fi

# 7. Prune de redes Docker
docker network prune -f
