import os
import subprocess
import shutil

# Configuration des proxys disponibles
APT_PROXIES = ["172.25.253.25:3142", "192.168.1.11:3142"]
DOCKER_PROXIES = ["172.25.253.25:8081", "192.168.1.21:8081"]
HTTP_PROXIES = ["172.16.0.1:3128", "192.168.1.31:3128"]
GW_CLASSROOM = "172.25.254.254"
DRY_MODE = True


def test_proxy(proxy_ip):
    """Teste la disponibilité d'un proxy."""
    print(f"  - Test de la disponibilité du proxy : {proxy_ip}...", end=" ")
    host, port = proxy_ip.split(":")
    result = subprocess.run(["nc", "-z", "-w", "2", host, port], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if result.returncode == 0:
        print("disponible.")
        return True
    else:
        print("non disponible.")
        return False


def find_available_proxy(proxies):
    """Trouve le premier proxy disponible dans une liste."""
    print("Recherche du proxy disponible...")
    for proxy in proxies:
        if test_proxy(proxy):
            return proxy
    print("Aucun proxy disponible trouvé.")
    return None


def disable_apt():
    """Désactive la configuration APT."""
    if DRY_MODE:
        print("[DRY MODE] Désactiver la configuration APT (supprimer /etc/apt/apt.conf.d/01proxy)")
    else:
        print("Désactivation de la configuration APT")
        if os.path.exists("/etc/apt/apt.conf.d/01proxy"):
            os.remove("/etc/apt/apt.conf.d/01proxy")


def enable_apt(apt_proxy):
    """Active la configuration APT."""
    if DRY_MODE:
        print(f"[DRY MODE] Activer la configuration APT avec le proxy : {apt_proxy}")
    else:
        print(f"Activation de la configuration APT avec le proxy : {apt_proxy}")
        with open("/etc/apt/apt.conf.d/01proxy", "w") as f:
            f.write(f"Acquire::http::Proxy \"http://{apt_proxy}\";")


def disable_docker():
    """Désactive la configuration Docker."""
    if shutil.which('docker') is not None == 0:
        if DRY_MODE:
            print("[DRY MODE] Désactiver la configuration Docker (supprimer /etc/docker/daemon.json et /etc/systemd/system/docker.service.d/http-proxy.conf)")
        else:
            print("Désactivation de la configuration Docker")
            os.makedirs("/etc/systemd/system/docker.service.d", exist_ok=True)
            with open("/etc/systemd/system/docker.service.d/http-proxy.conf", "w") as f:
                f.write("[Service]\nEnvironment=\"NO_PROXY=\"")
            subprocess.run(["systemctl", "daemon-reload"])
            subprocess.run(["systemctl", "restart", "docker"])
            if os.path.exists("/etc/docker/daemon.json"):
                os.remove("/etc/docker/daemon.json")


def enable_docker(docker_proxy):
    """Active la configuration Docker."""
    if shutil.which('docker') is not None == 0:
        if DRY_MODE:
            print(f"[DRY MODE] Activer la configuration Docker avec le proxy : {docker_proxy}")
        else:
            print(f"Activation de la configuration Docker avec le proxy : {docker_proxy}")
            with open("/etc/docker/daemon.json", "w") as f:
                f.write(f"{{\n  \"registry-mirrors\": [\"http://{docker_proxy}\"],\n  \"insecure-registries\": [\"{docker_proxy}\"]\n}}")
            subprocess.run(["systemctl", "daemon-reload"])
            subprocess.run(["systemctl", "restart", "docker"])


def disable_git():
    """Désactive la configuration Git."""
    if shutil.which('git') is not None == 0:
        if DRY_MODE:
            print("[DRY MODE] Désactiver la configuration Git")
        else:
            print("Désactivation de la configuration Git")
            subprocess.run(["git", "config", "--global", "--unset", "http.proxy"])
            subprocess.run(["git", "config", "--global", "--unset", "https.proxy"])


def enable_git(http_proxy):
    """Active la configuration Git."""
    if shutil.which('git') is not None == 0:
        if DRY_MODE:
            print(f"[DRY MODE] Activer la configuration Git avec le proxy : {http_proxy}")
        else:
            print(f"Activation de la configuration Git avec le proxy : {http_proxy}")
            subprocess.run(["git", "config", "--global", "http.proxy", f"http://{http_proxy}"])
            subprocess.run(["git", "config", "--global", "https.proxy", f"http://{http_proxy}"])


def disable_env_proxy():
    """Supprime la configuration des variables d'environnement."""
    if DRY_MODE:
        print("[DRY MODE] Supprimer la configuration des variables d'environnement (supprimer ~/.proxy_env)")
    else:
        print("Suppression de la configuration des variables d'environnement")
        proxy_env_path = os.path.expanduser("~/.proxy_env")
        if os.path.exists(proxy_env_path):
            os.remove(proxy_env_path)


def enable_env_proxy(proxy):
    """Ajoute les variables d'environnement du proxy."""
    if DRY_MODE:
        print(f"[DRY MODE] Ajouter les variables d'environnement du proxy : {proxy}")
    else:
        print(f"Ajout des variables d'environnement du proxy : {proxy}")
        proxy_env_path = os.path.expanduser("~/.proxy_env")
        with open(proxy_env_path, "w") as f:
            f.write(f"export http_proxy=\"http://{proxy}\"\n")
            f.write(f"export https_proxy=\"http://{proxy}\"\n")
            f.write(f"export ftp_proxy=\"http://{proxy}\"\n")
            f.write("export no_proxy=\"localhost,127.0.0.1,.local\"\n")
        for shell_rc in ["~/.bashrc", "~/.zshrc"]:
            shell_rc_path = os.path.expanduser(shell_rc)
            if os.path.exists(shell_rc_path):
                with open(shell_rc_path, "a") as f:
                    f.write(f"\nsource {proxy_env_path}\n")


# Détection de l'environnement (classe ou maison)
print("Détection de l'environnement (classe ou maison)...")
result = subprocess.run(["ping", "-c", "1", "-W", "2", GW_CLASSROOM], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if result.returncode != 0:
    print("Pas de proxy nécessaire, configuration directe.")
    disable_apt()
    disable_docker()
    disable_git()
    disable_env_proxy()
else:
    # Configuration des proxys
    print("Configuration des proxys...")
    apt_proxy = find_available_proxy(APT_PROXIES)
    if apt_proxy:
        print(f"Proxy APT retenu : {apt_proxy}")
        enable_apt(apt_proxy)
    else:
        print("Aucun proxy APT disponible.")

    docker_proxy = find_available_proxy(DOCKER_PROXIES)
    if docker_proxy:
        print(f"Proxy Docker retenu : {docker_proxy}")
        enable_docker(docker_proxy)
    else:
        print("Aucun proxy Docker disponible.")

    http_proxy = find_available_proxy(HTTP_PROXIES)
    if http_proxy:
        print(f"Proxy HTTP retenu : {http_proxy}")
        enable_env_proxy(http_proxy)
        enable_git(http_proxy)
        print(f"HTTP proxy configuré : {http_proxy}")
    else:
        print("Aucun proxy HTTP disponible.")
