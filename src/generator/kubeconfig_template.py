"""Generate template file for kubeconfig."""

import yaml


def generate_template(kubeconfig_filepath:str="../kubeconfig.yaml"):
    output_file = "../templates/kubeconfig.yaml"
    # load kubeconfig file
    with open(kubeconfig_filepath, "r") as f:
        kubeconfig = yaml.safe_load(f)
    kubeconfig["contexts"][0]["context"]["user"] = "changeme"
    kubeconfig["users"][0]["name"] = "changeme"
    kubeconfig["users"][0]["user"]["client-certificate-data"] = "changeme"
    kubeconfig["users"][0]["user"]["client-key-data"] = "changeme"
    #pprint(kubeconfig)
    # save template
    with open(output_file, "w") as f:
        yaml.dump(kubeconfig, stream=f, indent=2)
