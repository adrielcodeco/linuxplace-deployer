
""" Variaveis Globais"""
# Path para clone do helm chart
LOCAL_PATH_CHART = "./curr_chart"
LOCAL_PATH_ARGOCD = "./tmp/argocd"
LOCAL_PATH_APPS = "./tmp/apps-config"
LOCAL_PATH_MS_CONFIG = "./tmp/ms-config"
# Local do ci_default.yaml
LOCAL_CI_VALUES  = "./ci.values"
# Dicionario para armazenar status de deployment
RELEASE_STATUS = {}
#AWS Account
AWS_ACCOUNT_ID = ""
# Repositorio
REPOSITORY = ""
# TAG
TAG = ""
HELM_TIMEOUT = "20s"
PIPE_TIMEOUT = "1000"
CI_PROJECT_PATH = ""