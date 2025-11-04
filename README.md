# k8s-config-generator

## Overview

`k8s-config-generator` is a Python script that generates Kubernetes configuration files for a specified number of teams. The generated files include namespaces, roles, role bindings, quotas, and client certificates. The script takes command-line arguments to configure the generated files.

## Requirements

- A k8s cluster installed. See [microk8s](https://microk8s.io/) installation.
- Enable Role Based Access Control (RBAC) on the cluster using the following command:

 ```bash
 sudo microk8s.enable rbac
 ```

- Get cluster `kubeconfig.yaml` configuration file using the following command:

 ```bash
 microk8s config view
 ```

 NOTE: Copy and paste the content of the output into a `kubeconfig.yaml` file.

## Getting started

1. Clone this repository to your local machine:

    ```bash
    git clone https://github.com/<username>/k8s-config-generator.git
    ```

2. Create and activate a virtual environment

    ```bash
    python -m venv .env && source .env/bin/activate
    ```

3. Install the required packages:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

To use `k8s-config-generator`, run the following command:

``` bash
cd src && KUBECONFIG=/path/to/kubeconfig.yaml python main2.py
```

The command-line arguments are as follows:

- `--out_directory`: The directory where the generated files will be saved.
<!-- - `--namespace_count`: The number of namespaces to generate for each group. -->
<!-- - `--group_count`: The number of groups to generate. -->
- `--group`: The group number.
- `--team`: The team number.
- `--kubeconfig_path`: The path to the kubeconfig file.
- `--cpu_limit`: The CPU limit for the quota.
- `--memory_limit`: The memory limit for the quota.
- `--cpu_request`: The CPU request for the quota.
- `--memory_request`: The memory request for the quota.
- `--role_resources`: The resources that the role will have access to.
- `--verbs`: The verbs that the role will have access to.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
