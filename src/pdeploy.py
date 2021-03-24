#!/usr/bin/python3
# TODO trocar

# -*- coding: utf-8 -*-
import os, sys, getopt, shlex, re
import subprocess
#import jq, boto3
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

    init_git()
    alert("SSH e git configurado")

def init(argocd_repo, apps_repo, ns, need_api_configs=True):
    configura_ssh_e_git()
    if ns != "dev" and need_api_configs:
        # publicacoes em ambiente dev nao precisa buscar informacoes no api-configs
        # buscam diretamente do proprio diretorio do projeto
        CI_PROJECT_NAME = get_env_var("CI_PROJECT_NAME")
        CI_PROJECT_PATH = get_env_var("CI_PROJECT_PATH")
        print (CI_PROJECT_NAME)
        print (CI_PROJECT_PATH)
        ssh_url  = f"git@gitlab.com:"
        # removendo o nome do projeto
        base_url = ssh_url + CI_PROJECT_PATH[:-len(CI_PROJECT_NAME)]
        print (base_url)
        fetch_repo(f"{base_url}api-configs.git", LOCAL_PATH_MS_CONFIG)

    fetch_repo(apps_repo,   LOCAL_PATH_APPS)
    fetch_repo(argocd_repo, LOCAL_PATH_ARGOCD)

def help():
    # TODO arruamr
    alert ('usage: deploy.py -v deploy   -n <ns> -a <app_properties> -c <apps_config> -d <argocd_config> -p <debug> ')
    alert ('       deploy.py -v undeploy -n <ns> -a <app_properties> -c <apps_config> -d <argocd_config> -p <debug> ')
    sys.exit(1)


def main(argv):
    try:
        # https://www.tutorialspoint.com/python/python_command_line_arguments.htm
        opts, args = getopt.getopt(argv,"a:c:d:h:i:n:o:p:r:v:")
    except getopt.GetoptError:
        help()
    if len(argv) == 0:
        help()

    verb = ""
    apps_repo = ""
    release_name_override = ""
    release_suffix = ""
    app_properties = ""
    argocd_repo = ""
    ns = ""
    image_name = ""
    global DEBUG

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
        elif opt == "-i":
            image_name = arg
        elif opt == "-n":
            ns = arg
        elif opt == "-o":
            release_suffix = arg
        elif opt == "-p":
            DEBUG = arg
        elif opt == "-r":
            release_name_override = arg
        elif opt == "-v":
            verb = arg
        else: 
            alert ("Parametro incorreto", "red")
            help()

    #TODO remover
    DEPLOY = 0

    alert("TESTE", "red")

    if not (apps_repo and argocd_repo and app_properties and ns):
        help()
        exit(1)

    if verb == "deploy":
        init(argocd_repo, apps_repo, ns)
        deploy = Deploy(release_suffix, app_properties, ns)
        deploy.deploy_argocd()
    elif verb == "undeploy":
        init(argocd_repo, apps_repo, ns, need_api_configs=False)
        deploy = Deploy(release_suffix, app_properties, ns)
        deploy.undeploy_argocd()

    elif verb == "":
        alert ("verbo inexistente", "red")
        help()

    alert(f"Job Finalizado com sucesso", "green")
if __name__ == '__main__':
    main(sys.argv[1:])
