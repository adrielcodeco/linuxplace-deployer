
import os, sys, getopt, shlex, re
from subprocess import PIPE, Popen
import json
from shutil import copyfile

#TODO alterar os yq3

"""
Imprime mensgens na tela em formatos coloridos
"""
def alert(msg, color="green"):
	if color == "red":
		print(f"\033[91m\033[1m{msg}\033[0m") #red and bold
	else: # green
		print(f"\033[92m{msg}\033[0m") #green

"""
Executa comandos de sistemas
"""
def command(cmd, output=PIPE):
	try:
		if output == PIPE:
			run = Popen(shlex.split(cmd), stderr=PIPE, stdout=output)
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
				run.communicate()
				if run.returncode == 0:
					return True
				else:
					alert(f"# Falha ao executar comando {cmd}, erro: {err}", "red")
					exit(1)
					#return False
	except NameError as e:
		alert(f"\n# Erro ao executar {cmd}", "red")
		alert(e, "red")
		exit(1)
	except:
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
	if os.path.exists(path):
		os.remove(path)

def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def save_into_file(file_name, information, mode="w"):
	try:	
	    file_pointer = open(file_name, mode)
	    file_pointer.write(information)
	    file_pointer.close()
	except:
		raise

def read_from_file(file_name):
    try:
        file_pointer = open(file_name, "r")

        information = file_pointer.read()
        file_pointer.close()

        return information
    except:
        if file_pointer == "":
            alert(f"\n# Nao existe o arquivo {file_name} para ser lido.")
        raise

def get_yq(path_file, key):
	cmd = f"yq3 r {path_file} {key}"
	null, out = command(cmd)
	return out

	# yq2.12
	# cmd = ['yq'] + ['-y'] + ["." + key] + [path_file] + [" | head -n1"]
	# print "COMANDO YQ: " + str(cmd)
	# processa o comando e captura o resultado
	#result = subprocess.check_output(cmd)

	# retira o \n no final
	#return result[:-1].decode("utf-8")

def set_yq(path_file, key, value, key_base_path="", isList=False):
	# monta a query
	if isList:
		cmd = f"yq3 w -i {path_file} {key_base_path}.{key}[+] {value}"
	else:
		cmd = f"yq3 w -i {path_file} {key_base_path}.{key} {value}"

	alert(f"Comando a ser executado no set yq: {cmd}")

	command(cmd)

def pwd():
	return os.getcwd()

def chdir(path, imprime=True):
	try:
		os.chdir(path)
		if imprime:
			alert(f"# Diretorio alterado para {os.getcwd()}")
	except:
		raise

def get_env_var(var_name):
	return os.environ[var_name]

# def get_jq(json, key):
# 	# TODO testar se ja tiver um deploy
# 	ret = ""
# 	try:
# 		# print jq.first(key, json)
# 		ret = "trocar"
# 	except Exception as e:
# 		# print "asdfk"
# 		ret = ""
#
# 	return ret
