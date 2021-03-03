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
    alert("\n#SSH e git configurado")

def init(argocd_repo, apps_repo, ns):
    configura_ssh_e_git()
    if ns != "dev":
        # publicacoes em ambiente dev nao precisa buscar informacoes no api-configs
        # buscam diretamente do proprio diretorio do projeto
        global CI_PROJECT_PATH
        CI_PROJECT_PATH = get_env_var("CI_PROJECT_PATH")
        alert("Pegando variavel de ambiente", "red")
        print(CI_PROJECT_PATH)
        project_name = get_regex("\/.*$", CI_PROJECT_PATH)[1:]

        global CI_REPOSITORY_URL
        CI_REPOSITORY_URL = get_env_var("CI_REPOSITORY_URL")
        base_url = remove_regex(f"\/{project_name}.*$", CI_REPOSITORY_URL)
        print(base_url)
        print(base_url+"/api-configs.git")
        exit (3)
        fetch_repo(f"{base_url}/api-configs.git", LOCAL_PATH_MS_CONFIG)

    fetch_repo(apps_repo,   LOCAL_PATH_APPS)
    fetch_repo(argocd_repo, LOCAL_PATH_ARGOCD)

def help():
    # TODO arruamr
    alert ('usage: deploy.py -v init')
    alert ('       deploy.py -v deployArgoCD -n <ns> -a <app_properties>')
    sys.exit(1)


def main(argv):
    try:
        # https://www.tutorialspoint.com/python/python_command_line_arguments.htm
        opts, args = getopt.getopt(argv,"a:c:d:h:i:n:o:r:v:")
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

    for opt, arg in opts:
        alert(f"{opt} {arg}")
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
        elif opt == "-r":
            release_name_override = arg
        elif opt == "-v":
            verb = arg
        else: 
            alert ("parametro incorreto", "red")
            help()

    if verb == "deployArgoCD":
        if not (apps_repo and argocd_repo and app_properties and ns) :
            help()
        init(argocd_repo, apps_repo, ns)
        deploy = Deploy(release_suffix, app_properties, ns)
        deploy.create_app_config()
        deploy.deploy_argocd()

    elif verb == "":
        alert ("verbo inexistente", "red")
        help()

if __name__ == '__main__':
    main(sys.argv[1:])
