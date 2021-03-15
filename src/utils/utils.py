
import os, sys, getopt, shlex, re
from subprocess import PIPE, Popen
import json, boto3
from shutil import copyfile, rmtree

"""
Imprime mensgens na tela em formatos coloridos
"""
def alert(msg, color="green"):
	if color == "yellow":
		print(f"\033[93m{msg}\033[0m") #yellow
	elif color == "magenta":
		print(f"\033[95m{msg}\033[0m") #magenta
	elif color == "red":
		print(f"\033[91m\033[1m{msg}\033[0m") #red and bold
	else: # green
		print(f"\033[92m{msg}\033[0m") #green

"""
Executa comandos de sistemas
"""
def command(command, output=PIPE, sensitive=True):
	cmd = command
	try:
		if output == PIPE:
			run = Popen(shlex.split(cmd), stderr=PIPE, stdout=output)
			if sensitive:
				cmd = "XXX" # Limpa comando caso tenha variavel sensivel
			out, err = run.communicate()
			if run.returncode == 0:
				return True, out[:-1].decode("utf-8")
			else:
				alert(f"# Falha ao executar comando {cmd}, erro: {err}", "red")
				exit(1)
				#return False, err[:-1].decode("utf-8")
		else:
			with open(output, "a") as standard_out:
				run = Popen(shlex.split(cmd), stderr=PIPE, stdout=standard_out)
				if sensitive:
					cmd = "XXX" # Limpa comando caso tenha variavel sensivel
				run.communicate()
				if run.returncode == 0:
					return True
				else:
					alert(f"# Falha ao executar comando {cmd}, erro: {err}", "red")
					exit(1)
	except NameError as e:
		alert(f"\n# Erro ao executar {cmd}", "red")
		alert(e, "red")
		exit(1)
	except:
		if sensitive:
			alert("# Falha ao executar comando.", "red")
			exit(1)
		raise
"""
Copy and Paste
"""
def copia_e_cola(src, dst):
	try:
		copyfile(src, dst)
	except FileNotFoundError as e:
		alert(f"\n# Arquivos nao encontrados para copia", "red")
		alert(f"{e}", "red")
		exit(1)
	except:
		raise

"""
Regex
"""
def get_regex(reg, str):
	try:
		matches = re.findall(reg, str)
		return matches[0]
	except IndexError:
		alert(f"\n# Regex nao encontrou {reg} em {str}", "red")
	except:
		raise

def remove_regex(reg, str):
	try:
		matches = re.sub(reg,"", str, 1)
		return matches
	except IndexError:
		alert(f"\n# Regex nao encontrou {reg} em {str}", "red")
	except:
		raise

"""
Manipulacao de arquivos e diretorios
"""
def there_is_dir(path):
	return os.path.exists(path)

def rmdir(path):
	try:
		if os.path.exists(path):
			rmtree(path)
			alert(f"Diretorio {path} removido", "yellow")
	except:
		alert(f"\n# Erro ao remover diretorio {path}", "red")
		raise

def mkdir(path):
	try:
		if not os.path.exists(path):
			os.makedirs(path)
			alert(f"Diretorio {path} criado", "yellow")
	except:
		alert(f"Erro ao criar o diretorio {path}", "red")
		raise

def save_into_file(file_name, information, mode="w"):
	try:	
		file_pointer = open(file_name, mode)
		file_pointer.write(information)
		file_pointer.close()
	except:
		alert(f"Erro ao salvar no arquivo {file_name}", "red")
		raise

def read_from_file(file_name):
    try:
        file_pointer = open(file_name, "r")

        information = file_pointer.read()
        file_pointer.close()

        return information
    except:
        if file_pointer == "":
            alert(f"\n# Nao existe o arquivo {file_name} para ser lido", "red")
        raise

def get_yq(path_file, key):
	try:
		cmd = f"yq r {path_file} '{key}'"
		null, out = command(cmd)
		return out
	except:
		alert(f"\n# Erro no get yq: {cmd}", "yellow")
		raise

def delete_yq(path_file, key):
	cmd = f"yq d -i {path_file} '{key}'"
	command(cmd)

def set_yq(path_file, key, value, isList=False):
	if isList:
		cmd = f"yq w -i {path_file} '{key}[+]' '{value}'"
	else:
		cmd = f"yq w -i {path_file} '{key}' '{value}'"
	command(cmd)

def pwd():
	return os.getcwd()

def chdir(path, imprime=True):
	try:
		os.chdir(path)
		if imprime:
			alert(f"# Diretorio alterado para {os.getcwd()}", "yellow")
	except:
		alert(f"# Erro ao trocar para o diretorio {path}", "red")
		raise

def get_env_var(var_name):
	try:
		var = os.environ[var_name]
		alert(f"# Variavel {var_name} recuperada", "yellow")
		return var
	except:
		alert(f"# Variavel {var_name} nao recuperada", "red")
		raise

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
