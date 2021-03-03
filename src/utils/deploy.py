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

    def __init__(self, release_suffix, app_properties, ns):
        alert(f"\n# Instanciando o Deploy")
        self.release_name = self.set_release_name(release_suffix, app_properties)
        self.ns = ns
        self.basename = get_yq(app_properties, "basename")
        alert(f"\n# Microsservico: {self.release_name} no ambiente {self.ns}")
        alert(f"\n# Instancia construida")

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

    def create_app_config(self):
        alert(f"\n# Iniciando configuracao do App Config Repo")
        old_path = pwd()
        chdir(f"{LOCAL_PATH_APPS}")
        mkdir(f"{self.ns}/{self.release_name}")

        # TODO situacao o 0 deploys finais

        if self.ns == "dev":
            copia_e_cola(f"../kubernetes/values.yaml", f"{self.ns}/{self.release_name}/values.yaml")
        else:
            alert(f"\n#BETA: Deploy em hml e prd ainda nao concluido", "red")
            exit(1)
            # TODO SE FOR HML E PRD USA O COPIA E COLA, DEV NAO USA
            # TODO Alterar o path ../.. pos eu coloquei o temp nos globais
            # copia_e_cola(f"../../{LOCAL_PATH_MS_CONFIG}/{self.basename}/{self.ns}/kubernetes/values.yaml",
            #             f"{self.ns}/{self.release_name}/values.yaml")

        # adiciona o account id no values
        set_yq(f"{self.ns}/{self.release_name}/values.yaml", "AwsAccountId", get_aws_account_id())

        add_and_push(self.release_name, self.ns)
        chdir(old_path)
        alert(f"# Repositorio App Config configurado")

    def add_argocd_config(self):
        # TODO situacao o 0 deploys finais
        alert(f"\n# Iniciando configuracao do ArgoCD Repo")
        old_path = pwd()
        path_to_values = f"{LOCAL_PATH_ARGOCD}/{self.ns}"
        chdir(f"{path_to_values}")
        # verifica se existe ja
        there_is_deploy = get_yq(f"values.yaml", f"'applications.(name=={self.release_name}).name'")

        if there_is_deploy:
            # se sim so reescreve sobre o mapa
            # yq w -i values.yaml 'applications.(name==v1-api-u4c-YYY-master).name' 'v1-api-u4c-XXXYYY-master'
            #cmd = f"yq w -i values.yaml 'applications.(name=={self.release_name}).name' '{self.release_name}'"
            set_yq("values.yaml", f"applications.(name=={self.release_name}).name", f"{self.release_name}")
        else:
            # caso contrario cria um novo
            # yq w -i values.yaml 'applications[+].name' 'v1-api-u4c-rodolfo-master'
            #cmd = f"yq w -i values.yaml 'applications[+].name' '{self.release_name}'"
            set_yq("values.yaml", f"applications[+].name", f"{self.release_name}")

        #cmd = f"yq w -i values.yaml 'applications.(name=={self.release_name}).namespace' '{self.ns}'"
        set_yq("values.yaml", f"applications.(name=={self.release_name}).namespace", f"{self.ns}")
        #cmd = f"yq w -i values.yaml 'applications.(name=={self.release_name}).source.targetRevision' 'HEAD'"
        set_yq("values.yaml", f"applications.(name=={self.release_name}).source.targetRevision", f"HEAD")
        #cmd = f"yq w -i values.yaml 'applications.(name=={self.release_name}).source.path' 'ms-chart'"
        set_yq("values.yaml", f"applications.(name=={self.release_name}).source.path", f"ms-chart")
        #cmd = f"yq w -i values.yaml 'applications.(name=={self.release_name}).source.repoURL' 'git@gitlab.com:u4crypto/devops/aplicacoes/app-configs.git'"
        set_yq("values.yaml", f"applications.(name=={self.release_name}).source.repoURL", f"git@gitlab.com:u4crypto/devops/aplicacoes/app-configs.git")

        add_and_push(self.release_name, self.ns)
        chdir(old_path)
        alert(f"# ArgoCD Repo configurado")

    def deploy_argocd(self):
        self.add_argocd_config()