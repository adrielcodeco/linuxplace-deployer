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
    ssh_path = "~/.ssh"
    host = "gitlab.com"
    if not os.path.exists(ssh_path):
        os.makedirs(ssh_path)

    cmd = "touch " + ssh_path + "/known_hosts"
    command(cmd)
    cmd = "touch " + ssh_path + "/id_rsa"
    command(cmd)

    cmd = f"ssh-keyscan {host}"
    command(cmd, f"{ssh_path}/known_hosts")

    save_into_file(f"{ssh_path}/id_rsa", get_env_var("SSH_PRIVATE_KEY"), "a")
    cmd = f"chmod 0600 {ssh_path}/id_rsa"
    command(cmd)

    command("git config --global user.email \"suporte@linuxplace.com.br\"; git config --global user.name \"LxP Deployer\"")
    alert("\n#SSH e git configurado")


def init(argocd_repo, apps_repo):
    configura_ssh_e_git()

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

    # TODO descomentar
    #fetch_repo(apps_repo,   LOCAL_PATH_APPS)
    #fetch_repo(f"{base_url}/api-configs.git", LOCAL_PATH_MS_CONFIG)
    #fetch_repo(argocd_repo, LOCAL_PATH_ARGOCD)

# def build_values(app_name, release_name):
#     if os.path.exists(LOCAL_CI_VALUES):
#         os.remove(LOCAL_CI_VALUES)
#
#     open(LOCAL_CI_VALUES, 'a').close()
#
#     set_yq(LOCAL_CI_VALUES, "releaseName", release_name)
#     set_yq(LOCAL_CI_VALUES, "image.repository", REPOSITORY)
#     set_yq(LOCAL_CI_VALUES, "image.tag", TAG)
#
#     set_yq(LOCAL_CI_VALUES, "AwsAccountId", AWS_ACCOUNT_ID)
#
#     set_yq(LOCAL_CI_VALUES, "cd.commit", "TODO")
#     set_yq(LOCAL_CI_VALUES, "cd.branch", "TODO")
#     set_yq(LOCAL_CI_VALUES, "cd.basename", app_name)
#     set_yq(LOCAL_CI_VALUES, "cd.reponame", "TODO")
#     set_yq(LOCAL_CI_VALUES, "cd.group", "TODO")

""" Funcoes para comandos HELM """
# def build_release_status(deploy_name):
#     cmd = f"helm --namespace {NAMESPACE} STATUS {deploy_name} -o json"
#     #print "COMANDO HELM: " + str(cmd)
#
#     deploy_status_result = ""
#     #try:
#     #    deploy_status_result = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
#     #except subprocess.CalledProcessError, e:
#     #    deploy_status_result = e.output
#
#     deploy_status_result = deploy_status_result[:-1]
#
#     global RELEASE_STATUS
#     if "Error" in deploy_status_result:
#         #possui erro
#         RELEASE_STATUS = {'error':'true', 'status': deploy_status_result[7:]}
#         if "release: not found" in deploy_status_result:
#             return 1
#         else:
#             #TODO
#             return 2
#     else:
#         #nao possui erro
#         RELEASE_STATUS = {'error':'false', 'status': deploy_status_result}
#         return 0


# def helm_template(release_name,name_override_cmd):
#     cmd = f"helm template -f {LOCAL_CI_VALUES}, -f ./kubernetes/values.yaml {release_name} {LOCAL_PATH_CHART} --namespace {NAMESPACE} {name_override_cmd}"
#     ret, out = command(cmd)
#     return out.decode("utf-8")

# def helm_delete(release_name):
#     cmd = ["helm"]+["delete"]+[release_name]+["--namespace"]+[NAMESPACE]
#
#     #print "COMANDO HELM: " + str(cmd)
#     subprocess.check_call(cmd)
#     print


# def helm_upgrade(release_name):
#     # parent is not 0
#     # child is 0
#     i_am_parent = os.fork()
#
#     if not i_am_parent:
#         #print "PING"
#         cmd = ["helm"]+["upgrade"]+["--install"]+["-f"]+[LOCAL_CI_VALUES]+["-f"]+["./kubernetes/values.yaml"]+[release_name]+[LOCAL_PATH_CHART]+["--namespace"]+[NAMESPACE]+["--wait"]+["--timeout"]+[HELM_TIMEOUT]#+["&"]
#
#         #print "COMANDO HELM: " + str(cmd)
#         subprocess.check_call(cmd)
#     #else:
#         #print "PONG"


