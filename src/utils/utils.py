import os, sys, getopt, shlex, re
from subprocess import PIPE, Popen
import json, boto3
from utils.constants import *
from shutil import copyfile, rmtree

"""
Imprime mensgens na tela em formatos padronizados
"""
def alert(msg, color="white"):
	DEFAULT  = "\033[0m"
	NEGRITO  = "\033[1m"
	AMARELO  = "\033[93m"
	MAGENTA  = "\033[95m"
	VERMELHO = "\033[91m"
	VERDE    = "\033[92m"
	BRANCO   = "\033[37m"
	# prefix em todos os logs
	prefix = "# "
	#TODO definir variavel debug por parametro
	DEBUG = 1

	# Mensagens amarelas soh serao impressas com DEBUG > 1
	if color == "yellow" and DEBUG >= 1:
		print(f"{AMARELO}{prefix}DEBUG {msg}{DEFAULT}") #yellow
	elif color == "magenta":
		print(f"{MAGENTA}{prefix}{msg}{DEFAULT}") #magenta
	elif color == "red":
		print(f"\n{VERMELHO}{NEGRITO}{prefix}{msg}{DEFAULT}") #red and bold
	elif color == "green":
		print(f"{VERDE}{NEGRITO}{prefix}{msg}{DEFAULT}") #green and bold
	else: # white
		print(f"{BRANCO}{prefix}{msg}{DEFAULT}")

"""
Executa comandos de sistemas e retorna.
OBS: esse comando nao fara exit() caso erro.
"""
def command(command, output=PIPE, sensitive=False):
	cmd = command
	try:
		if output == PIPE:
			run = Popen(shlex.split(cmd), stderr=PIPE, stdout=output)
			if sensitive:
				cmd = "<<Sensive>>" # Limpa comando caso tenha variavel sensivel
			out, err = run.communicate()
			if run.returncode == 0:
				return True, out[:-1].decode("utf-8")
			else:
				alert(f"O comando '{cmd}' retornou o erro {err}", "red")
				return False, err[:-1].decode("utf-8")
		else:
			with open(output, "a") as standard_out:
				run = Popen(shlex.split(cmd), stderr=PIPE, stdout=standard_out)
				if sensitive:
					cmd = "<<Sensive>>" # Limpa comando caso tenha variavel sensivel
				run.communicate()
				if run.returncode == 0:
					return True
				else:
					alert(f"Falha ao executar comando {cmd}, erro: {err}", "red")
					exit(1)
	except NameError as e:
		alert(f"Erro ao executar {cmd}", "red")
		alert(e, "red")
		exit(1)
	except:
		if sensitive:
			alert("Falha ao executar comando.", "red")
			exit(1)
		raise

"""
Copia uma arquivo de um diretorio para outro
"""
def copia_e_cola(src, dst):
	try:
		copyfile(src, dst)
	except FileNotFoundError as e:
		alert(f"Arquivos nao encontrados para copia", "red")
		alert(f"{e}", "red")
		exit(1)
	except:
		raise

"""
Regex sobre uma string
"""
def get_regex(reg, str):
	try:
		matches = re.findall(reg, str)
		return matches[0]
	except IndexError:
		alert(f"Regex nao encontrou {reg} em {str}", "red")
	except:
		raise

"""
Remove baseado em Regex
"""
def remove_regex(reg, str):
	try:
		matches = re.sub(reg,"", str, 1)
		return matches
	except IndexError:
		alert(f"Regex nao encontrou {reg} em {str}", "red")
	except:
		raise

"""
Manipulacao de arquivos e diretorios
"""
"""
Verifica se o diretorio existe
"""
def there_is_dir(path):
	return os.path.exists(path)

"""
Executa comando ls
"""
def ls(path="", args=""):
	alert(f"Executando ls {path}", "yellow")
	ok, out = command(f"ls {args} {path}")
	alert(out)

"""
Executa comando de rm -rf
"""
def rmdir(path):
	try:
		if os.path.exists(path):
			rmtree(path)
			alert(f"Diretorio {path} removido", "yellow")
	except:
		alert(f"Erro ao remover diretorio {path}", "red")
		raise

"""
Executa comando de mkdir
"""
def mkdir(path):
	try:
		if not os.path.exists(path):
			os.makedirs(path)
			alert(f"Diretorio {path} criado", "yellow")
	except:
		alert(f"Erro ao criar o diretorio {path}", "red")
		raise

"""
Salva informacao passada por parametro em arquivo
"""
def save_into_file(file_name, information, mode="w"):
	try:	
		file_pointer = open(file_name, mode)
		file_pointer.write(information)
		file_pointer.close()
	except:
		alert(f"Erro ao salvar no arquivo {file_name}", "red")
		raise

"""
Leh informacao de arquivo e retorna 
"""
def read_from_file(file_name):
    try:
        file_pointer = open(file_name, "r")
        information = file_pointer.read()
        file_pointer.close()
        return information
    except:
        if file_pointer == "":
            alert(f"Nao existe o arquivo {file_name} para ser lido", "red")
        raise

"""
Executa comando pwd
"""
def pwd():
	try:
		return os.getcwd()
	except:
		raise

"""
Muda o diretorio no Runner
"""
def chdir(path, imprime=True):
	try:
		os.chdir(path)
		if imprime:
			alert(f"Diretorio alterado para {os.getcwd()}", "yellow")
	except:
		alert(f"#Erro ao trocar para o diretorio {path}", "red")
		raise

"""
Busca informacao da variavel de ambiente do Runner
"""
def get_env_var(var_name):
	try:
		var = os.environ[var_name]
		alert(f"Variavel {var_name} recuperada", "yellow")
		return var
	except:
		alert(f"Variavel {var_name} nao recuperada", "red")
		raise

"""
Busca informacao em um arquivo .yaml
"""
def get_yq(path_file, key):
	try:
		cmd = f"yq r {path_file} '{key}'"
		null, out = command(cmd)
		return out
	except:
		alert(f"Erro no get yq: {cmd}", "yellow")
		raise

"""
Remove informacao de um arquivo .yaml
"""
def delete_yq(path_file, key):
	try:
		cmd = f"yq d -i {path_file} '{key}'"
		command(cmd)
	except:
		alert(f"Erro no delete yq: {cmd}", "yellow")
		raise

"""
Escreve em aquivo .yaml
"""
def set_yq(path_file, key, value, isList=False):
	try:
		if isList:
			cmd = f"yq w -i {path_file} '{key}[+]' '{value}'"
		else:
			cmd = f"yq w -i {path_file} '{key}' '{value}'"
		command(cmd)
	except:
		alert(f"Erro no set yq: {cmd}", "yellow")
		raise

"""
Busca a informacao de conta AWS
"""
def get_aws_account_id():
	sts = boto3.client('sts')
	resp = sts.get_caller_identity()

	aws_account_id = resp["Account"]

	if aws_account_id == "":
		alert("Account ID nao encontrado.", "red")
		erro(1)
	else:
		alert(f"Account ID: {aws_account_id}", "yellow")

	return aws_account_id
