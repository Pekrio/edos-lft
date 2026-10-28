# Tutorial: Configuração e Execução do Ambiente eDoS-LFT

Este guia fornece o passo a passo para configurar e executar a topologia **eDoS-LFT** em uma máquina virtual com **Ubuntu 24.04 LTS (Server Edition)**.

---

## 📋 Pré-requisitos

- **SO:** Ubuntu 24.04 LTS (versão Server ou Desktop).
- **Acesso:** Permissões de superusuário (`sudo`) e conexão com a internet.
- **Ferramenta essencial:** `git` instalado.

---

## 🚀 Passo a Passo

### 1. Clonar o Repositório

Faça o clone do projeto oficial e acesse o diretório principal:

```bash
git clone https://github.com/Pekrio/edos-lft
cd edos-lft
```

---

### 2. Instalar Pacotes e Dependências do Sistema

Atualize os repositórios locais e instale os pacotes necessários de rede, monitoramento, Python e suporte ao Docker:

```bash
sudo apt update && sudo apt install -y \
    python3-pip \
    python3-dev \
    python3-pandas \
    python3-matplotlib \
    docker.io \
    openvswitch-switch \
    openvswitch-common \
    iproute2 \
    iptables \
    firewalld \
    net-tools \
    nfdump \
    tshark \
    tcpdump
```

Em seguida, inicialize os serviços necessários e configure as permissões de usuário do Docker:

```bash
# Habilitar e iniciar o serviço Open vSwitch
sudo systemctl enable --now openvswitch-switch

# Adicionar o usuário atual ao grupo docker
sudo usermod -aG docker $USER

# Aplicar o novo grupo à sessão atual sem precisar deslogar
newgrp docker
```

---

### 3. Executar o Script de Dependências

Certifique-se de estar no diretório raiz do repositório (`edos-lft`), conceda permissão de execução ao script e rode-o:

```bash
chmod +x dependencies.sh
sudo ./dependencies.sh
```

---

### 4. Executar a Topologia

Na raiz do projeto, execute o cli amigável:

```bash
sudo python3 run_oran.py
```
