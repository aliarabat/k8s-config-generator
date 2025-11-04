import os

EQUIPE_COUNT = 15
GROUP_COUNT = 2

for group in range(1, GROUP_COUNT+1):
    for equipe in range(1, EQUIPE_COUNT):
        os.system(f"kubectl delete namespace grp0{group}eq{equipe}-namespace --kubeconfig=kubeconfig.yaml")