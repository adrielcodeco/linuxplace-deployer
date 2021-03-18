from utils.utils import *
from utils.constants import *
from utils.git import *

class Deploy:
    release_name = ""
    basename = ""
    values = {}
    pod_name = ""
    events = {}
    ns = ""
    argocd_timeout = 300
    CI_COMMIT_SHORT_SHA = ""
    tag_name = ""


    def create_app_config_tag_name(self):
        tag_name = f"{self.release_name}-{self.ns}-{self.CI_COMMIT_SHORT_SHA}"
        alert(f"# Tag name: {tag_name}", "yellow")
        return tag_name

    def __init__(self, release_suffix, app_properties, ns):
        alert(f"\n# Instanciando o Deploy", "green")
        self.release_name = self.set_release_name(release_suffix, app_properties)
        self.ns = ns
        self.basename = get_yq(app_properties, "basename")
        self.CI_COMMIT_SHORT_SHA = get_env_var("CI_COMMIT_SHORT_SHA")
        self.tag_name = self.create_app_config_tag_name()

        alert(f"# Microsservico: {self.release_name} no ambiente {self.ns}")
        alert(f"# Tag name: {self.tag_name}")
        alert(f"# Instancia construida", "green")

    def set_release_name(self, release_suffix, app_properties):
        api_version = get_yq(app_properties, "apiVersion")
        app_name = get_yq(app_properties, "basename")
        if not release_suffix:
            suffix = get_yq(f"{LOCAL_PATH_APPS}/ms-chart/Chart.yaml", "name")
        else:
            suffix = release_suffix
        return f"{api_version}-{app_name}-{suffix}"

    def get_release_name(self):
        return self.release_name

    def verify_empty_applications_map(self, values_path):
        names = get_yq(values_path, 'applications[*].name')
        alert(f"# Lista do .applications\n{names}", "yellow")
        if names == "":
            delete_yq(values_path, "applications")
            alert(f"# Mapa .applications removido", "yellow")

    def delete_app_config(self):
        alert(f"\n# Iniciando configuracao do App Config Repo")
        old_path = pwd()
        chdir(f"{LOCAL_PATH_APPS}")

        rmdir(f"{self.ns}/{self.release_name}")

        add_and_push(f"UnDeploy {self.release_name} {self.ns}")
        chdir(old_path)
        alert(f"# Repositorio App Config configurado")

    def there_is_tag_ms_config(self):
        old_path = pwd()
        chdir(f"{LOCAL_PATH_MS_CONFIG}")
        there_is_tag = there_is_this_tag(self.tag_name)

        if there_is_tag:
            git_checkout(self.tag_name)
        else:
            tag_and_push(f"Deploy {self.release_name} {self.ns}", self.tag_name)

        chdir(old_path)

    def create_app_config(self):
        alert(f"\n# Iniciando configuracao do App Config Repo", "green")

        self.there_is_tag_ms_config()

        old_path = pwd()
        chdir(f"{LOCAL_PATH_APPS}")
        mkdir(f"{self.ns}/{self.release_name}")

        if self.ns == "dev":
            copia_e_cola(f"../kubernetes/values.yaml", f"{self.ns}/{self.release_name}/values.yaml")
        else:
            # Checa se existe algum deploy ja com essa tag pois pode ser uma tag de deploy antigo
            if there_is_this_tag(self.tag_name):
                git_checkout(self.tag_name)
                alert(f"# Deploy encontrado no historico de tags do repositorio app-config, reutilizando ({self.tag_name})",)
                return
            else:
                alert(f"# Deploy nao encontrado no historico de tags do repositorio app-config, criando uma tag nova ({self.tag_name})")
                alert(f"# Copiando values.yaml do {LOCAL_PATH_MS_CONFIG}/{self.basename}/{self.ns}/kubernetes/values.yaml")
                ls()
                ls("..")
                ls(f"../{LOCAL_PATH_MS_CONFIG}")
                ls(f"../{LOCAL_PATH_MS_CONFIG}/{self.basename}")
                ls(f"../{LOCAL_PATH_MS_CONFIG}/{self.basename}/{self.ns}")
                ls(f"../{LOCAL_PATH_MS_CONFIG}/{self.basename}/{self.ns}/kubernetes")
                copia_e_cola(f"../{LOCAL_PATH_MS_CONFIG}/{self.basename}/{self.ns}/kubernetes/values.yaml",
                             f"{self.ns}/{self.release_name}/values.yaml")

        # adiciona o account id no values
        set_yq(f"{self.ns}/{self.release_name}/values.yaml", "AwsAccountId", get_aws_account_id())
        add_and_push_with_tag(f"Deploy {self.release_name} {self.ns}", self.tag_name)
        chdir(old_path)
        alert(f"# Repositorio App Config configurado", "green")

    def delete_argocd_config(self):
        alert(f"\n# Iniciando configuracao do ArgoCD Repo", "green")
        old_path = pwd()
        path_to_values = f"{LOCAL_PATH_ARGOCD}/{self.ns}"
        chdir(f"{path_to_values}")
        # verifica se existe ja
        there_is_deploy = get_yq(f"values.yaml", f"'applications.(name=={self.release_name}-{self.ns}).name'")

        if there_is_deploy:
            #cmd = f"yq d -i values.yaml 'applications.(name=={self.release_name}).name'"
            delete_yq("values.yaml", f"applications.(name=={self.release_name}-{self.ns})")
            # https://github.com/mikefarah/yq/issues/493

        self.verify_empty_applications_map("values.yaml")
        add_and_push(f"UnDeploy {self.release_name} {self.ns}")

        chdir(old_path)
        alert(f"# ArgoCD Repo configurado", "green")

    def add_argocd_config(self):
        alert(f"\n# Iniciando configuracao do ArgoCD Repo", "gren")
        old_path = pwd()
        path_to_values = f"{LOCAL_PATH_ARGOCD}/{self.ns}"
        chdir(f"{path_to_values}")
        # verifica se existe ja
        there_is_deploy = get_yq(f"values.yaml", f"'applications.(name=={self.release_name}-{self.ns}).name'")

        if there_is_deploy:
            # se sim so reescreve sobre o mapa
            # yq w -i values.yaml 'applications.(name==v1-api-u4c-YYY-master).name' 'v1-api-u4c-XXXYYY-master'
            #cmd = f"yq w -i values.yaml 'applications.(name=={self.release_name}).name' '{self.release_name}'"
            set_yq("values.yaml", f"applications.(name=={self.release_name}-{self.ns}).name", f"{self.release_name}-{self.ns}")
        else:
            # caso contrario cria um novo
            # yq w -i values.yaml 'applications[+].name' 'v1-api-u4c-rodolfo-master'
            #cmd = f"yq w -i values.yaml 'applications[+].name' '{self.release_name}'"
            set_yq("values.yaml", f"applications[+].name", f"{self.release_name}-{self.ns}")

        #cmd = f"yq w -i values.yaml 'applications.(name=={self.release_name}).namespace' '{self.ns}'"
        set_yq("values.yaml", f"applications.(name=={self.release_name}).namespace", f"{self.ns}")
        #cmd = f"yq w -i values.yaml 'applications.(name=={self.release_name}).source.targetRevision' 'HEAD'"
        set_yq("values.yaml", f"applications.(name=={self.release_name}).source.targetRevision", f"{self.tag_name}")
        #cmd = f"yq w -i values.yaml 'applications.(name=={self.release_name}).source.path' 'ms-chart'"
        set_yq("values.yaml", f"applications.(name=={self.release_name}).source.path", f"ms-chart")
        #cmd = f"yq w -i values.yaml 'applications.(name=={self.release_name}).source.repoURL'
        # 'git@gitlab.com:u4crypto/devops/aplicacoes/app-configs.git'"
        set_yq("values.yaml", f"applications.(name=={self.release_name}).source.repoURL",
               f"git@gitlab.com:u4crypto/devops/aplicacoes/app-configs.git")

        add_and_push(f"Deploy {self.release_name} {self.ns}")
        chdir(old_path)
        alert(f"# ArgoCD Repo configurado", "green")

    def sync(self):
        #alert(f"\n# Iniciando ArgoCD Sync", "yellow")
        #env = string.upper(self.ns)
        #token = get_env_var(f"ARGOCD_TOKEN_{env}_PROJECT")
        #flags = f"--prune --timeout {self.argocd_timeout} --insecure --auth-token {token}"
        #command(f"argocd app sync {self.release_name} {flags}", sensitive=True)
        #flags = token = None
        #alert(f"# ArgoCD sincronizado, execute o comando abaixo para verificar o status do Deploy:")
        alert(f"# Para verificar o status, faca login no U4CRYPTO-SHARED-CLUSTER, execute o comando abaixo para verificar "
              f"o status do Deploy, e depois abra no seu navegador o endereco https://localhost:8080/", "yellow")
        alert(f"$ kubectl port-forward svc/argocd-server -n argocd 8080:443", "yellow")

    def deploy_argocd(self):
        self.create_app_config()
        self.add_argocd_config()
        self.sync()

    def undeploy_argocd(self):
        self.delete_app_config()
        self.delete_argocd_config()
        self.sync()
