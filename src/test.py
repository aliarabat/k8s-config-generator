import os

os.system("kubectl get cm kube-root-ca.crt -o jsonpath=\"{.data['ca\\.crt']}\" > ca.crt")