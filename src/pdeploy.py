#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, getopt, shlex, boto3, re
import subprocess
#import jq
from shutil import copyfile


""" 
Funcoes para uso de git
"""
def git(*args):
    return subprocess.check_call(['git'] + list(args))

def fetch_chart(repo, branch):
    git("clone", repo, "-b", branch, LOCAL_PATH_CHART)

"""
Configurando chave ssh para conexao com o gitlab.
"""
def init_key():
    path = "./ssh"
    host = "gitlab.com"

    if not os.path.exists(path): 
        os.makedirs(path)

    cmd = "ssh-keyscan " + host + " >> " + path + "/known_hosts"
    os.system(cmd)

    known_file = open(path + "/id_rsa", 'a')
    known_file.write(os.environ["SSH_PRIVATE_KEY"])
    known_file.close

    cmd = "chmod 0600 " + path + "/id_rsa"
    os.system(cmd)


""" Funcoes para manipulação de Arquivo """
def save_to_file(file_name, information):

    file_pointer = open(file_name, "w")
    file_pointer.write(information)
    file_pointer.close()


def read_from_file(file_name):

    file_pointer = open(file_name, "r")

    if file_pointer == "":
        print ("Nao existe o arquivo" + file_name + " para ser lido.")

    information = file_pointer.read()
    file_pointer.close()

    return information


def get_yq(path_file, key):
    # monta a query
    cmd = ['yq3'] + ['r'] + [path_file] + [key]
    # yq2.12
    #cmd = ['yq'] + ['-y'] + ["." + key] + [path_file] + [" | head -n1"]
    #print "COMANDO YQ: " + str(cmd)
    # processa o comando e captura o resultado
    result = subprocess.check_output(cmd)

    # retira o \n no final 
    return result[:-1].decode("utf-8")


def set_yq(path_file, key, value, isList=False):
    # monta a query
    if isList:
        cmd = ['yq3'] + ['w'] + ['-i'] + [path_file] + [key+"[+]"] + [value]
    else:
        cmd = ['yq3'] + ['w'] + ['-i'] + [path_file] + [key] + [value]

    #print "COMANDO YQ: " + str(cmd)
    # processa o comando e captura o resultado
    subprocess.check_call(cmd)


def get_jq(json, key):
    # TODO testar se ja tiver um deploy
    ret = ""
    try:
        #print jq.first(key, json)
        ret = "trocar"
    except Exception as e:
        #print "asdfk"
        ret = ""
    
    exit(0)
    # TODO
    return ret


""" Funcoes para construcao de informacoes """

def get_release_name(release_suffix, app_properties):
    # prefix
    api_version = get_yq(app_properties, "apiVersion")

    # mid
    app_name = get_yq(app_properties, "basename")

    #sufix
    suffix = release_suffix
    if not suffix: 
        suffix = get_yq(LOCAL_PATH_CHART + "/Chart.yaml", "name")

    return api_version + "-" + app_name + "-" + suffix


def build_values(app_name, release_name):

    if os.path.exists(LOCAL_CI_VALUES):
        os.remove(LOCAL_CI_VALUES)

    open(LOCAL_CI_VALUES, 'a').close()

    set_yq(LOCAL_CI_VALUES, "releaseName", release_name)
    set_yq(LOCAL_CI_VALUES, "image.repository", REPOSITORY)
    set_yq(LOCAL_CI_VALUES, "image.tag", TAG)

    set_yq(LOCAL_CI_VALUES, "AwsAccountId", AWS_ACCOUNT_ID)

    set_yq(LOCAL_CI_VALUES, "cd.commit", "TODO")
    set_yq(LOCAL_CI_VALUES, "cd.branch", "TODO")
    set_yq(LOCAL_CI_VALUES, "cd.basename", app_name)
    set_yq(LOCAL_CI_VALUES, "cd.reponame", "TODO")
    set_yq(LOCAL_CI_VALUES, "cd.group", "TODO")    

    

""" Funcoes para comandos HELM """
def build_release_status(deploy_name):
    cmd = ['helm'] + ['--namespace'] + [NAMESPACE] + ["status"] + [deploy_name] + ["-o"] + ["json"] 
    #print "COMANDO HELM: " + str(cmd)

    deploy_status_result = ""
    #try:
    #    deploy_status_result = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    #except subprocess.CalledProcessError, e:
    #    deploy_status_result = e.output

    deploy_status_result = deploy_status_result[:-1]

    global RELEASE_STATUS
    if "Error" in deploy_status_result:
        #possui erro
        RELEASE_STATUS = {'error':'true', 'status': deploy_status_result[7:]}
        if "release: not found" in deploy_status_result:
            return 1
        else:
            #TODO
            return 2
    else:
        #nao possui erro
        RELEASE_STATUS = {'error':'false', 'status': deploy_status_result}
        return 0


