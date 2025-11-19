import os
import errno
import base64
import time
import subprocess
from pathlib import Path

from generator.conf import conf_generator
from generator.quota import quota_generator
from generator.role import role_generator
from generator.role_binding import role_binding_generator
from generator.namespace import namespace_generator
from file_handle.file_handle import read_yaml, write_yaml
from cli.cli2 import parse_arguments


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

    # ---------------------------
    # GET CLUSTER CA CERTIFICATE
    # ---------------------------
    def generate_cluster_ca_cert(self):
        print("[INFO] Fetching Kubernetes cluster CA certificate...")
        cmd = (
            "kubectl get cm kube-root-ca.crt -o jsonpath=\"{.data['ca\\.crt']}\" > "
            + self.cluster_ca_cert_file
        )
        os.system(cmd)

    # ---------------------------
    # ENTRYPOINT
    # ---------------------------
    def generate(self):
        self.generate_cluster_ca_cert()

        team_name = f"grp0{self.group}eq{self.team}"
        self.team_name = team_name
        self.out_path = os.path.join(self.out, team_name)
        self.team_namespace = f"{team_name}-namespace"
        self.team_role = f"{team_name}-role"
        self.team_permissions = f"{team_name}-permissions"
        self.team_quota = f"{team_name}-quota"
        self.team_csr = f"{team_name}-csr"

        print(f"[INFO] Team identifier: {self.team_name}")

        self.namespace_file = os.path.join(self.out_path, "namespace.yaml")
        self.role_file = os.path.join(self.out_path, "role.yaml")
        self.role_binding_file = os.path.join(self.out_path, "role_binding.yaml")
        self.quota_file = os.path.join(self.out_path, "quota.yaml")
        self.crt_file = os.path.join(self.out_path, "kubecrt.crt")
        self.key_file = os.path.join(self.out_path, "kubekey.key")
        self.csr_file = os.path.join(self.out_path, "csr.csr")
        self.kubecsr_file = os.path.join(self.out_path, "kubecsr.yaml")
        self.conf_file = os.path.join(self.out_path, "kubecsr.csr.cnf")
        self.kubeconf_file = os.path.join(self.out_path, "kubeconf.yaml")
        self.kubeconf_b64_file = os.path.join(self.out_path, "kubeconf.b64")

        self.setup()
        self.generate_files()

    # ---------------------------
    # CREATE DIRECTORIES
    # ---------------------------
    def setup(self):
        for directory in [self.out, self.out_path]:
            try:
                os.mkdir(directory)
            except OSError as exc:
                if exc.errno != errno.EEXIST:
                    raise
                pass

    # ---------------------------
    # CREATE CSR YAML
    # ---------------------------
    def kubecsr(self):
        data = read_yaml("../templates/kubecsr.yaml")
        data["metadata"]["name"] = self.team_csr
        data["spec"]["request"] = self.team_request
        write_yaml(self.kubecsr_file, data)

    # ---------------------------
    # BUILD FINAL KUBECONFIG
    # ---------------------------
    def kubeconfig(self):
        # Path(__file__).parent.parent / "kubeconfig.yaml"
        template_path = Path(__file__).resolve().parent.parent / "kubeconfig.yaml"

        if not template_path.exists():
            raise FileNotFoundError(f"[ERROR] Missing kubeconfig.yaml template at: {template_path}")

        print("[INFO] Loading kubeconfig template...")
        data = read_yaml(template_path)

        cluster_info = data["clusters"][0]
        cluster_name = cluster_info["name"]
        server_ip = cluster_info["cluster"]["server"]

        print("[INFO] Generating kubeconfig...")

        os.system(
            f"kubectl config set-cluster {cluster_name} "
            f"--server={server_ip} "
            f"--certificate-authority={self.cluster_ca_cert_file} "
            f"--embed-certs=true "
            f"--kubeconfig={self.kubeconf_file}"
        )

        os.system(
            f"kubectl config set-credentials {self.team_name} "
            f"--client-certificate={self.crt_file} "
            f"--client-key={self.key_file} "
            f"--embed-certs=true "
            f"--kubeconfig={self.kubeconf_file}"
        )

        os.system(
            f"kubectl config set-context {self.team_name}-context "
            f"--cluster={cluster_name} "
            f"--namespace={self.team_namespace} "
            f"--user={self.team_name} "
            f"--kubeconfig={self.kubeconf_file}"
        )

        os.system(
            f"kubectl config use-context {self.team_name}-context "
            f"--kubeconfig={self.kubeconf_file}"
        )

    # ---------------------------
    # GENERATE CSR FILE
    # ---------------------------
    def generate_csr(self):
        subj = f"/CN={self.team_name}"
        cmd = [
            "openssl",
            "req",
            "-new",
            "-key", self.key_file,
            "-out", self.csr_file,
            "-subj", subj
        ]

        subprocess.run(cmd, check=True)

    # ---------------------------
    # GENERATE ALL FILES
    # ---------------------------
    def generate_files(self):
        # Namespace
        namespace = namespace_generator(
            self.team_namespace,
            "../templates/namespace.yaml",
            self.namespace_file
        )
        namespace.generate()
        namespace.apply()

        # Quota
        quota = quota_generator(
            self.team_role,
            self.team_namespace,
            "../templates/quota.yaml",
            self.quota_file,
            self.cpu_request,
            self.memory_request,
            self.cpu_limit,
            self.memory_limit
        )
        quota.generate()
        quota.apply()

        conf = conf_generator(self.team_name, self.conf_file)
        conf.generate()

        # Generate private key
        os.system(f"openssl genrsa -out {self.key_file} 2048")

        # Generate CSR
        self.generate_csr()

        csr_text = Path(self.csr_file).read_text()
        csr_b64 = base64.b64encode(csr_text.encode()).decode()
        self.team_request = csr_b64.replace("\n", "")

        self.kubecsr()

        os.system(f"kubectl create -f {self.kubecsr_file}")
        os.system(f"kubectl certificate approve {self.team_csr}")

        # Wait for certificate
        print("[INFO] Waiting for Kubernetes to issue the certificate...")
        cert = ""
        for i in range(30):
            cert = subprocess.getoutput(
                f"kubectl get csr {self.team_csr} -o jsonpath='{{.status.certificate}}'"
            ).strip()

            if cert:
                break

            print(f"[INFO] Certificate not ready yet, retrying ({i+1}/30)...")
            time.sleep(1)

        if not cert:
            raise Exception("[ERROR] Kubernetes did not issue certificate. Aborting.")

        with open(self.crt_file, "wb") as f:
            f.write(base64.b64decode(cert))

        # Build kubeconfig
        self.kubeconfig()

        # Base64 encode kubeconfig
        os.system(f"base64 -i {self.kubeconf_file} > {self.kubeconf_b64_file}")
        print(f"[SUCCESS] kubeconfig base64 saved to: {self.kubeconf_b64_file}")

        # Role and role binding
        role = role_generator(
            self.team_role,
            self.team_namespace,
            "../templates/role.yaml",
            self.role_file,
            self.role_resources,
            self.verbs
        )
        role.generate()
        role.apply()

        role_binding = role_binding_generator(
            self.team_permissions,
            self.team_namespace,
            self.team_name,
            self.team_role,
            "../templates/role_binding.yaml",
            self.role_binding_file
        )
        role_binding.generate()
        role_binding.apply()


if __name__ == "__main__":
    k8s = k8s_config()
    k8s.generate()
