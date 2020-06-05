#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, getopt, shlex, boto3, re
import subprocess
import jq


""" Funcao generica para uso de git
"""
def git(*args):
    return subprocess.check_call(['git'] + list(args))

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


def fetch_chart(repo, branch):
    git("clone", repo, "-b", branch, LOCAL_PATH_CHART)

""" ================== """



def get_yq(path_file, key):
    # monta a query
    cmd = ['yq'] + ['r'] + [path_file] + [key]
    #print "COMANDO YQ: " + str(cmd)
    # processa o comando e captura o resultado
    result = subprocess.check_output(cmd)

    # retira o \n no final 
    return result[:-1]


def get_release_name(release_suffix, app_properties):
    # prefix
    api_version = get_yq(app_properties, "apiVersion")

    # mid
    app_name = get_yq(app_properties, "basename")

    #sufix
    suffix = release_suffix
    if not suffix: 
        suffix = get_yq(LOCAL_PATH_CHART + "/Chart.yaml", "name")

    return api_version+"-"+app_name+"-"+suffix

    
def build_release_status(deploy_name):
    cmd = ['helm'] + ['--namespace'] + [NAMESPACE] + ["status"] + [deploy_name] + ["-o"] + ["json"] 
    #print "COMANDO HELM: " + str(cmd)

    deploy_status_result = ""
    try:
        deploy_status_result = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError, e:
        deploy_status_result = e.output

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

def set_yq(path_file, key, value):
    # monta a query
    cmd = ['yq'] + ['w'] + ['-i'] + [path_file] + [key] + [value]
    #print "COMANDO YQ: " + str(cmd)
    # processa o comando e captura o resultado
    subprocess.check_call(cmd)


def build_values(app_name):

    if os.path.exists(LOCAL_CI_VALUES):
        os.remove(LOCAL_CI_VALUES)

    open(LOCAL_CI_VALUES, 'a').close()

    set_yq(LOCAL_CI_VALUES, "image.repository", REPOSITORY)
    set_yq(LOCAL_CI_VALUES, "image.tag", TAG)

    set_yq(LOCAL_CI_VALUES, "AwsAccountId", AWS_ACCOUNT_ID)

    set_yq(LOCAL_CI_VALUES, "cd.commit", "TODO")
    set_yq(LOCAL_CI_VALUES, "cd.branch", "TODO")
    set_yq(LOCAL_CI_VALUES, "cd.basename", app_name)
    set_yq(LOCAL_CI_VALUES, "cd.reponame", "TODO")
    set_yq(LOCAL_CI_VALUES, "cd.group", "TODO")    


def helm_template(release_name,name_override_cmd):
    if name_override_cmd:
        cmd = ["helm"]+["template"]+["-f"]+[LOCAL_CI_VALUES]+["-f"]+["./kubernetes/values.yaml"]+[release_name]+[LOCAL_PATH_CHART]+["--namespace"]+[NAMESPACE]+name_override_cmd
    else:
        cmd = ["helm"]+["template"]+["-f"]+[LOCAL_CI_VALUES]+["-f"]+["./kubernetes/values.yaml"]+[release_name]+[LOCAL_PATH_CHART]+["--namespace"]+[NAMESPACE]

    
    print "COMANDO HELM: " + str(cmd)
    subprocess.check_call(cmd)
    print ""

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
        print "PING"
        cmd = ["helm"]+["upgrade"]+["--install"]+["-f"]+[LOCAL_CI_VALUES]+["-f"]+["./kubernetes/values.yaml"]+[release_name]+[LOCAL_PATH_CHART]+["--namespace"]+[NAMESPACE]+["--wait"]+["--timeout"]+[HELM_TIMEOUT]#+["&"]
    
        #print "COMANDO HELM: " + str(cmd)
        subprocess.check_call(cmd)
    else:
        print "PONG"

