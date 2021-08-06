from utils.utils import *
from utils.constants import *
from utils.git import *

"""
Class que possui informacoes e metodos relativos ao deploy e undeploy
"""
class Deploy:
    release_name = ""
    basename = ""
    api_version = ""
    group = ""
    values = {}
    pod_name = ""
    events = {}
    ns = ""
    microservice = ""
    CI_COMMIT_SHORT_SHA = ""
    tag_name = ""
    ARGOCD_AUTH_TOKEN = ""
    ARGOCD_SERVER = "argocd-server.argocd.svc.cluster.local"

    """
    Cria um TAG NAME
    """
    def create_tag_name(self):
        tag_name = f"{self.release_name}-{self.ns}-{self.CI_COMMIT_SHORT_SHA}"
        alert(f"Tag name: {tag_name}", "yellow")
        return tag_name

    """
    Instancia a classe do deploy com as informacoes basicas
    """
    def __init__(self, release_suffix, app_properties, ns, microservice=""):
        alert(f"Instanciando o Deploy")

        self.ns = ns
        self.microservice = microservice
        self.basename =    get_yq(app_properties, "basename")
        self.api_version = get_yq(app_properties, "apiVersion")
        self.group =       get_yq(app_properties, "group")
        self.CI_COMMIT_SHORT_SHA = get_env_var("CI_COMMIT_SHORT_SHA")
        self.ARGOCD_AUTH_TOKEN = get_env_var("ARGOCD_AUTH_TOKEN_"+self.ns.upper())
        self.release_name = self.set_release_name(release_suffix)
        self.tag_name = self.create_tag_name()

        alert(f"Microsservico: {self.release_name} no ambiente {self.ns}")
        alert(f"Tag name: {self.tag_name}")
        alert(f"Instancia construida")

    """
    Configura o nome do releaseName
    """
    def set_release_name(self, release_suffix):
        api_version = self.api_version
        app_name = self.basename
        if not release_suffix:
            alert(f"release_suffix nao definido", "yellow")
            suffix = get_yq(f"{LOCAL_PATH_APPS}/ms-chart/Chart.yaml", "name")
        else:
            alert(f"release_suffix definido {release_suffix}", "yellow")
            suffix = release_suffix
        return f"{api_version}-{app_name}-{suffix}"

    """
    Recupera o releaseName
    """
    def get_release_name(self):
        return self.release_name

    """
    Verifica se existe mapa applications no yaml esta vazio
    Se sim, deleta o mapa por completo
    """
    # TODO Possivel de ser enviado para o git.py
    def verify_empty_applications_map(self, values_path):
        names = get_yq(values_path, 'applications[*].name')
        alert(f"Lista do .applications\n{names}", "yellow")
        if names == "":
            delete_yq(values_path, "applications")
            alert(f"Mapa .applications removido", "yellow")

    """
    Metodo que deleta um ms do repositorio app_config
    """
    def delete_app_config(self):
        alert(f"Iniciando configuracao do App Config Repo")
        old_path = pwd()
        chdir(f"{LOCAL_PATH_APPS}")

        # remove o direotorio inteiro
        rmdir(f"{self.ns}/{self.release_name}-{self.ns}")

        # publica as alteracoes
        add_and_commit(f"UnDeploy {self.release_name} {self.ns}")
        ok, ret = push(rebase=True)
        if not ok:
            alert(f"Erro ao executar push")
            exit(1)
        chdir(old_path)
        alert(f"Repositorio App Config configurado")

    """
    Verifica se jah existe uma tag no repositorio api_config
    """
    def there_is_tag_ms_config(self):
        old_path = pwd()
        chdir(f"{LOCAL_PATH_MS_CONFIG}")

        there_is_tag = there_is_this_tag(self.tag_name)
        if there_is_tag:
            # se tem a tag, faz git checkout para ela
            git_checkout(self.tag_name)
        else:
            # caso contrario, cria a tag no repo api_config
            tag(self.tag_name)
            ok, out = push(f"Deploy {self.release_name} {self.ns}")
            if not ok:
                alert(f"Erro ao executar push")
                exit(1)

        chdir(old_path)

    """
    Define variaveis de Continous Delivery no arquivo values.yaml
    """
    # TODO Conferir
    def set_cd_vars(self, file):
        set_yq(file, "cd.commit", get_env_var("CI_COMMIT_SHA"))
        set_yq(file, "cd.branch", get_env_var("CI_COMMIT_REF_NAME"))
        set_yq(file, "cd.basename", self.basename)
        set_yq(file, "cd.reponame", get_env_var("CI_PROJECT_NAME"))
        set_yq(file, "cd.group", self.group)

    """
    Cria uma nova configuracao no repositorio app_config com o values.yaml
    do ms a ser publicado.
    Se jah existir uma tag, reutiliza-a
    """
    def create_app_config(self):
        alert(f"Iniciando configuracao do App Config Repo")
        # Checa se ja existe tag no repo api_configs
        if self.ns != "dev":
            alert("Checando tag no repositorio api_configs", "yellow")
            # Se existir, realiza git checkout no api_configs para a tag
            self.there_is_tag_ms_config()
        else:
            alert("Ambiente dev nao utiliza repositorio api_configs, pulando checagem de tag", "yellow")

        old_path = pwd()
        chdir(f"{LOCAL_PATH_APPS}")

        # Verifica se existe tag nesse reposito app_config
        if there_is_this_tag(self.tag_name):
            # Se sim, muda para a tag e reutiliza-a
            git_checkout(self.tag_name)
            # Checa se existe algum deploy ja com essa tag pois pode ser uma tag de deploy antigo
            alert(f"Deploy encontrado no historico de tags do repositorio app-config, reutilizando ({self.tag_name})", )
        else:
            # caso contrario, cria uma tag nova com informacoes novas
            mkdir(f"{self.ns}/{self.release_name}-{self.ns}")
            # Se for da branch dev
            if self.ns == "dev":
                # copia o arquivo values.yaml de dentro do proprio projeto
                if self.microservice == "":
                    copia_e_cola(f"../kubernetes/values.yaml", f"{self.ns}/{self.release_name}-{self.ns}/values.yaml")
                else:
                    alert(f"Executando copia de values do package {self.microservice} de dentro do projeto", "yellow")
                    copia_e_cola(f"../packages/{self.microservice}/kubernetes/values.yaml", f"{self.ns}/{self.release_name}-{self.ns}/values.yaml")
            else:
                # Se for de hml ou prd, copia do repositorio api_config
                alert(f"Deploy nao encontrado no historico de tags do repositorio app-config, criando uma tag nova ({self.tag_name})")
                alert(f"Copiando values.yaml do {LOCAL_PATH_MS_CONFIG}/{self.basename}/{self.ns}/kubernetes/values.yaml")
                copia_e_cola(f"../{LOCAL_PATH_MS_CONFIG}/{self.basename}/{self.ns}/kubernetes/values.yaml",
                             f"{self.ns}/{self.release_name}/values.yaml")

            # adiciona o account id no values
            set_yq(f"{self.ns}/{self.release_name}-{self.ns}/values.yaml", "AwsAccountId", get_aws_account_id())
            # Adiciona informacoes de CD no values
            self.set_cd_vars(f"{self.ns}/{self.release_name}-{self.ns}/values.yaml")
            # Publica as alteracoes
            add_and_commit(f"Deploy {self.release_name} {self.ns}")
            tag(self.tag_name)
            ok, ret = push(rebase=True)
            if not ok:
                alert(f"Erro ao executar push")
                exit(1)
        chdir(old_path)
        alert(f"Repositorio App Config configurado")

    """
    Deleta um deploy do reposiorio argocd
    """
    def delete_argocd_config(self):
        alert(f"Iniciando configuracao do ArgoCD Repo")
        old_path = pwd()
        path_to_values = f"{LOCAL_PATH_ARGOCD}/{self.ns}"
        chdir(f"{path_to_values}")

        # confere se o deploy existe no yaml de configuracao, se sim
        # deleta-o
        there_is_deploy = get_yq(f"values.yaml", f"'applications.(name=={self.release_name}-{self.ns}).name'")
        if there_is_deploy:
            delete_yq("values.yaml", f"applications.(name=={self.release_name}-{self.ns})")
            # https://github.com/mikefarah/yq/issues/493

        # Caso o mapa 'applicatinos' no .yaml tenha ficado vazio, elimina-o tambem
        self.verify_empty_applications_map("values.yaml")
        # Publica as alteracoes
        add_and_commit(f"UnDeploy {self.release_name} {self.ns}")
        ok, ret = push(rebase=True)
        if not ok:
            alert(f"Erro ao executar push")
            exit(1)
        chdir(old_path)
        alert(f"ArgoCD Repo configurado")


    """
    Adiciona informacoes no repositorio argocd
    """
    def add_argocd_config(self):
        alert(f"Iniciando configuracao do ArgoCD Repo")
        old_path = pwd()
        path_to_values = f"{LOCAL_PATH_ARGOCD}/{self.ns}"
        chdir(f"{path_to_values}")

        # verifica se existe alguma publicacao deste ms
        there_is_deploy = get_yq(f"values.yaml", f"'applications.(name=={self.release_name}-{self.ns}).name'")
        if there_is_deploy:
            # se sim somente reescreve sobre o mapa
            set_yq("values.yaml", f"applications.(name=={self.release_name}-{self.ns}).name", f"{self.release_name}-{self.ns}")
        else:
            # caso contrario cria um novo
            set_yq("values.yaml", f"applications[+].name", f"{self.release_name}-{self.ns}")

        # adiciona as outras informacoes basicas para configuracao do mapa
        set_yq("values.yaml", f"applications.(name=={self.release_name}-{self.ns}).namespace", f"{self.ns}")
        set_yq("values.yaml", f"applications.(name=={self.release_name}-{self.ns}).releaseName", f"{self.release_name}")
        set_yq("values.yaml", f"applications.(name=={self.release_name}-{self.ns}).source.targetRevision", f"{self.tag_name}")
        set_yq("values.yaml", f"applications.(name=={self.release_name}-{self.ns}).source.path", f"ms-chart")
        set_yq("values.yaml", f"applications.(name=={self.release_name}-{self.ns}).source.repoURL",
               f"git@gitlab.com:u4crypto/devops/aplicacoes/app-configs.git")

        # Publica as alteracoes
        add_and_commit(f"Deploy {self.release_name} {self.ns}")
        ok, ret = push(rebase=True)
        if not ok:
            alert(f"Erro ao executar push")
            exit(1)
        chdir(old_path)
        alert(f"ArgoCD Repo configurado")

    """
    Conecta no ArgoCD via auth-token e estimula um sync no projeto AMBIENTE
    """
    def sync(self):
        alert(f"Iniciando ArgoCD Sync")
        general_flags = f"--insecure --server {self.ARGOCD_SERVER} --auth-token {self.ARGOCD_AUTH_TOKEN}"
        alert("Executando ArgoCD Sync", "yellow")
        command(f"argocd app sync {self.ns}-apps --prune {general_flags}")
        alert(f"Para verificar o status, faca login no U4CRYPTO-SHARED-CLUSTER, execute o comando abaixo para verificar "
              f"o status do Deploy, e depois abra no seu navegador o endereco https://localhost:8080/", "yellow")
        alert(f"$ kubectl port-forward svc/argocd-server -n argocd 8080:443", "yellow")

    """
    Metodo invocativo para deploy
    """
    def deploy_argocd(self):
        self.create_app_config()
        self.add_argocd_config()
        self.sync()

    """
    Metodo invocativo para undeploy
    """
    def undeploy_argocd(self):
        self.delete_app_config()
        self.delete_argocd_config()
        self.sync()
