import os
import errno
import base64
from pathlib import Path
from generator.conf import conf_generator
from generator.quota import quota_generator
from generator.role import role_generator
from generator.role_binding import role_binding_generator
from generator.kubeconfig_template import generate_template
from file_handle.file_handle import read_yaml, write_yaml
from generator.namespace import namespace_generator
from cli.cli2 import parse_arguments
import subprocess
import platform

class k8s_config:
    def __init__(self):
        args = parse_arguments()
        self.out = args.out_directory
        self.group = args.group
        self.team = args.team
        self.kubeconfig_path = args.kubeconfig_path
        self.cpu_limit = args.cpu_limit
        self.memory_limit = args.memory_limit
        self.cpu_request = args.cpu_request
        self.memory_request = args.memory_request
        self.role_resources = args.role_resources
        self.verbs = args.verbs

        self.cluster_ca_cert_file = str(Path(__file__).parent / "ca.crt")
        self.POSTGRES_PRIVATE_IP = "172.16.0.5"

    def generate_cluster_ca_cert(self):
        os.system(
            "kubectl get cm kube-root-ca.crt -o jsonpath=\"{.data['ca\\.crt']}\" >" + self.cluster_ca_cert_file)

    def generate(self):
        # generate_template(self.kubeconfig_path)

        self.generate_cluster_ca_cert()

        team_name = f"grp0{self.group}eq{self.team}"
        self.team_name = team_name
        self.out_path = os.path.join(self.out, team_name)
        self.team_namespace = f"{team_name}-namespace"
        self.team_role = f"{team_name}-role"
        self.team_permissions = f"{team_name}-permissions"
        self.team_quota = f"{team_name}-quota"
        self.team_csr = f"{team_name}-csr"
        self.team_request = ""
        self.team_cert = ""
        self.team_key = ""

        self.namespace_file = os.path.join(
            self.out_path, "namespace.yaml")
        self.role_file = os.path.join(self.out_path, "role.yaml")
        self.role_binding_file = os.path.join(
            self.out_path, "role_binding.yaml")
        self.quota_file = os.path.join(self.out_path, "quota.yaml")
        self.crt_file = os.path.join(self.out_path, "kubecrt.crt")
        self.key_file = os.path.join(self.out_path, "kubekey.key")
        self.csr_file = os.path.join(self.out_path, "csr.csr")
        self.kubecsr_file = os.path.join(self.out_path, "kubecsr.yaml")
        self.conf_file = os.path.join(self.out_path, "kubecsr.csr.cnf")
        self.kubeconf_file = os.path.join(
            self.out_path, "kubeconf.yaml")
        self.kubeconf_b64_file = os.path.join(
            self.out_path, "kubeconf.b64")
        print(self.team_name)

        self.setup()
        self.generate_files()

    def setup(self):
        try:
            os.mkdir(self.out)
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise
            pass

        try:
            os.mkdir(os.path.join(self.out, self.team_name))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise
            pass

    def kubecsr(self):
        data = read_yaml("../templates/kubecsr.yaml")
        data["metadata"]["name"] = self.team_csr
        data["spec"]["request"] = self.team_request
        write_yaml(self.kubecsr_file, data)

    def kubeconfig(self):
        data = read_yaml(Path(__file__).parent.parent / "kubeconfig.yaml")
        cluster_info = data['clusters'][0]
        cluster_name, server_ip = cluster_info['name'], cluster_info['cluster']['server']
        # data["contexts"][0]["context"]["user"] = self.team_name
        # data["contexts"][0]["context"].update({"namespace": self.team_namespace})
        # data["users"][0]["name"] = self.team_name
        # data["users"][0]["user"]["client-certificate-data"] = self.team_cert
        # data["users"][0]["user"]["client-key-data"] = self.team_key
        os.system(
            f"kubectl config set-cluster {cluster_name} --server={server_ip} --certificate-authority={self.cluster_ca_cert_file} --embed-certs=true --kubeconfig={self.kubeconf_file}"
        )

        os.system(
            f"kubectl config set-credentials {self.team_name} --client-certificate={self.crt_file} --client-key={self.key_file} --embed-certs=true --kubeconfig={self.kubeconf_file}"
        )

        os.system(
            f"kubectl config set-context {self.team_name}-context --cluster={cluster_name} --namespace={self.team_namespace} --user={self.team_name} --kubeconfig={self.kubeconf_file}"
        )

        os.system(
            f"kubectl config use-context {self.team_name}-context --kubeconfig={self.kubeconf_file}"
        )
        # write_yaml(self.kubeconf_file, data)
        
    def generate_csr(self):
        subj = f"/CN={self.team_name}"

        # On Windows, openssl still accepts the string — no quoting issues with list mode
        cmd = [
            "openssl",
            "req",
            "-new",
            "-key", self.key_file,
            "-out", self.csr_file,
            "-subj", subj,
        ]

        # Run the command
        subprocess.run(cmd, check=True)

    def generate_files(self):
        namespace = namespace_generator(
            self.team_namespace, "../templates/namespace.yaml", self.namespace_file
        )
        namespace.generate()
        namespace.apply()

        quota = quota_generator(
            self.team_role,
            self.team_namespace,
            "../templates/quota.yaml",
            self.quota_file,
            self.cpu_request,
            self.memory_request,
            self.cpu_limit,
            self.memory_limit,
        )
        quota.generate()
        quota.apply()

        conf = conf_generator(self.team_name, self.conf_file)
        conf.generate()

        os.system(f"openssl genrsa -out {self.key_file} 2048")
        
        self.generate_csr()

        crs_file_content = open(self.csr_file, "r").read()
        crs_file_content_base64 = base64.b64encode(
            crs_file_content.encode("ascii")).decode('ascii')
        self.team_request = crs_file_content_base64.replace('\n', '')

        self.kubecsr()

        os.system(f"kubectl create -f {self.kubecsr_file}")
        os.system(f"kubectl certificate approve {self.team_csr}")

        os.system(
            f"kubectl get csr {self.team_csr} -o jsonpath='{{.status.certificate}}' | base64 --decode > {self.crt_file}"
        )


        self.kubeconfig()

        # os.system(
        #     f"kubectl create secret generic my-postgres-ip-secret --from-literal=db_host={self.POSTGRES_PRIVATE_IP} -n {self.team_namespace}"
        # )

        os.system(
            f"base64 -i {self.kubeconf_file} > {self.kubeconf_b64_file}"
        )
        print(f"{self.kubeconf_b64_file} generated succesfully...")

        role = role_generator(
            self.team_role,
            self.team_namespace,
            "../templates/role.yaml",
            self.role_file,
            self.role_resources,
            self.verbs,
        )
        role.generate()
        role.apply()

        role_binding = role_binding_generator(
            self.team_permissions,
            self.team_namespace,
            self.team_name,
            self.team_role,
            "../templates/role_binding.yaml",
            self.role_binding_file,
        )
        role_binding.generate()
        role_binding.apply()


if __name__ == "__main__":
    k8s = k8s_config()
    k8s.generate()