def get_jq(json, key):
    # TODO testar se ja tiver um deploy
    ret = ""
    try:
        print jq.first(key, json)
        ret = "trocar"
    except Exception as e:
        print "asdfk"
        ret = ""
    
    exit(0)
    # TODO
    return ret


def helm_deploy(release_name_override, release_suffix, app_properties):
    # Etapa 1: chegar estado atual
    # constoi o nome do deploy
    release_name = ""
    if release_name_override: 
        release_name = release_name_override
    else:
        release_name = get_release_name(release_suffix, app_properties)

    # Recupera o status do deploy atual, se tiver
    build_release_status(release_name)

    # Recupera nomes dentro do arquivo propeties no repo do ms
    app_name = get_yq(app_properties, "basename")
    group_name = get_yq(app_properties, "groupname")

    name_override_cmd = ""
    if app_name:
        name_override_cmd = ["--set-string"]+["nameOverride="+app_name]

    build_values(app_name)

    print ""
    print "Template a ser executado"
    #helm_template(release_name, name_override_cmd)

    # se ja existir um deploy com mas no estado de failed, remove-o
    # TODO testar quando tiver deploy antes
    if get_jq(RELEASE_STATUS['status'], "info.status") == "failed":
        print "Deletando o Deploy anterior que estava Failed"
        helm_delete(release_name)

    # Etapa 2: fazer um helm upgrade --install
    helm_upgrade(release_name)

    # Etapa 3: validar o deploy


    print "ESPERANDO"
    os.wait()
    exit(12)

""" ================== """

def help():
    print 'usage: deploy.py -v init'
    print '       deploy.py -v fetchchart -c <chart_repo> [-b <chart_branch> -r <release_name_override>]'
    print '       deploy.py -v deploy [-r <release_name_override> -o <release_suffix>]'
    sys.exit(1)


""" Variaveis Globais"""
# Path para clone do helm chart
LOCAL_PATH_CHART = "./curr_chart"
# Local do ci_default.yaml
LOCAL_CI_VALUES  = "./ci.values"
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

def init_deploy(image_name):
    global AWS_ACCOUNT_ID
    global TAG
    global REPOSITORY

    sts = boto3.client('sts')
    resp = sts.get_caller_identity()

    AWS_ACCOUNT_ID = resp["Account"]
    print "Running in " + AWS_ACCOUNT_ID
    
    # se variavel vazia
    if not image_name:
        TAG = "none"
        REPOSITORY = "none"
    else:
        # usa regex pra fazer split via ":"
        splited = re.split(":", image_name)
        REPOSITORY = splited[0]
        TAG = splited[1]


def main(argv):
    try:
        # https://www.tutorialspoint.com/python/python_command_line_arguments.htm
        opts, args = getopt.getopt(argv,"h:i:b:r:n:v:a:o:c:")
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
    global NAMESPACE
    image_name = ""

    for opt, arg in opts:
        print opt + " " + arg
        if opt == "-a":
            app_properties = arg
        elif opt == "-b":
            chart_branch = arg
        elif opt == "-c":
            chart_repo = arg
        elif opt == "-h":
            help()
        elif opt == "-i":
            image_name = arg
        elif opt == "-n":
            NAMESPACE = arg
        elif opt == "-o":
            release_suffix = arg
        elif opt == "-r":
            release_name_override = arg
        elif opt == "-v":
            verb = arg
        else: 
            print "parametro incorreto"
            help()

    if verb == "init":
        init_key()

    elif verb == "fetchchart":
        # se vazio
        if not chart_repo:
            print "parametro invalido"
            help()

        fetch_chart(chart_repo, chart_branch)

    elif verb == "deploy":
        # se algum vazio
        if not app_properties or not NAMESPACE:
            print "parametro invalido"
            help()

        init_deploy(image_name)

        helm_deploy(release_name_override, release_suffix, app_properties)

    elif verb == "":
        print "verbo inexistente"
        help()


if __name__ == '__main__':
    main(sys.argv[1:])