def exec_helm_template(release_name,name_override_cmd):
    if name_override_cmd:
        cmd = ["helm"]+["template"]+["-f"]+[LOCAL_CI_VALUES]+["-f"]+["./kubernetes/values.yaml"]+[release_name]+[LOCAL_PATH_CHART]+["--namespace"]+[NAMESPACE]+name_override_cmd
    else:
        cmd = ["helm"]+["template"]+["-f"]+[LOCAL_CI_VALUES]+["-f"]+["./kubernetes/values.yaml"]+[release_name]+[LOCAL_PATH_CHART]+["--namespace"]+[NAMESPACE]

    
    #print "COMANDO HELM: " + str(cmd)
    #subprocess.check_call(cmd)
    output = subprocess.check_output(cmd)
    #print ""

    return output.decode("utf-8")


def helm_delete(release_name):
    cmd = ["helm"]+["delete"]+[release_name]+["--namespace"]+[NAMESPACE]
    
    #print "COMANDO HELM: " + str(cmd)
    subprocess.check_call(cmd)
    print 


def helm_upgrade(release_name):
    # parent is not 0
    # child is 0
    i_am_parent = os.fork()

    if not i_am_parent:
        #print "PING"
        cmd = ["helm"]+["upgrade"]+["--install"]+["-f"]+[LOCAL_CI_VALUES]+["-f"]+["./kubernetes/values.yaml"]+[release_name]+[LOCAL_PATH_CHART]+["--namespace"]+[NAMESPACE]+["--wait"]+["--timeout"]+[HELM_TIMEOUT]#+["&"]
    
        #print "COMANDO HELM: " + str(cmd)
        subprocess.check_call(cmd)
    #else:
        #print "PONG"

"""
def generateHelmTemplate(release_name_override, release_suffix, app_properties):
    # Etapa 1: chegar estado atual
    # constoi o nome do deploy
    release_name = ""
    if release_name_override: 
        release_name = release_name_override
    else:
        release_name = get_release_name(release_suffix, app_properties)

    # Recupera nomes dentro do arquivo propeties no repo do ms
    app_name = get_yq(app_properties, "basename")
    group_name = get_yq(app_properties, "groupname")

    name_override_cmd = ""
    if app_name:
        name_override_cmd = ["--set-string"]+["nameOverride="+app_name]

    build_values(app_name, release_name)

    #print ""
    #print "Template a ser executado"
    template = exec_helm_template(release_name, name_override_cmd)

    return template

"""
def generateHelmRelease(release_name_override, release_suffix, app_properties, chart_repo):
    # TODO
    # Etapa 1: chegar estado atual
    # constoi o nome do deploy
    release_name = ""
    if release_name_override: 
        release_name = release_name_override
    else:
        release_name = get_release_name(release_suffix, app_properties)

    # Recupera nomes dentro do arquivo propeties no repo do ms
    app_name = get_yq(app_properties, "basename")
    group_name = get_yq(app_properties, "groupname")

    print (release_name)

    name_override_cmd = ""
    if app_name:
        name_override_cmd = ["--set-string"]+["nameOverride="+app_name]

    build_values(app_name)

    hrFile = release_name + "-hr.yaml"

    copyfile("helmReleaseTemplate.yaml", hrFile)

    open(hrFile, 'a').close()

    # Metadata informations
    set_yq(hrFile, "metadata.name", release_name)
    set_yq(hrFile, "metadata.namespace", NAMESPACE)

    # Spec Informations
    set_yq(hrFile, "spec.releaseName", release_name)
    set_yq(hrFile, "spec.chart.git", chart_repo)

    # spec.values
    set_yq(hrFile, "spec.values.image.repository", REPOSITORY)
    set_yq(hrFile, "spec.values.image.tag", TAG)

    #set_yq(LOCAL_CI_VALUES, "cd.commit", "TODO")
    #set_yq(LOCAL_CI_VALUES, "cd.branch", "TODO")
    #set_yq(LOCAL_CI_VALUES, "cd.basename", app_name)
    #set_yq(LOCAL_CI_VALUES, "cd.reponame", "TODO")
    #set_yq(LOCAL_CI_VALUES, "cd.group", "TODO")    

    return hrFile


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
    print ('usage: deploy.py -v init')
    print ('       deploy.py -v fetchchart          -c <chart_repo> [-b <chart_branch> -r <release_name_override>]')
    print ('       deploy.py -v generateHelmRelease -n <ns> -a <app_properties> -i <image_tag> -c <chart_repo>')
    print ('       deploy.py -v deploy              [-n <ns> -a <app_properties>]')
    sys.exit(1)


