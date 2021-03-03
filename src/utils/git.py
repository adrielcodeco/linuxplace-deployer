from utils.utils import *

def init_git():
	info = f"[user]\n\tname = LxP Deployer\n\temail = suporte@linuxplace.com.br"
	save_into_file("/root/.gitconfig", info)
	# command("git config --global user.email \"suporte@linuxplace.com.br\"; git config --global user.name \"LxP Deployer\"")

def git_pull(branch="master"):
	command(f"git pull origin {branch}")

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

def git_add_all():
	command(f"git add -A")

def git_commit_and_push(msg, branch="master"):
	command(f"git commit -m '{msg}'")
	command(f"git push origin {branch}")

def add_and_push(msg, branch="master"):
	#alert(f"# Ultima tag da branch {branch}: {get_last_tag()}")
	if there_is_modification():
		alert("# Repositorio com atualizacoes", "yellow")
		git_add_all()
		git_commit_and_push(f"Deploy {msg}")
		alert(f"# Commit e Push feitos para origin {branch}", "yellow")
	else:
		alert("# Nao existe modificacoes e por isso nao exige acoes nesse repositorio", "yellow")
		return

# CLASS POC
class Git:
	last_tag = ""
	last_commit = ""

	def __init__(self):
		self.last_tag = self.get_last_tag()

	#git add
	#if [ -n "$(git status -uno --porcelain)" ]; then git add -A && git commit -m "Deploy ${release_name}" && git push origin master; else echo "Nada a commitar!"; fi

	#git new tag


	#git get last tag
	def get_last_tag(self):
		null, out = command(f"git describe --abbrev=0 --tag")
		return out


#git push