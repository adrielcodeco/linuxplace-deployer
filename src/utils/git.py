from utils.utils import *
from random import randint
from time import sleep
from utils.constants import *

"""
Configura o arquivo .gitconfig com informacoes de usuario ssh
"""
def init_git():
	info = f"[user]\n\tname = LxP Deployer\n\temail = suporte@linuxplace.com.br"
	save_into_file("/root/.gitconfig", info)

"""
Executa git clone
"""
def fetch_repo(repo, path, branch="master"):
	alert(f"Clonando repo {repo} em {path}", "yellow")
	if there_is_dir(path):
		old_path = pwd()
		chdir(path, imprime=False)
		git_pull()
		chdir(old_path, imprime=False)
	else:
		cmd = f"git clone {repo} -b {branch} {path}"
		command(cmd)

"""
Retorna ultima tag do repositorio atual
"""
def get_last_tag():
	null, out = command(f"git describe --abbrev=0 --tag")
	return out

"""
Verifica se no repositorio atual existe alguma atualizacao de arquivo
"""
def there_is_modification():
	# esse comando lista alteracoes em arquivos, caso exista retorna sim
	null, out = command(f"git status --porcelain")
	alert(f"Arquivos alterados:\n{out}", "yellow")
	if out:
		return True
	else:
		return False

"""
Verifica se nesse repositorio existe a tag especifica
"""
def there_is_this_tag(tag_name):
	null, there_is = command(f"git tag -l {tag_name}")
	alert(f"Output Git Tag: {there_is}.", "yellow")
	if there_is:
		alert(f"Tag {tag_name} existe", "yellow")
		return True
	else:
		alert(f"Tag {tag_name} nao existe", "yellow")
		return False

"""
Commando interno git add
"""
def __git_add(args):
	return command(f"git add {args}")

"""
Commando interno git commit
"""
def __git_commit(msg):
	return command(f"git commit -m '{msg}'")

"""
Commando interno git tag
"""
def __git_tag(name):
	return command(f"git tag '{name}'")

"""
Commando interno git pull
"""
def __git_pull(args, branch="master"):
	alert(f"git pull origin {branch} realizando", "yellow")
	return command(f"git pull origin {branch} {args}")

"""
Commando interno git push
"""
def __git_push(branch="master"):
	arg = f"--tags"
	return command(f"git push origin {branch} {arg}")

"""
Commando git checkout
"""
def git_checkout(target):
	return command(f"git checkout {target}")


"""
Executa comando de add -A e commit
"""
def add_and_commit(msg):
	if there_is_modification():
		alert("Repositorio com atualizacoes", "yellow")
		__git_add("-A")
		__git_commit(msg)
	else:
		alert("Repositorio sem atualizacoes", "yellow")

"""
Define com tag
"""
def tag(tag_name):
	__git_tag(tag_name)

"""
Executa comando Pull
"""
def pull(rebase=False, branch="master"):
	if rebase == True:
		args = "--rebase"
	return __git_pull(args, branch)

"""
Commando git Push
"""
def push(rebase=False, retry=True, branch="master"):
	tries = 5
	ok = False
	while tries > 1 and not ok:
		if rebase:
			pull(rebase=True)
		ok, ret = __git_push(branch)
		if not ok:
			alert(f"Tentando pull e push novamente", "yellow")
			sleep(randint(1, 6))
			tries = tries - 1
	return ok, ret
