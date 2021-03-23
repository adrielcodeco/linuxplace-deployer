from utils.utils import *

def init_git():
	info = f"[user]\n\tname = LxP Deployer\n\temail = suporte@linuxplace.com.br"
	save_into_file("/root/.gitconfig", info)
	# command("git config --global user.email \"suporte@linuxplace.com.br\"; git config --global user.name \"LxP Deployer\"")

def fetch_repo(repo, path, branch="master"):
	alert(f"# Clonando repo {repo} em {path}", "yellow")
	if there_is_dir(path):
		old_path = pwd()
		chdir(path, imprime=False)
		git_pull()
		chdir(old_path, imprime=False)
	else:
		cmd = f"git clone {repo} -b {branch} {path}"
		command(cmd)

def get_last_tag():
	null, out = command(f"git describe --abbrev=0 --tag")
	return out

def there_is_modification():
	# esse comando lista alteracoes em arquivos, caso exista retorna sim
	null, out = command(f"git status --porcelain")
	alert(f"# Arquivos alterados:\n{out}", "yellow")
	if out:
		return True
	else:
		return False

def there_is_this_tag(tag_name):
	null, there_is = command(f"git tag -l {tag_name}")
	alert(f"# Output Git Tag: {there_is}.", "yellow")
	if there_is:
		alert(f"# Tag {tag_name} existe", "yellow")
		return True
	else:
		alert(f"# Tag {tag_name} nao existe", "yellow")
		return False

def git_add_all():
	command(f"git add -A")

def git_commit(msg):
	command(f"git commit -m '{msg}'")

def git_tag(name):
	command(f"git tag '{name}'")

def git_pull(branch="master"):
	command(f"git pull origin {branch}")
	alert(f"# git pull origin {branch} realizado", "yellow")

def git_checkout(target):
	command(f"git checkout {target}")

def git_push(branch="master"):
	arg = f"--tags"
	# commita
	return command(f"git push origin {branch} {arg}")

def add_and_push(msg, branch="master"):
	if there_is_modification():
		alert("# Repositorio com atualizacoes", "yellow")
		git_pull(branch=branch)
		git_add_all()
		git_commit(msg)
		ok, ret = git_push(branch=branch)
		if ok:
			alert(f"# Commit e Push feitos para origin {branch}", "yellow")
		else:
			alert(f"# Erro ao fazer commit e push", "red")
		return ok, ret
	else:
		alert("# Nao existe modificacoes e por isso nao exige acoes nesse repositorio", "yellow")
		return True, None


def add_and_push_with_tag(msg, tag, branch="master"):
	if there_is_modification():
		alert("# Repositorio com atualizacoes", "yellow")
		git_pull(branch=branch)
		git_add_all()
		git_commit(msg)
		git_tag(tag)
		ok, ret = git_push(branch=branch)
		if ok:
			alert(f"# Commit, Tag e Push feitos para origin {branch}", "yellow")
		else:
			alert(f"# Erro ao fazer commit, tag e push", "red")
		return ok, ret
	else:
		alert("# Nao existe modificacoes e por isso nao exige acoes nesse repositorio", "yellow")
		return True, None

def tag_and_push(msg, tag_name, branch="master"):
	git_pull(branch=branch)
	git_tag(tag_name)
	ok, ret = git_push(branch=branch)
	if ok:
		alert(f"# Tag e Push feitos para origin {branch}", "yellow")
	else:
		alert(f"# Erro ao fazer tag e push", "red")
	return ok, ret