# def generateHelmRelease(release_name_override, release_suffix, app_properties, chart_repo):
#     # TODO
#     # Etapa 1: chegar estado atual
#     # constoi o nome do deploy
#     release_name = ""
#     if release_name_override:
#         release_name = release_name_override
#     else:
#         release_name = get_release_name(release_suffix, app_properties)
#
#     # Recupera nomes dentro do arquivo propeties no repo do ms
#     app_name = get_yq(app_properties, "basename")
#     group_name = get_yq(app_properties, "groupname")
#
#     print (release_name)
#
#     name_override_cmd = ""
#     if app_name:
#         name_override_cmd = ["--set-string"]+["nameOverride="+app_name]
#
#     build_values(app_name)
#
#     hrFile = release_name + "-hr.yaml"
#
#     copyfile("helmReleaseTemplate.yaml", hrFile)
#
#     open(hrFile, 'a').close()
#
#     # Metadata informations
#     set_yq(hrFile, "metadata.name", release_name)
#     set_yq(hrFile, "metadata.namespace", NAMESPACE)
#
#     # Spec Informations
#     set_yq(hrFile, "spec.releaseName", release_name)
#     set_yq(hrFile, "spec.chart.git", chart_repo)
#
#     # spec.values
#     set_yq(hrFile, "spec.values.image.repository", REPOSITORY)
#     set_yq(hrFile, "spec.values.image.tag", TAG)
#
#     #set_yq(LOCAL_CI_VALUES, "cd.commit", "TODO")
#     #set_yq(LOCAL_CI_VALUES, "cd.branch", "TODO")
#     #set_yq(LOCAL_CI_VALUES, "cd.basename", app_name)
#     #set_yq(LOCAL_CI_VALUES, "cd.reponame", "TODO")
#     #set_yq(LOCAL_CI_VALUES, "cd.group", "TODO")
#
#     return hrFile


""" Funcoes ArgoCD """
"""
def update_argo_repo(repo):
    # TODO
    global CI_PROJECT_NAME

    manifest = read_from_file("manifests.yaml")
    release_name = get_yq(LOCAL_CI_VALUES, "releaseName")

    git("clone", repo, "argo")

    path = NAMESPACE + "/" + CI_PROJECT_NAME + "/" + release_name


    if not os.path.exists(path): 
        os.makedirs(path)

    print ("Path no repositorio ArgoCD: " + path)

    save_to_file(path + "/manifests.yaml")
"""
"""
def generateApplicationArgoCD(repo_aplicacoes, release_name):

    set_yq(LOCAL_ARGOCDAPP, "metadata.name", release_name)

    set_yq(LOCAL_ARGOCDAPP, "spec.destination.namespace", NAMESPACE)
    set_yq(LOCAL_ARGOCDAPP, "spec.destination.server", "{{ .Values.spec.destination.server }}")

    set_yq(LOCAL_ARGOCDAPP, "spec.project", NAMESPACE)

    set_yq(LOCAL_ARGOCDAPP, "spec.source.path", "default-chart")
    set_yq(LOCAL_ARGOCDAPP, "spec.source.repoURL", repo_aplicacoes)
    set_yq(LOCAL_ARGOCDAPP, "spec.source.targetRevision", "HEAD")
    set_yq(LOCAL_ARGOCDAPP, "spec.source.helm.valueFiles", "../{{ .Values.env }}/"+ release_name + "/values.yaml", True) 

    os.rename(LOCAL_ARGOCDAPP, release_name + ".yaml")
"""

"""
def generateValuesApp(release_name_override, release_suffix, app_properties, chart_repo):

    release_name = get_yq(LOCAL_CI_VALUES, "releaseName")

    # Recupera nomes dentro do arquivo propeties no repo do ms
    app_name = get_yq(app_properties, "basename")

    build_values(app_name, release_name)

    copyfile("./kubernetes/values.yaml", "values.yaml")

    set_yq("values.yaml", "spec.values.image.repository", REPOSITORY)

    # spec.values
    #set_yq(hrFile, "spec.values.image.repository", REPOSITORY)
    #set_yq(hrFile, "spec.values.image.tag", TAG)

    #set_yq(LOCAL_CI_VALUES, "cd.commit", "TODO")
    #set_yq(LOCAL_CI_VALUES, "cd.branch", "TODO")
    #set_yq(LOCAL_CI_VALUES, "cd.basename", app_name)
    #set_yq(LOCAL_CI_VALUES, "cd.reponame", "TODO")
    #set_yq(LOCAL_CI_VALUES, "cd.group", "TODO")    

    return hrFile
"""

def help():
    # TODO arruamr
    alert ('usage: deploy.py -v init')
    alert ('       deploy.py -v fetchchart          -c <chart_repo> [-b <chart_branch> -r <release_name_override>]')
    alert ('       deploy.py -v generateHelmRelease -n <ns> -a <app_properties> -i <image_tag> -c <chart_repo>')
    alert ('       deploy.py -v deployArgoCD        -n <ns> -a <app_properties>')
    sys.exit(1)




def get_aws_account_id():
    global AWS_ACCOUNT_ID

    sts = boto3.client('sts')
    resp = sts.get_caller_identity()

    AWS_ACCOUNT_ID = resp["Account"]

    if AWS_ACCOUNT_ID == "": 
        alert ("Account ID nao encontrado.", "red")
        erro(1)

    print (f"Running in {AWS_ACCOUNT_ID}")


# def get_repository_tag(image_name):
#     global TAG
#     global REPOSITORY
#
#     # se variavel vazia
#     if not image_name:
#         TAG = "none"
#         REPOSITORY = "none"
#     else:
#         # usa regex pra fazer split via ":"
#         splited = re.split(":", image_name)
#         REPOSITORY = splited[0]
#         TAG = splited[1]
#
#     alert ("Repositorio:tag : " + REPOSITORY + ":" + TAG)


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
        init(argocd_repo, apps_repo)

        deploy = Deploy(release_suffix, app_properties, ns)

        # Primeiro faz a alteracao no config
        deploy.create_app_config()

        deploy.deploy_argocd()

        #depois faz a alteracao do argocd

    elif verb == "":
        alert ("verbo inexistente", "red")
        help()

if __name__ == '__main__':
    main(sys.argv[1:])
