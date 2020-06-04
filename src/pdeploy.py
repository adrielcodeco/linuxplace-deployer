import os, sys, getopt, shlex
import subprocess

""" Variaveis Globais"""
LOCAL_PATH_CHART = "./curr_chart"
DEPLOYMENT_STATUS = {}


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



def yq(path_file, param):
    # monta a query
    cmd = ['yq'] + ['r'] + [path_file] + [param]
    #print "COMANDO YQ: " + str(cmd)
    # processa o comando e captura o resultado
    result = subprocess.check_output(cmd)

    # retira o \n no final 
    return result[:-1]


def get_release_name(release_suffix, app_properties):
    # prefix
    api_version = yq(app_properties, "apiVersion")

    # mid
    app_name = yq(app_properties, "basename")

    #sufix
    suffix = release_suffix
    if not suffix: 
        suffix = yq(LOCAL_PATH_CHART + "/Chart.yaml", "name")

    return api_version+"-"+app_name+"-"+suffix

    
def build_release_status(deploy_name, namespace):
    cmd = ['helm'] + ['--namespace'] + [namespace] + ["status"] + [deploy_name] + ["-o"] + ["json"] 
    #print "COMANDO HELM: " + str(cmd)

    deploy_status_result = ""
    try:
        deploy_status_result = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError, e:
        deploy_status_result = e.output

    deploy_status_result = deploy_status_result[:-1]

    global DEPLOYMENT_STATUS
    if "Error" in deploy_status_result:
        #possui erro
        DEPLOYMENT_STATUS = {'error':'true', 'status': deploy_status_result[7:]}
        if "release: not found" in deploy_status_result:
            return 1
        else:
            #TODO
            return 2
    else:
        #nao possui erro
        DEPLOYMENT_STATUS = {'error':'false', 'status': deploy_status_result}
        return 0



def helm_deploy(release_name_override, release_suffix, app_properties, namespace):
    # Etapa 1: chegar estado atual
    release_name = ""
    if release_name_override: 
        release_name = release_name_override
    else:
        release_name = get_release_name(release_suffix, app_properties)

    build_release_status(release_name, namespace)

    app_name = yq(app_properties, "basename")
    group_name = yq(app_properties, "groupname")

    name_override_cmd = ""
    if not app_name:
        name_override_cmd = "--set-string nameOverride="+app_name

    print ""
    print "Template a ser executado"
    exit (2)
    # Etapa 2: fazer um helm upgrade --install

    # Etapa 3: validar o deploy



""" ================== """

def help():
    print 'usage: deploy.py -v init'
    print '       deploy.py -v fetchchart -c <chart_repo> [-b <chart_branch> -r <release_name_override>]'
    print '       deploy.py -v deploy [-r <release_name_override> -o <release_suffix>]'
    sys.exit(1)


def main(argv):
    try:
        # https://www.tutorialspoint.com/python/python_command_line_arguments.htm
        opts, args = getopt.getopt(argv,"h:b:r:n:v:a:o:c:")
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
    namespace = ""

    for opt, arg in opts:
        print opt + " " + arg
        if opt == "-h":
            help()
        elif opt == "-v":
            verb = arg
        elif opt == "-c":
            chart_repo = arg
        elif opt == "-b":
            chart_branch = arg
        elif opt == "-a":
            app_properties = arg
        elif opt == "-r":
            release_name_override = arg
        elif opt == "-o":
            release_suffix = arg
        elif opt == "-n":
            namespace = arg
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
        if not app_properties or not namespace:
            print "parametro invalido"
            help()
        helm_deploy(release_name_override, release_suffix, app_properties, namespace)
    elif verb == "":
        print "verbo inexistente"
        help()


if __name__ == '__main__':
    main(sys.argv[1:])