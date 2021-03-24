""" Variaveis Globais"""
# Path para clone do helm chart
LOCAL_PATH_CHART = "./curr_chart"
LOCAL_PATH_ARGOCD = "./argocd"
LOCAL_PATH_APPS = "./apps-config"
LOCAL_PATH_MS_CONFIG = "./ms-config"
# Local do ci_default.yaml
LOCAL_CI_VALUES  = "./ci.values"
# Dicionario para armazenar status de deployment
RELEASE_STATUS = {}
#AWS Account
AWS_ACCOUNT_ID = ""
# Repositorio
REPOSITORY = ""
HELM_TIMEOUT = "20s"
DEPLOY_TIMEOUT = 300
PIPE_TIMEOUT = "1000"
DEBUG = 0