""" Variaveis Globais"""

# Path para clone do helm chart
LOCAL_PATH_CHART = "./curr_chart"
# Local do ci_default.yaml
LOCAL_CI_VALUES  = "./ci.values"
LOCAL_ARGOCDAPP  = "./linuxplace-deployer/src/ArgoCDApplication.yaml"
# Dicionario para armazenar status de deployment
RELEASE_STATUS = {}
#AWS Account
AWS_ACCOUNT_ID = ""
# Repositorio
REPOSITORY = ""
NAMESPACE = ""
# TAG
TAG = ""
HELM_TIMEOUT = "20s"


def get_aws_account_id():
    global AWS_ACCOUNT_ID

    sts = boto3.client('sts')
    resp = sts.get_caller_identity()

    AWS_ACCOUNT_ID = resp["Account"]

    if AWS_ACCOUNT_ID == "": 
        print ("Account ID nao encontrado.")
        erro(1)

    print ("Running in " + AWS_ACCOUNT_ID)


def get_repository_tag(image_name):
    global TAG
    global REPOSITORY

    # se variavel vazia
    if not image_name:
        TAG = "none"
        REPOSITORY = "none"
    else:
        # usa regex pra fazer split via ":"
        splited = re.split(":", image_name)
        REPOSITORY = splited[0]
        TAG = splited[1]

    print ("Repositorio:tag : " + REPOSITORY + ":" + TAG)


def main(argv):
    try:
        # https://www.tutorialspoint.com/python/python_command_line_arguments.htm
        opts, args = getopt.getopt(argv,"a:b:c:d:h:i:n:o:p:r:v:")
    except getopt.GetoptError:
        help()
    
    
    if len(argv) == 0:
        help()
    

    verb = ""
    chart_branch = "master"
    chart_repo = ""
    release_name_override = ""
    release_suffix = ""
    app_properties = ""
    argocd_repo = ""
    global NAMESPACE
    image_name = ""

    for opt, arg in opts:
        print (opt + " " + arg)
        if opt == "-a":
            app_properties = arg
        elif opt == "-b":
            chart_branch = arg
        elif opt == "-c":
            chart_repo = arg
        elif opt == "-d":
            argocd_repo = arg
        elif opt == "-h":
            help()
        elif opt == "-i":
            image_name = arg
        elif opt == "-n":
            NAMESPACE = arg
        elif opt == "-o":
            release_suffix = arg
        elif opt == "-p":
            project_name = arg
        elif opt == "-r":
            release_name_override = arg
        elif opt == "-v":
            verb = arg
        else: 
            print ("parametro incorreto")
            help()

    if verb == "init":
        init_key()

    elif verb == "fetchchart":
        # se vazio
        if not chart_repo:
            print ("parametro invalido")
            help()

        fetch_chart(chart_repo, chart_branch)

    elif verb == "generateAppArgoCD":
        if not NAMESPACE or not chart_repo or not release_name_override:
            print ("parametro invalido")
            help()

        generateApplicationArgoCD(chart_repo, release_name_override)


    elif verb == "generateHelmRelease":
        # se algum vazio
        if not app_properties or not NAMESPACE:
            print ("parametro invalido")
            help()

        get_repository_tag(image_name)

        hrFile = generateHelmRelease(release_name_override, release_suffix, app_properties, chart_repo)


    elif verb == "generateHelmTemplate":
        # se algum vazio
        if not app_properties or not NAMESPACE:
            print ("parametro invalido")
            help()

        get_aws_account_id()
        get_repository_tag(image_name)

        manifests = generateHelmTemplate(release_name_override, release_suffix, app_properties)

        save_to_file("manifests.yaml", manifests)


    elif verb == "saveArgoCDRepo":
        if not argocd_repo: 
            print ("parametro invalido")
            help()

        update_argo_repo(argocd_repo)


    elif verb == "":
        print ("verbo inexistente")
        help()


if __name__ == '__main__':
    main(sys.argv[1:])
