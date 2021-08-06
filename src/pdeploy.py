#!/usr/bin/python3

# OBS:
# 1 - Verificar todos os TODOS dos arquivos .py

# -*- coding: utf-8 -*-
import os, sys, getopt, shlex, re
import subprocess
from shutil import copyfile
from utils.utils import *
from utils.git import *
from utils.constants import *
from utils.deploy import Deploy

"""
Configurando chave ssh para conexao com o gitlab.
"""
def configura_ssh_e_git():
    ssh_path = "/root/.ssh"
    host = "gitlab.com"
    mkdir(ssh_path)
    cmd = "touch " + ssh_path + "/known_hosts"
    command(cmd)
    cmd = "touch " + ssh_path + "/id_rsa"
    command(cmd)

    cmd = f"ssh-keyscan {host}"
    command(cmd, f"{ssh_path}/known_hosts")

    save_into_file(f"{ssh_path}/id_rsa", get_env_var("SSH_PRIVATE_KEY")+"\n", "a")
    cmd = f"chmod 0600 {ssh_path}/id_rsa"
    command(cmd)

    # Configura o usuario git que sera usado por esse runner
    init_git()
    alert("SSH e git configurado")

"""
Define configuracoes iniciais para a execucao do Runner
"""
def init(argocd_repo, apps_repo, ns, need_api_configs=True):
    configura_ssh_e_git()
    # ambientes hml e prd utilizam um repositorio separado para arquivos de
    # configuracao de ms. Se eh um desses ambientes, clona tambem esse repo
    # ja as publicacoes em ambiente dev nao precisam buscar informacoes no
    # api-configs, buscam diretamente do proprio diretorio do projeto
    if ns != "dev" and need_api_configs:
        CI_PROJECT_NAME = get_env_var("CI_PROJECT_NAME")
        CI_PROJECT_PATH = get_env_var("CI_PROJECT_PATH")
        ssh_url  = f"git@gitlab.com:"
        # removendo o nome do projeto da string
        base_url = ssh_url + CI_PROJECT_PATH[:-len(CI_PROJECT_NAME)]
        fetch_repo(f"{base_url}api-configs.git", LOCAL_PATH_MS_CONFIG)

    fetch_repo(apps_repo,   LOCAL_PATH_APPS)
    fetch_repo(argocd_repo, LOCAL_PATH_ARGOCD)

"""
Metodo de Help
"""
def help():
    alert ('usage: deploy.py -v deploy   -n <ns> -a <app_properties> -c <apps_config> -d <argocd_config> -p <debug> ')
    alert ('       deploy.py -v undeploy -n <ns> -a <app_properties> -c <apps_config> -d <argocd_config> -p <debug> ')
    sys.exit(1)

"""
Metodo Main
"""
def main(argv):
    try:
        # https://www.tutorialspoint.com/python/python_command_line_arguments.htm
        opts, args = getopt.getopt(argv,"a:c:d:h:n:o:p:v:m:i:")
    except getopt.GetoptError:
        help()
    if len(argv) == 0:
        help()

    verb = ""
    apps_repo = ""
    release_suffix = ""
    app_properties = ""
    argocd_repo = ""
    ns = ""
    microservice = ""
    debug = 0

    # pega os arquivos passados por parametro
    for opt, arg in opts:
        alert(f"{opt} {arg}", "yellow")
        if opt == "-a":
            app_properties = arg
        elif opt == "-c":
            apps_repo = arg
        elif opt == "-d":
            argocd_repo = arg
        elif opt == "-h":
            help()
        elif opt == "-n":
            ns = arg
        elif opt == "-o":
            release_suffix = arg
        elif opt == "-p":
            debug = arg
        elif opt == "-v":
            verb = arg
        elif opt == "-m":
            microservice = arg
        else:
            alert ("Parametro incorreto", "red")
            help()

    # TODO Definir variavel de DEBUG global

    # Verifica se tem todos os parametros basicos para o runner funcionar
    if not (apps_repo and argocd_repo and app_properties and ns):
        alert("Parametros Incompletos", "red")
        help()

    # Caso o parametro foi de deploy
    if verb == "deploy":
        # Define as configuracoes basicas
        init(argocd_repo, apps_repo, ns)
        # Instancia o Deploy
        deploy = Deploy(release_suffix, app_properties, ns, microservice, image_tag)
        # Executa o comando de deploy
        deploy.deploy_argocd()
    elif verb == "undeploy":
        # Define as configuracoes basicas
        init(argocd_repo, apps_repo, ns, need_api_configs=False)
        # Instancia o Deploy
        deploy = Deploy(release_suffix, app_properties, ns)
        # Executa o comando de undeploy
        deploy.undeploy_argocd()

    # caso o verbo utilizado seja diferente, lerta erro
    else:
        alert ("verbo inexistente", "red")
        help()

    # Sinaliza fim de execucao do Runner
    alert(f"Job Finalizado com sucesso", "green")

if __name__ == '__main__':
    main(sys.argv[1:])
