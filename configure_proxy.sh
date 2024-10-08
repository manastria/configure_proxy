#!/bin/bash

# Nom du fichier : configure_proxies.sh

# Liste des proxys disponibles
APT_PROXIES=("192.168.1.10:3142" "192.168.1.11:3142")
DOCKER_PROXIES=("192.168.1.20:8081" "192.168.1.21:8081")
HTTP_PROXIES=("192.168.1.30:3128" "192.168.1.31:3128")
GW_CLASSROOM=192.168.1.1

# Fonction pour tester la disponibilité d'un proxy
test_proxy() {
    local proxy_ip=$1
    nc -z -w 2 $(echo $proxy_ip | cut -d':' -f1) $(echo $proxy_ip | cut -d':' -f2) >/dev/null 2>&1
    return $?
}

# Fonction pour trouver le premier proxy disponible dans une liste
find_available_proxy() {
    local proxies=($@)
    for proxy in "${proxies[@]}"; do
        if test_proxy $proxy; then
            echo $proxy
            return 0
        fi
    done
    return 1
}

# Fonction pour désactiver la configuration APT
disable_apt() {
    rm -f /etc/apt/apt.conf.d/01proxy
}

# Fonction pour activer la configuration APT
enable_apt() {
    local apt_proxy=$1
    echo "Acquire::http::Proxy \"http://$apt_proxy\";" > /etc/apt/apt.conf.d/01proxy
    echo "APT proxy configuré : $apt_proxy"
}

# Fonction pour désactiver la configuration Docker
disable_docker() {
    if command -v docker >/dev/null 2>&1; then
        mkdir -p /etc/systemd/system/docker.service.d
        echo -e "[Service]\nEnvironment=\"NO_PROXY=\"" > /etc/systemd/system/docker.service.d/http-proxy.conf
        systemctl daemon-reload
        systemctl restart docker
        rm -f /etc/docker/daemon.json
    fi
}

# Fonction pour activer la configuration Docker
enable_docker() {
    local docker_proxy=$1
    if command -v docker >/dev/null 2>&1; then
        sudo bash -c 'cat > /etc/docker/daemon.json << EOF
{
  "registry-mirrors": ["http://$docker_proxy"],
  "insecure-registries": ["$docker_proxy"]
}
EOF'
        systemctl daemon-reload
        systemctl restart docker
        echo "Docker proxy configuré : $docker_proxy"
    fi
}

# Fonction pour désactiver la configuration Git
disable_git() {
    if command -v git >/dev/null 2>&1; then
        git config --global --unset http.proxy
        git config --global --unset https.proxy
    fi
}

# Fonction pour activer la configuration Git
enable_git() {
    local http_proxy=$1
    if command -v git >/dev/null 2>&1; then
        git config --global http.proxy "http://$http_proxy"
        git config --global https.proxy "http://$http_proxy"
        echo "Git proxy configuré : $http_proxy"
    fi
}

# Fonction pour supprimer la configuration des variables d'environnement
disable_env_proxy() {
    rm -f ~/.proxy_env
}

# Fonction pour ajouter les variables d'environnement du proxy
enable_env_proxy() {
    local proxy=$1
    echo "export http_proxy=\"http://$proxy\"" > ~/.proxy_env
    echo "export https_proxy=\"http://$proxy\"" >> ~/.proxy_env
    echo "export ftp_proxy=\"http://$proxy\"" >> ~/.proxy_env
    echo "export no_proxy=\"localhost,127.0.0.1,.local\"" >> ~/.proxy_env
    # Ajouter l'inclusion du fichier de variables d'environnement dans .bashrc et .zshrc
    if [ -f ~/.bashrc ] && ! grep -q "source ~/.proxy_env" ~/.bashrc; then
        echo "source ~/.proxy_env" >> ~/.bashrc
    fi
    if [ -f ~/.zshrc ] && ! grep -q "source ~/.proxy_env" ~/.zshrc; then
        echo "source ~/.proxy_env" >> ~/.zshrc
    fi
}

# Détection de l'environnement (classe ou maison)
ping -c 1 -W 2 ${GW_CLASSROOM} >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Pas de proxy nécessaire, configuration directe."
    disable_apt
    disable_docker
    disable_git
    disable_env_proxy
    exit 0
fi

# Configuration des proxys
APT_PROXY=$(find_available_proxy "${APT_PROXIES[@]}")
DOCKER_PROXY=$(find_available_proxy "${DOCKER_PROXIES[@]}")
HTTP_PROXY=$(find_available_proxy "${HTTP_PROXIES[@]}")

if [ -n "$APT_PROXY" ]; then
    enable_apt "$APT_PROXY"
fi

if [ -n "$DOCKER_PROXY" ]; then
    enable_docker "$DOCKER_PROXY"
fi

if [ -n "$HTTP_PROXY" ]; then
    enable_env_proxy "$HTTP_PROXY"
    enable_git "$HTTP_PROXY"
    echo "HTTP proxy configuré : $HTTP_PROXY"
fi