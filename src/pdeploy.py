import os, sys, getopt 
import subprocess

""" Variaveis Globais"""
LOCAL_PATH_CHART = "./curr_chart"


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



def cat_yq(param, file, path=LOCAL_PATH_CHART):
    
    #file = os.popen('cat '+ path + file).read()

    #cmd = ['cat'] + [path + file] + [" | yq -r ."+ param]
    #cmd = ['cat'] + [path + file ] #+ " | yq -r ."+ param]
    cmd = ['cat'] + [path + file] + ['|']+ ['grep'] + ['name']
    print cmd
    a = subprocess.check_call(cmd, shell=True)
    #list_files = subprocess.run(["ls", "-l"])


def get_release_name(release_suffix):
    cat_yq("name", "/Chart.yaml")
    

def helm_deploy(release_name_override, release_suffix):

    # Etapa 1: chegar estado atual
    if release_name_override: 
        release_name = release_name_override
    else:
        release_name = get_release_name(release_suffix)
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
        opts, args = getopt.getopt(argv,"h:b:r:v:o:c:")
    except getopt.GetoptError:
        help()

    if len(argv) == 0:
        help()
    
    verb = ""
    chart_branch = "master"
    chart_repo = ""
    release_name_override = ""
    release_suffix = ""

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
        elif opt == "-r":
            release_name_override = arg
        elif opt == "-o":
            release_suffix = arg
        else: 
            print "parametro incorreto"
            help()

    if verb == "init":
        init_key()
    elif verb == "fetchchart":
        if chart_repo == "":
            print "parametro -c invalido"
            help()
        fetch_chart(chart_repo, chart_branch)
    elif verb == "deploy":
        helm_deploy(release_name_override, release_suffix)
    elif verb == "":
        print "verbo inexistente"
        help()


if __name__ == '__main__':
    main(sys.argv[1:])